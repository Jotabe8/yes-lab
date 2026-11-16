# Preregistro v14d · Régimen de Hurst sobre los descartados más prometedores (16-11-2026, antes de calcular)

Pedido de Jorge: aplicar lo mismo a otras estrategias prometedoras. "Prometedor" = descartado **con ventaja bruta
real** que murió por coste o por poca potencia (no los de clase A, donde un filtro no puede crear nada):
1. **ORB sin condición en GER40, UK100, JP225, oro** (v13 incondicional: GER40 t 1,58-2,24, JP225 bruto real pero
   coste). Datos y H ya calculados en v14.
2. **Gotobi del yen** (comprar 08:00 JST, cerrar 09:55, stop 0,25 × rango diario medio de 14 días, días 5/10/15/20/25
   y último de mes; si cae en fin de semana, el hábil anterior, como en la prueba original): bruto +0,106 R t 3,5 en USDJPY, pero coste 1,6 pips ≈ bruto/1,5.
Fuera: ORB cripto (comisión, no bruto), deriva pre-FOMC (≈ 8 ops/año), GEX (sin potencia), clase A.

**Hipótesis:** el filtro de régimen persistente sube la media por operación lo bastante para que pase el listón
completo por sí mismo. Aviso: en v14 un filtro así no batió al azar en el US100 ni en el ORB en juego, y el
conmutador mostró que la pata "persistente" del ORB sin condición da +0,070 R t 2,27 (H5) y +0,033 (Hhoy) en
cartera: el resultado de la prueba 1 está **parcialmente visto**. Se ejecuta igual por mercado con el listón
completo, y se dice.

## Medidas (código de metodo/v14/fractales.py)
- ORB: H5 y Hhoy de v14 (régimen H ≥ mediana de 250 días previos).
- Gotobi (hora de Tokio): **H5** = DFA de los rendimientos M1 de 00:00-09:55 JST de los 5 días hábiles anteriores
  (escalas 4-64); **Hhoy** = DFA de los 390 rendimientos M1 anteriores a las 08:00 JST (escalas 4-32).
  Mismo régimen (mediana de 250 días hábiles previos).
- Gotobi datos: M1 bid/ask Dukascopy 2012-01 → 2026-11, USDJPY, EURJPY, GBPJPY (workflow v14-gotobi.yml). Entrada
  al ask de 08:00, salida al bid de 09:54 (cierre); stop vela a vela sobre el bid, huecos a la apertura.
  Coste añadido por comisión 0,5 pips (la horquilla ya va en bid/ask); prueba ×2 = +1,6 pips más.

## Pruebas: 2 sistemas × 2 medidas = 4 → placebo al p99. Una prueba pasa si cumple TODO
1. t neto por operación del sistema filtrado ≥ 2,4 (2012-26).
2. Media neta filtrada > p99 de 2.000 subconjuntos al azar del mismo tamaño (por mercado) del sistema base.
3. Mejora sobre la base en las dos mitades (corte 2019-07-01).
4. Costes ×2 neto > 0.
5. Sharpe anual diario filtrado > base.
6. ORB: ≥ 3 de 4 mercados con neto filtrado > 0. Gotobi: decide USDJPY (coste medido); EURJPY y GBPJPY deben dar
   mejora > 0 en bruto (réplica), su coste no está medido.
7. Corr diaria con v018 < 0,3.
Si no pasa: DESCARTADO sin rescates. Si pasa: P4-P6 y decide Jorge.
