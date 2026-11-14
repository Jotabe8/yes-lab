# Preregistro: dos ideas con bonos que solo Darwinex permite (13-11-2026)

Escrito y subido ANTES de descargar los datos. FTMO no tiene bonos; Darwinex Zero sí (futuros CME ZT/ZF/ZN/ZB
vía la cuenta de futuros). Precio de los bonos aproximado con los rendimientos de FRED a plazo constante:
retorno diario ≈ −D·Δy + y/252 con D = 1,9 (2 a), 4,6 (5 a), 6,3 (7 a), 8,5 (10 a), 17 (30 a).
Así se evitan los saltos de vencimiento de los futuros continuos de Yahoo.

## Idea 1. Ciclo de subastas del Tesoro (Lou, Yan y Zhang, RFS 2013)
Mecanismo: los intermediarios absorben la oferta nueva; el precio cae antes de la subasta y se recupera después.
Muestra del artículo: 1980-2008. **Prueba aquí: 2009-01 → 2026-10, todo fuera de la muestra publicada.**
- Fechas: subastas de notas y bonos (2, 5, 7, 10 y 30 años, incluidas reaperturas) de TreasuryDirect/fiscaldata.
- Por cada subasta en el día T: corto del plazo subastado del cierre de T−6 al cierre de T−1, y largo del cierre
  de T−1 al cierre de T+4 (días hábiles). Resultado del ciclo = retorno largo − retorno corto, en pb.
- Principal: media semanal a igual riesgo de los plazos subastados esa semana (una observación por semana con subasta).
- Coste: 3 pb por ciclo (≈ 2 idas y vueltas de 1 tick en ZF/ZN más comisión); ×2 = 6 pb.
- Pasa si: t neto ≥ 2,4 en 2009-2026; segunda mitad > 0; costes ×2 > 0; y el placebo (mismas ventanas dos
  semanas después, sin subasta) no da un resultado igual o mayor.
- Informativo (no decide): 1990-2008 como réplica; resultado por plazo.

## Idea 2. Rebalanceo de fondos de pensiones a fin de mes (Harvey, Mazzoleni y Melone, 2025)
Mecanismo: carteras 60/40 que rebalancean por calendario venden lo que más subió en los últimos días del mes.
- Señal al cierre del 5.º día hábil antes del último del mes: retorno del mes hasta ese día del S&P 500 (^GSPC)
  menos el del bono a 10 años. Si es > 0: corto S&P / largo bono; si es < 0, al revés.
- Mantener del cierre de ese día al cierre del penúltimo día hábil del mes (4 días). Patas a igual volatilidad
  (60 días), suma de riesgo constante.
- Coste: 3 pb por operación (ES 0,5 pb + ZN 1 pb por lado); ×2 = 6 pb.
- Periodo: 1999-01 → 2026-10 (la muestra publicada acaba en 2023-03; 2023-04 → 2026-10 es fuera de muestra).
- Pasa si: t neto ≥ 2,4; segunda mitad > 0; costes ×2 > 0; supera al placebo de mitad de mes (misma regla con
  señal al día 10 del mes y 4 días de tenencia); y 2023-04 → 2026-10 > 0.

## Triaje T0 (aviso de potencia)
Las dos están al límite: con el Sharpe publicado dividido por 2 (~0,5-0,7) harían falta 20-40 años para verlas con
un 80 % de probabilidad. Un "no pasa" será clase C (sin potencia) si el signo y el tamaño coinciden con el artículo,
y clase A si no. Un "pasa" es firme.
