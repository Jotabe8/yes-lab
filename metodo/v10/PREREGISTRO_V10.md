# Preregistro v10: datos nuevos de la apertura y el cierre de Nueva York (Databento)

Escrito el 15-11-2026 antes de bajar ningún dato (commit anterior al primer run de `v10-databento.yml`).

## Por qué estas y no otras
La v9 cerró la búsqueda con precio, calendario y macro: solo el ORB US100 tiene ventaja neta y su ventaja es
propia de la **apertura de contado de Nueva York**. Lo único que no se ha mirado nunca es lo que pasa **dentro**
de esa apertura con datos que el CFD no enseña:

1. **El desequilibrio de la subasta de apertura de Nasdaq (NOII)**: órdenes de compra y venta sin casar que la
   bolsa publica de 9:25 a 9:30 ET. Es el flujo obligado de la apertura (órdenes "on open" de fondos).
2. **El volumen con signo del futuro NQ** (quién agrede, comprador o vendedor) durante el rango de 9:30 a 9:40.
3. **El desequilibrio de la subasta de cierre (MOC)** que Nasdaq publica desde las 15:50 ET.

Fuente: Databento, pago por uso, 125 $ de crédito gratis al darse de alta (caduca a los 6 meses).
XNAS.ITCH esquema `imbalance` (desde 2018-05), GLBX.MDP3 esquemas `trades` y `ohlcv-1m` (NQ continuo por
volumen `NQ.v.0`). Valores: QQQ y las 8 mayores del Nasdaq-100 que cotizan en Nasdaq (AAPL, MSFT, NVDA, AMZN,
META, AVGO, GOOGL, TSLA). Periodo 2018-05-01 → 2026-11-13.

Aviso previo (T0) sobre H3: el estudio de la propia Nasdaq (2019) dice que el 80 % del movimiento hacia el cierre
tras publicarse el desequilibrio se descuenta en 300 ms y que el efecto medio por acción es 5,5 pb. Con la
latencia de MT5 (segundos) la H3 parte casi descartada; se prueba solo porque sus datos vienen en la misma
descarga sin coste extra.

## Definiciones (fijadas ahora)
- Día válido: hay mensaje de imbalance de apertura de QQQ entre 9:29:00 y 9:29:59 ET y velas NQ de 9:30 a 16:00.
- **D_ape** (desequilibrio de apertura agregado) = Σ_s lado_s × total_imbalance_qty_s × ref_price_s /
  Σ_s paired_qty_s × ref_price_s, con el último mensaje de cada valor antes de 9:30:00 (lado B = +1, A = −1).
  Señal = signo(D_ape). Versión QQQ sola solo como réplica.
- **Dirección ORB** = signo de cierre − apertura de NQ en la vela 9:30-9:40 ET (la misma regla que la vela del
  rango de v018). R del ORB = serie `serie_v018_be.csv` (v018 sobre CFD FTMO/Dukascopy, columna Rbe), unida por fecha.
- **Delta** = (volumen agresor comprador − volumen agresor vendedor) / volumen total en NQ entre 9:30:00 y
  9:39:59 ET (Databento `side` B = comprador, A = vendedor).
- **D_cie** = como D_ape pero con el primer mensaje de cierre a partir de 15:50:00 ET.
- Coste NQ/MNQ: 0,5 puntos ida y vuelta (comisión MNQ + medio tick de deslizamiento por lado), en pb del precio.

## Hipótesis y reglas (5 pruebas en total; no hay más variantes)
- **H1a, filtro de apertura**: el ORB gana más cuando signo(D_ape) = dirección ORB que cuando no.
  Medida: diferencia de R medio (acuerdo − desacuerdo) en las operaciones de v018.
- **H1b, sistema propio**: entrar en NQ a la apertura de la vela 9:31 en el signo de D_ape, salir al cierre de la
  vela 9:59. Neto en pb.
- **H2a, filtro de flujo**: el ORB gana más cuando signo(Delta) = dirección ORB (sin absorción) que cuando no.
- **H2b, intensidad**: dentro de los días de acuerdo, el tercio con |Delta| mayor gana más que el tercio menor.
- **H3, cierre**: entrar en NQ a la apertura de la vela 15:51 en el signo de D_cie, salir al cierre de la
  vela 15:59. Neto en pb.

## Listón
Filtros (H1a, H2a, H2b):
1. Diferencia ≥ +0,15 R con t de Welch ≥ 2,4.
2. Mismo signo y ≥ +0,05 R en 2018-05→2022 y 2023→2026.
3. El grupo que el filtro quita tiene R medio ≤ +0,02 (si no, quitarlo baja el R total y no sirve en prop).
4. Placebo: barajar la señal entre días 2.000 veces; la diferencia real supera el p95.
5. Réplica: con QQQ sola (H1a) o con el delta de 9:30-9:35 (H2a) la diferencia tiene el mismo signo y t ≥ 1,5.

Sistemas (H1b, H3):
1. t neto ≥ 2,4 con al menos 150 operaciones.
2. Neto > 0 en las dos mitades y con coste ×2.
3. Placebo de lado (signo contrario) pierde; placebo de señal barajada 2.000 veces: real > p95.
4. Réplica con QQQ sola: neto > 0.
5. Correlación diaria con el ORB < 0,3.

Si falla cualquier punto: descartada, sin rescate por subconjuntos (horas, años, valores, umbrales).
Si pasa: P2 (paseo aleatorio con el mismo código), luego port a MQL5. Aviso operativo: H1a/H2a solo se pueden
operar si el dato llega en vivo al EA (Databento en vivo cuesta 199 $/mes; MNQ en NinjaTrader con Lucid lo
haría posible para H2a porque el delta sale del propio feed de futuros sin coste).

## Tope de gasto
El workflow pide primero el coste a la API (`metadata.get_cost`, gratis) y no baja nada si el total supera 100 $.

## Anexo v10-bis (15-11-2026, antes de bajar datos): sin Databento
Jorge no abre cuenta en Databento. El desequilibrio de subasta (H1, H3) no tiene fuente alternativa: **cerradas
sin probar**. NinjaTrader solo da 1 año de ticks: con la dispersión de v018 (σ 2,19 R, 208 ops/año) la diferencia
mínima detectable a t 2,4 sería 0,73 R. Sin potencia: descartado como fuente.
H2 se prueba con **QQQ en lugar de NQ** (Alpaca, cuenta de papel gratis, SIP 2016-26): Delta = volumen con signo por la
regla del tick (sin la subasta de apertura ni lotes impares) entre 9:30:00 y 9:39:59 ET; dirección = signo del
último menos el primer precio de esa ventana. Mitades 2018-21 y 2022-26. Mismo listón de filtro (puntos 1-5) con la
réplica en 9:30-9:35. `descargar_alpaca.py`, `analizar_alpaca.py`, workflow `v10-alpaca.yml`
(secretos `ALPACA_KEY_ID` y `ALPACA_SECRET`).
