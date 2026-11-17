# P5 ReversionDZ_v001: cómo probarlo en el Strategy Tester (17-11-2026)

**Nunca en el terminal de la cuenta real.** Usa una instalación de prueba (por ejemplo MT5_FTMO_10K_C con cuenta demo).

1. Copia `ReversionDZ_v001.mq5` a `MQL5\Experts\` de esa instalación y compila (F7): 0 errores. (Ya viene compilado
   en esta carpeta si el .ex5 está al lado.)
2. Borra `ReversionDZ_v001_*_ops.csv` de `%APPDATA%\MetaQuotes\Terminal\Common\Files\` si existe.
3. Strategy Tester, una pasada por símbolo: **US500.cash**, **US100.cash**, **US30.cash** (y US2000.cash si existe).
   - Marco: M1. Modelado: **"Cada tick basado en ticks reales"**. Fechas: 2022.01.01 → hoy.
   - Depósito 100.000 USD. Parámetros por defecto (riesgo 0,30 % por ATR, servidor − NY = 7).
4. Pásame la ruta del CSV (o déjalo en Common\Files) y yo hago la comparación operación a operación con
   `ops_ref_<símbolo>_cmp.csv` de esta carpeta: `python -m metodo.comparar_ops ops_ref_US500_cmp.csv ReversionDZ_v001_US500.cash_ops.csv`.
   Criterio: ≥ 90 % de ops emparejadas, R media a ±20 %, corr R ≥ 0,9, ≥ 90 % de pares con |ΔR| ≤ 0,1.

Referencia con M1 a las 15:58 NY (misma lógica que el EA), 2018-26:
US500 n=246 bruto +0,287 R t 3,6 · US30 n=236 +0,238 t 3,0 · US100 (FTMO 2021-26) n=149 +0,249 t 2,5 · US2000 n=213 +0,112 t 1,3.

En Darwinex Zero: comprobar que el servidor está a NY+7 todo el año (si no, `InpServidorMenosNY`), un gráfico por
símbolo con magic distinto, y empezar en demo (P6).
