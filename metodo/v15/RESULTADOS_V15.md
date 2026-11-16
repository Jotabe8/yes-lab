# Resultados v15 · Cointegración con Kalman y saltos de Hawkes · 16-11-2026

Preregistro: `PREREGISTRO_V15.md` (commit 901ab75, antes de bajar datos). Datos: M1 bid/ask Dukascopy en precio medio,
sesión regular, `datos/*.npz` (workflow `v15-datos.yml`): US100 y US500 2012-26, US30 y GER40 2013-26.
Salidas completas: `h1_salida.txt`, `h2_salida.txt`. Ambos motores limpios en velas barajadas (sesgo ≈ 0).

## Veredicto: las dos DESCARTADAS (clase A, sin ventaja bruta). No se rescatan.

| | H1 valor relativo US500/US100/US30 (Kalman) | H2 saltos endógenos vs exógenos (Hawkes) |
|---|---|---|
| Operaciones | 5.231 (≈ 350/año) | 7.752 (≈ 550/año) |
| Bruto / coste por op | **−0,028 R** / 0,055 R | **+0,005 R** / 0,019 R |
| Neto cartera diaria | −0,083 R, t −2,83 | −0,013 R, t −2,72 |
| Mitades (neto) | −0,054 / −0,032 | −0,048 / −0,020 |
| Costes ×2 | −0,100 | −0,053 |
| Mercados/pares con neto > 0 | 0/3 | 0/4 |
| Placebos | seguir +0,028 bruto (neto < 0); día anterior −0,029 | al revés −0,015 bruto; aleatorio p95 −0,011 neto |
| Corr ORB v018 | −0,14 | +0,06 |
| Motor (10 réplicas barajadas) | bruto −0,004, t −1,0 | bruto −0,001, t −0,5 |
| Variantes | z 2,5: −0,072 t −2,7; sin objetivo: −0,092 t −2,9 | η 0,3/0,7: −0,012 t −2,6; salida 60: −0,018 t −2,8 |

**H1.** La separación intradía entre índices US no revierte: si acaso sigue un poco (bruto −0,03 R en contra;
2 de 3 pares con bruto negativo, solo US500/US100 +0,013 R, menos de un cuarto de su coste). La separación típica
al entrar es de 23 pb, así que el coste de las dos patas (≈ 1,3 pb) ya se come 0,05 R. Ningún año con neto > 0.

**H2.** El Hawkes se ajusta bien (ramificación 0,5-0,8, como en la literatura: la mayoría de los saltos son endógenos),
pero la clase no predice el sentido: los choques "endógenos" tampoco revierten (en contra −0,011 R bruto) y los
"exógenos" siguen solo +0,020 R. La diferencia entre clases (≈ 0,03 R) es del tamaño del ruido y menor que el coste.
Confirma v3: en índices baratos los choques de minutos no tienen pagador visible con precios de CFD.

**Lección.** Las dos herramientas funcionan (Kalman estable, MLE de Hawkes recupera parámetros en simulación:
μ 0,0098 vs 0,010, ramificación 0,61 vs 0,60, β 0,22 vs 0,20), pero una matemática mejor no crea un pagador.
En US100/US500/US30/GER40 intradía, dirección a minutos y valor relativo están arbitrados; lo único que paga sigue
siendo la volatilidad de apertura (ORB). Descartadas en T0 sin datos: HMM, entropía, espectral/wavelets, valores
extremos, recurrencia y CUSUM (motivos en el preregistro).
