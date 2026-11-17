# Preregistro: compras de duración de fin de mes en bonos del Tesoro (16-11-2026)

Escrito y subido ANTES de ejecutar la prueba sobre `datos_bonos/`. Aviso honesto: la rutina semanal ya miró
2016-2026 con ETF (IEF, TLT) y vio el efecto, sobre todo en febrero, mayo, agosto y noviembre (ramas cerradas
`estrategias-2026-11-02` y `estrategias-2026-11-09`). Ese tramo no cuenta como fuera de muestra.

Instrumento: futuro ZN (10 años) en Darwinex Zero; FTMO no tiene bonos. Precio aproximado con los rendimientos de
FRED a plazo constante, igual que `bonos_dz.py`: retorno diario ≈ −D·Δy + y/252 con D = 8,5 (10 a), 4,6 (5 a), 17 (30 a).

## Mecanismo (Hartley y Schwarz, 2019; muestra 1990-2018)
El último día hábil del mes los índices de bonos del Tesoro incorporan las emisiones del mes y su duración sube.
Los fondos indexados compran duración para no desviarse; los activos se adelantan. Quien vende esos bonos en las
últimas sesiones cobra la prima. La extensión es casi el doble en los meses de refinanciación trimestral
(febrero, mayo, agosto y noviembre), según notas de mercado (ITC Markets).

## Regla (fija, sin optimizar)
- Largo del 10 años del cierre de la sesión N−4 al cierre de la última sesión del mes (N): 3 sesiones de retorno.
- Una operación por mes. Coste 3 pb por operación (1 tick de ZN por lado + comisión, redondeado al alza); ×2 = 6 pb.

## Prueba principal y criterio
- Periodo principal: 1990-01 → 2026-10, todos los meses.
- **Pasa si:** t neto ≥ 2,4; segunda mitad > 0; costes ×2 > 0; 2019-01 → 2026-10 (fuera de la muestra publicada)
  neto > 0; y el placebo (la misma ventana de 3 sesiones terminando en la sesión 12 del mes) da un resultado menor.
- **Hipótesis secundaria (decide la variante, no la principal):** solo meses de refinanciación. Pasa si su neto es
  mayor que el del resto de meses en 1990-2015 (tramo no mirado con ETF) y su t neto ≥ 2,4 en 1990-2026.

## Informativo (no decide)
- 1962-1989 como réplica anterior a la muestra publicada.
- 5 y 30 años con la misma regla.
- Resultado por año y por mes del calendario.

## Triaje T0
Con ~430 meses y el Sharpe publicado (~1 bruto, anual) la potencia es buena para la principal. La secundaria tiene
~145 operaciones y potencia baja: un "no pasa" con el signo correcto será clase C.
