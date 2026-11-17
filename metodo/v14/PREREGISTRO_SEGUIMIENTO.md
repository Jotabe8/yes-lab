# Preregistro v14c · Seguimiento en real del ORB US100 por régimen de Hurst (16-11-2026)

Única pista de v14: en el US100 el ORB gana más en días persistentes (+0,23 R) que antipersistentes (+0,09 R),
pero no superó el placebo p99. Se comprueba **fuera de muestra con las operaciones reales**, sin tocar el EA.

- Operaciones: las de US100.cash del EA ORB (v018/v019/v020) en /mnt/project-files/operaciones-live/ops_live.csv,
  **solo desde el 17-11-2026** (las anteriores no cuentan para la decisión). R = columna R del CSV.
- Régimen de cada día: el de v14 (Dukascopy US100 9:30-15:55 NY, H5 y Hhoy, H ≥ mediana de 250 días previos),
  calculado con metodo/v14/fractales.py. El workflow v14-seguimiento.yml lo refresca cada sábado (activo una vez
  fusionado en main; también se lanza a mano).
- Medida que decide: **H5** (la principal de v14). Hhoy solo informativa.
- Decisión con **100 operaciones** (≈ 5-6 meses): diferencia media R (persistente − antipersistente) > 0 con
  t de una cola ≥ 1,65. Si se cumple, se preregistra una versión nueva del EA con tamaño 1,5/0,5 según régimen
  (solo para cuentas nuevas, con su propio P5). Si no, se cierra la vía Hurst del todo.
- A las 50 operaciones se mira solo como información (no se decide nada).
Uso: python metodo/v14/seguimiento.py /mnt/project-files/operaciones-live/ops_live.csv
