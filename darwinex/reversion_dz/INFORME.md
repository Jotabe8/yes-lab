# Reversión de varios días en índices US para Darwinex Zero (17-11-2026)

**Veredicto: PASA P0-P4** (n_pruebas = 10, t requerido 2,58). Primer candidato con ventaja propia que solo cabe en DZ:
mantiene 1-5 días, algo que en las prop CFD mata el swap y la pérdida diaria. Siguiente: P5 (EA MQL5) y P6 (incubación).
Preregistro: `PREREGISTRO.md` (escrito y subido antes de bajar los datos, commit 67c5563).

## Regla
Al cierre: si IBS = (C − L)/(H − L) < 0,20 y C < C de ayer → largo. Salida al cierre del primer día con C > H de ayer, o
a las 5 sesiones. Sin stop. ES, NQ, RTY, YM (señal sobre ^GSPC, ^NDX, ^RUT, ^DJI). R = movimiento / ATR20.

## Resultados (salida_reversion.txt, salida_p4_redteam.txt, salida_cfd_mc.txt)
| Puerta | Resultado |
|---|---|
| P1 2003-22 | 2.424 ops (~30/año/mercado, 3,1 días). Bruto +0,261 R t 9,3; coste DZ 0,025 R (×10); **placebo de exposición** (mismas duraciones en días aleatorios = misma beta) media +0,086, p95 +0,128 → exceso +0,175 R; 4/4 mercados > 0 |
| P2 | Neto +0,236 (×2 coste +0,210); 18/20 años > 0; meseta IBS 0,15/0,25 y salida 4/6 días todas +0,20-0,27; entrada en la apertura siguiente +0,236 t 8,6 |
| P3 2023-26 (abierto una vez) | 447 ops, neto +0,270 R t 4,38 (ES +0,28, NQ +0,36, RTY +0,14, YM +0,32). Total 2003-26 t 9,4 |
| P4 DZ | Sharpe diario ES 0,85 / NQ 1,13 / RTY 0,66 / YM 0,77 frente a comprar y mantener 0,57 / 0,73 / 0,46 / 0,51 (2023-26 ES y NQ por debajo: 0,87 vs 1,22 y 1,14 vs 1,25). Con el ORB 2018-26 a igual volatilidad: corr mensual −0,02, **Sharpe 1,04 → 1,72**, peor DD 27,3 → 20,6 R; con la ventaja de la reversión a la mitad, 1,23 |

## Red team (lo que podría engañar y qué se comprobó)
1. **Las 4 US son casi el mismo mercado:** t por fecha de señal (1.338 fechas) 5,75; 2003-22 5,07; 2023-26 2,78. Sigue pasando.
2. **Anticipación al cierre:** con los **futuros** reales (Yahoo =F) entrando en la apertura Globex de las 18:00, después de la
   señal, y quitando las operaciones que cruzan un roll: ES +0,28 t 5,8, NQ +0,28 t 5,5, YM +0,24 t 4,6, RTY +0,09 t 1,1
   (solo desde 2017); por fecha +0,216 t 5,9, 2023-26 t 2,5. Traza a mano de 3 operaciones de NDX 2026: IBS, ATR y salida
   usan solo datos del cierre de ese día o anteriores.
3. **Colas sin stop:** peor operación −10,6 R (29-01-2018, Volmageddon, ES/YM/RTY a la vez), p1 −4,2 R. Está dentro del
   Sharpe y del DD de arriba, pero es la cola real: el riesgo por operación debe fijarse por esta cola, no por la media.
4. **No se replica en Europa:** DAX +0,05 (t 0,8), Euro Stoxx −0,04. El efecto es de EE. UU. (encaja con flujos de ETF,
   volatilidad objetivo y compradores de caídas de EE. UU.). Se opera solo en US.
5. **Es una anomalía publicada (Connors 2004, IBS):** aun así sigue viva en 2023-26 con el mismo tamaño. En el embudo de
   prop murió por coste/swap intradía, no por falta de efecto.

## Dónde operarla en DZ
- **Cuenta de futuros** (56 $/mes, sin swap): ES, NQ, YM (RTY flojo en futuros). 1 contrato ES ≈ 0,4 % del millón de vol diaria: granularidad suficiente.
- **Cuenta CFD** (la del ORB): aun con swap largo 6,5 %/año del nominal, NQ neto +0,258 R t 5,2 y ES +0,162 t 3,2
  (swap del US500 supuesto igual al del NDX, sin verificar). Evitaría abrir la cuenta de futuros y portar el ORB al NQ.
- Monte Carlo 36 meses (dz_sim, 1 R ≈ 0,45 %): ORB solo CFD +312 €/año (+1.807 con permanente +10 %); ORB + reversión
  +1.085 €/año (+3.992 con permanente); con la ventaja de la reversión a la mitad +477 (+2.408).

## Pendiente (P5-P6)
EA MQL5 desde `metodo/PlantillaPropEA.mq5`: señal a las 15:58-15:59 NY con la vela diaria en curso, entrada a mercado,
salida al cierre; comparación operación a operación con este Python en el Strategy Tester (no en el terminal de la cuenta real);
luego incubación en demo 4-8 semanas dentro de la banda del Monte Carlo.
