# Resultados v13 · ORB "en juego" en aperturas propias (16-11-2026)

Preregistro: `PREREGISTRO_ORB_EN_JUEGO.md` (commit 271b557, subido antes de bajar los datos).
Datos: M1 Dukascopy bid/ask con volumen 2012-2026 (workflow v13-orb-en-juego.yml; faltan GER40 2012 y JP225 2012-13
por fallo de descarga). Salida completa: `salida_v13.txt`; comprobaciones posteriores: `robustez_v2_salida.txt`.

## Veredicto
| Variante | Ops | Bruto R | Neto R (t) | 2.ª mitad | Costes ×2 | Placebo días p95 | Lado contrario | Mercados + | Corr v018 | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 volumen ≥ 1,5 (principal) | 2.116 | +0,207 | +0,128 (2,27) | +0,182 | +0,049 | +0,123 | −0,181 | 4/5 | −0,03 | **NO PASA** (t < 2,4) |
| **V2 rango ≥ 1,5** (listón 2,64) | 2.157 | +0,275 | **+0,200 (3,35)** | +0,150 | +0,126 | +0,130 | −0,143 | 5/5 | −0,01 | **PASA los 7 criterios** |
| Incondicional (referencia) | 15.786 | +0,126 | +0,053 (2,85) | | −0,020 | | | | | — |

V2 por mercado (neto R, t): GER40 +0,31 (2,10) · UK100 +0,18 (1,33) · JP225 +0,11 (0,90) · oro +0,25 (1,96) · crudo +0,13 (1,02).
Ninguno pasa solo; la ventaja es de la cartera (5 mercados, horas distintas, corr entre ellos ≈ 0 salvo GER40-UK100 0,54).
Monte Carlo (bloques de 20 días): P(media ≤ 0) < 0,001; peor DD p50 60 R, p95 98 R (todos los mercados a 1 R); +28 R/año.

## Comprobaciones posteriores (informativas, no cambian el veredicto)
- Umbral: neto sube de forma monótona 1,0 → 2,5 (+0,11 → +0,42 R); t ≥ 3 entre 1,0 y 1,7. No es un pico aislado.
- 14 de 15 años con neto > 0 (2021 negativo). Sin 2012: +0,18 t 2,99. **2018-2026: +0,14 t 1,95** (más flojo).
- Sin el crudo (coste no medido): +0,22 t 3,24. Solo GER40+UK100+oro (los costes más baratos): +0,25 t 3,13.
- Perfil convexo: gana el 24 % de las veces, mediana −1 R; sin el 1 % de mejores operaciones t 0,99. **El v018 es igual**
  (31 % ganadoras; sin el 1 % mejor t 1,45): es la forma normal de un ORB con salida al cierre.
- Sharpe anual de la cartera V2 0,82. v018 solo 0,97 → v018 + 0,5·V2 **1,16**; corr mensual −0,13.
- V1 (volumen) falla probablemente porque el volumen de Dukascopy es el de su propio libro, no el de la bolsa.

## Lectura
Primera hipótesis desde el ORB US100 que pasa un preregistro completo con coste real, placebos y correlación ≈ 0.
Riesgos que quedan: (1) es una prueba en Python (P3); falta paridad MQL5 y Strategy Tester con ticks FTMO (P4-P5);
(2) horquillas reales de USOIL, JP225 y oro a esas horas sin medir en MT5 (oro y JP225 de la tabla de FTMO, crudo
estimado); (3) 2018-26 más débil (t 1,95); (4) DD largo en R: con 5 mercados a la vez el riesgo por operación tiene
que ser bajo (≈ 0,25-0,35 %).
Registro: clase F provisional (pendiente P4-P6).

## Horquillas reales FTMO (16-11, script MedirHorquillasEnJuego, 60 días, 1.ª hora de cada apertura)
GER40 0,0051 % · UK100 0,0079 · JP225 0,0155 · XAUUSD 0,0099 · **USOIL 0,089 %** (el preregistro suponía 0,05).
Con el coste real: cartera de 5 neto +0,178 R t 2,97 (×2 +0,08); **el crudo queda en +0,02 R neto: fuera en CFD**.
**Cartera recomendada para MT5: GER40 + UK100 + JP225 + XAUUSD** → neto +0,218 R t 3,24, 2.ª mitad +0,15, ×2 +0,16,
~116 ops/año. (Quitar el crudo es una decisión de lugar, no de muestra: su bruto +0,27 R sigue ahí para MCL en futuros.)

## P5 (16-11, MT5 de laboratorio; informe completo en el PC: segundo_sistema_v13\P5_PARIDAD.md)
- Compila 0 errores / 0 avisos.
- **GER40 con ticks FTMO 2022-01 → 2026-05: EA 134 ops vs Python 138, 129 comunes, mismo lado 100 %, corr R 0,999,
  R media +0,018 vs +0,019.** Los 14 desparejados están en el borde del umbral 1,5. Paridad muy buena.
- XAUUSD (demo MetaQuotes, no FTMO): 129 comunes, mismo lado 100 %, corr R 0,898 (1,000 sin el 04-04-2025); R media
  EA +0,24 vs Python +0,59. Causas: servidor de la demo con verano UE (19 de 35 desparejados), días en el borde, y el
  04-04-2025 (Python +15 R, EA −1 R: stop de 4,9 $ saltado a los 30 s).
- **Aviso oro:** la entrada es a las 8:30 NY, el minuto de NFP/IPC. En Python el oro gana +0,84 R en esos 58 días y
  +0,18 R (t 1,4) el resto: parte de su resultado depende de llenar justo en el dato. Sin el oro en días de dato la
  cartera de 4 sigue en +0,197 R t 2,94 (2018+ +0,13 t 1,67). Solo índices (GER40+UK100+JP225): +0,203 R t 2,58.
- Pendiente: XAUUSD_FTMO con ticks FTMO; desfase del servidor automático si se usa fuera de FTMO (ServidorAUtc
  supone NY+7); P6 en demo.
