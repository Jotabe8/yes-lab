# Compras de duración de fin de mes en bonos: verificación, P4 en Darwinex Zero y réplica en el Bund (19-11-2026)

## Resumen

**Descartada por el preregistro de P4** (`PREREGISTRO_P4_Y_BUND.md`, commit `632fe32`, subido antes de calcular).
El efecto en EE. UU. es real y las cifras del informe semanal se reproducen, pero:

1. **En el futuro ZN, que es lo que se opera, el efecto es ~30 % menor** que en el 10 años de FRED (la duración del
   ZN es más corta) y en 2019-2026 el neto es +10,5 pb/op con **t 1,93** (2023-26 solo +3,8 pb).
2. **En el DARWIN sube el Sharpe (1,72 → 1,90) pero empeora el peor DD (20,6 → 22,1 R)**, que el preregistro exigía
   no empeorar (es la misma regla con la que se descartó la pata diversificadora). Con la ventaja a la mitad el
   Sharpe queda en 1,74, casi igual que sin la pata.
3. **No se replica en el Bund**: neto t 1,76 en 1998-2026 y negativo en 2019-2026. El mecanismo de fin de mes no
   viaja bien a Europa, igual que la reversión DZ.

## 1. Verificación de las cifras del informe (`auditoria.py`)

- El preregistro existe en `main` (commit `d1e0a70`, 16-11 07:49) y es anterior al script (`92e330a`, 07:51). Él
  mismo avisa de que 2016-26 ya se había mirado con ETF.
- Todas las cifras del informe salen igual (`bonos_fin_de_mes_salida.txt`). Con otro método de precio (bono a la par
  exacto en vez de duración fija 8,5): 1990-2026 neto +21,1 pb t 5,77; 2019-26 +19,3 pb t 2,60.
- **Placebo completo** (las 3 sesiones que terminan en cada posición del mes, no solo en la 12.ª): la ventana de fin de
  mes da +24,1 pb; las demás posiciones, media +2,9 pb y máximo +8,6. Fin de mes menos el resto del mismo mes:
  +21,2 pb t 5,45 (2019-26 t 3,01). No es deriva de los bonos.
- **Futuro ZN real**: el filtro original (|r| < 2 %) se sustituyó por saltos de vencimiento detectados contra FRED
  (55 días, solo 1 dentro de la ventana). Resultado casi igual: 2001-26 neto +14,5 pb t 4,18; **2019-26 +10,5 pb
  t 1,93**; 1.ª mitad +17,8, 2.ª +11,2. Correlación mes a mes con FRED 0,96, pero el ZN rinde el 70 %.

## 2. Costes en Darwinex Zero

ZN: 1 tick = 15,625 $ (1,5 pb sobre ~105.000 $) + 3 $ por orden → ~2,1 pb ida y vuelta. Los 3 pb del preregistro
son prudentes; con costes ×2 el ZN sigue en +11,5 pb. Para llevar la pata al peso probado harían falta **~33 contratos
(3,5 × el capital de 1 M$ en nominal)**; cabe por margen, pero es mucho apalancamiento para una pata de 12 ops/año.

## 3. P4 en el DARWIN (`p4_darwin.py`, 2018-01 → 2026-10)

Pata ZN sola en la ventana: SR 0,74, t 2,19. Correlación mensual: ORB +0,10, reversión −0,16, base −0,05.

| | Sharpe | Peor DD | Peor mes |
|---|---|---|---|
| Base ORB + reversión | 1,72 | 20,6 R | −19,6 R |
| **Base + ZN (peso 0,5)** | **1,90** | **22,1 R** ✗ | −13,5 R |
| Base + ZN con ventaja a la mitad | 1,74 | 23,4 R | −14,0 R |
| Placebo: ventana de la sesión 12 | 1,24 | 43,3 R | −18,0 R |
| (informativo) peso 0,25 | 1,87 | 21,3 R | −15,9 R |

Bootstrap por bloques de 3 meses: P(ΔSharpe > 0) 90 %, p10 +0,00. Monte Carlo (cuenta de futuros): +1.433 €/año
frente a +1.085 de la base (+4.825 frente a +3.992 con permanente); con la ventaja a la mitad +1.204.

| # | Criterio | Resultado | |
|---|---|---|---|
| 1 | \|corr\| con ORB y reversión ≤ 0,20 | 0,10 / 0,16 | ✓ |
| 2 | ΔSharpe ≥ +0,10 y peor DD no peor | +0,19; **DD 20,6 → 22,1 R** | **✗** |
| 3 | Ventaja a la mitad > base | 1,74 > 1,72 | ✓ (por la mínima) |
| 4 | Placebo sesión 12 no iguala | 1,24 | ✓ |
| 5 | Bootstrap P(Δ > 0) ≥ 80 % | 90 % | ✓ |
| 6 | Monte Carlo > base | +1.433 > +1.085 | ✓ |

## 4. Réplica en el Bund (`bund.py`, Bundesbank 10 años 1997-2026)

| Tramo | Neto pb | t |
|---|---|---|
| 1998-2026 | +5,9 | 1,76 ✗ (pedía ≥ 2,0) |
| 2019-2026 | −1,0 | −0,15 ✗ |
| Placebo sesión 12 | −1,3 | −0,36 |

El fin de mes queda en el percentil 95 del placebo completo, pero la posición 18 del mes da más (+12,0 frente a +8,9).
Correlación mensual con el ZN +0,47; ZN + Bund a igual riesgo t 3,59 < ZN solo 4,18. El CFD del Bund de Dukascopy
(2016-26) se bajó, pero sus velas diarias casan mal con el Bundesbank (correlación 0,37) y no se usa.

## Veredicto

Falla P4 por el criterio 2 y la réplica no pasa. **Descartada**: no queda en reserva. El DARWIN sigue con ORB US100
+ reversión. Lección: el efecto en el bono a plazo constante de FRED sobrestima en ~30 % lo que se cobra en el ZN, y
en 2019-26 el ZN ya no llega a t 2. Cualquier idea de bonos en DZ se prueba directamente en el futuro.
