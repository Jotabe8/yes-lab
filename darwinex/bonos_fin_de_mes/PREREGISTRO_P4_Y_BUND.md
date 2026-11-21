# Preregistro: P4 de las compras de fin de mes en ZN y réplica en el Bund (19-11-2026)

Escrito y subido ANTES de calcular la correlación con el ORB y la reversión, el DARWIN y de bajar datos del Bund.
Ya mirado (no cuenta como prueba): la auditoría `auditoria.py` de la regla en EE. UU. (FRED y ZN de Yahoo).

## Regla (la del `PREREGISTRO_BONOS_FIN_DE_MES.md`, sin cambios)
Largo del cierre de la sesión N−3 al cierre de la última sesión del mes (3 sesiones de retorno). Coste 3 pb.
En ZN se usa el futuro real de Yahoo con los saltos de vencimiento sustituidos por el retorno de FRED (`auditoria.py`).

## A. P4 en el DARWIN de Darwinex Zero (ventana común 2018-01 → 2026-10)
Base = mezcla ORB US100 + reversión de índices US de `reversion_dz/mensual_orb_reversion.csv` (columna `mezcla`).
Pata ZN mensual (meses sin operación = 0) escalada a vol mensual = 0,5 × la de la base; la suma se reescala a la vol
de la base (Darwinex reescala a VaR objetivo). Pasa P4 si se cumplen todos:
1. Correlación mensual de la pata con el ORB y con la reversión ≤ 0,20 en valor absoluto.
2. ΔSharpe mensual anualizado del DARWIN ≥ +0,10 sobre la base, y peor DD no peor que el de la base.
3. Con la ventaja de la pata a la mitad (se resta la mitad de su media en los meses con operación), Sharpe > base.
4. Placebo: la misma pata con la ventana de 3 sesiones terminando en la sesión 12 no da un ΔSharpe igual o mayor.
5. Bootstrap por bloques de 3 meses: P(ΔSharpe > 0) ≥ 80 %.
6. Monte Carlo de `dz_sim_base.py` (cuenta de futuros, 50 €/mes): neto €/año mayor que la base en la misma cuenta.

## B. Réplica en el Bund (contraste del mecanismo)
- Datos: rendimiento diario del Bund a 10 años del Bundesbank (curva estimada, desde 1997); precio con bono a la par
  exacto (como `auditoria.py`). Fin de mes = última sesión del mes en la serie. Si no llega el Bundesbank, la curva
  AAA del BCE (desde 2004). El futuro FGBL, si llega, es solo informativo.
- Coste 3 pb (1 tick de FGBL = 10 € sobre ~130.000 € ≈ 0,8 pb, más 3 € por orden; redondeado al alza como en ZN).
- **La réplica pasa si:** neto 1998-2026 t ≥ 2,0 (réplica de un mecanismo ya preregistrado, una sola prueba);
  2.ª mitad > 0; la ventana de fin de mes supera a todas las demás posiciones del mes (placebo completo, percentil
  ≥ 95); y 2019-2026 neto > 0.
- **Valor propio en la cuenta (decide si el Bund entra como 2.º instrumento, aparte de si replica):** correlación
  mensual con la ventana del ZN ≤ 0,6 y la combinación ZN + Bund a igual riesgo con t mayor que el ZN solo.
- Informativo: Gilt no se prueba (Darwinex Zero no tiene futuro del Gilt).

## Qué hago con el resultado
- A pasa → candidata a P5 (EA en la cuenta de futuros de DZ). A falla → la pata se descarta, no queda en reserva.
- B solo sirve de contraste y, si pasa también el valor propio, de segundo instrumento en la misma pata.
