# FundingPips para los ORB (30/10/2026, condiciones oficiales)

**Conclusión: FundingPips vale como firma adicional para el US100, sobre todo en 10K o 50K, pero no sustituye a FTMO
en cuentas grandes y no hace falta correr por Halloween.** Condiciones leídas en la web oficial (help.fundingpips.com y
fundingpips.com) con el navegador el 30/10/2026.

## Lo que dice la web oficial

**Promoción:** banner "HALLOWEEN SALE: 20 % OFF New Clients | 15 % OFF Existing Clients – Code: HALLOWEEN". No pone fecha
de fin. El código de bienvenida `HELLO` también da 20 % en la primera compra, así que Halloween solo aporta algo si ya
eres cliente (15 %).

**Precios de lista (2-Step, diaria 5 %):**

| | 10K | 25K | 50K | 100K |
|---|---|---|---|---|
| Standard (8 %/5 %, máx 10 %) | 72 $ | 195 $ | 349 $ | 652 $ |
| Flex (10 %/8 %, diaria 4 %, máx 12 %) | 64 $ | 175 $ | 299 $ | 555 $ |
| Pro (6 %/6 %, diaria 3 %, máx 6 %) | 55 $ | 145 $ | 249 $ | 466 $ |
| *FTMO 2-Step (10 %/5 %)* | *89 €* | *250 €* | *345 €* | *540 €* |

**2-Step Standard:**
- Fases: 8 % y 5 %, 3 días mínimos por fase, sin límite de tiempo. Diaria 5 % sobre el mayor de saldo o equity de
  apertura del día; máxima 10 % estática. 30 días sin cerrar una operación = cuenta perdida.
- Retiros: semanal 60 %, **quincenal 80 % (sin más condiciones)**, o "On Demand" 100 % con consistencia 35 %, 7 días
  con ≥ 0,5 % y **Striking System** (aviso si una idea pierde 1 % entre cerrado y flotante; 2º aviso reparto a la mitad,
  3º al 20 %, 4º cuenta cerrada). **El Striking solo aplica al ciclo On Demand.** Mínimo de retiro 1 %.
  Cuota devuelta en el **4º** retiro (solo Standard).
- Reset con descuento (12 % fase 1, 10 % fase 2, 7 % Master) si se compra en 7 días.

**2-Step Flex:** 10 % y 8 %, diaria 4 %, máxima 12 %. Se elige al comprar: 80 % quincenal (1 día mínimo) o **95 %
quincenal con 3 días ≥ 0,5 % por fase y por ciclo**. Sin consistencia en los quincenales, sin devolución de cuota.

**Noticias:** en las fases no hay restricción. En Master se **quita el beneficio** de operaciones abiertas o cerradas de
5 min antes a 5 min después de una noticia fuerte de la divisa afectada (en discursos, toda la duración más 5 min). No
cierra la cuenta. Las operaciones abiertas 5 h antes o más quedan exentas. Calendario oficial: el del panel de FundingPips.
"Operar noticias a propósito" está prohibido en todas las fases. Los ejemplos hablan de pares USD; no aclara índices.

**Noche y fin de semana:** permitidos en fases; en Master Standard/Flex el sistema **cierra todo cada día** entre
20:45-21:00 UTC en verano y 21:45-22:00 UTC en invierno (las 22:45 de Madrid en los dos casos), sin penalizar. Al ORB no le afecta
(cierra antes, con el cierre de contado). El add-on Swing evita el cierre pero baja índices a 1:5 también en fases: no comprarlo.

**Apalancamiento y comisión:** índices 1:20 en fases y **en Master escalonado por lotes** (1:50 hasta 0,05; 1:30; 1:25;
1:20; 1:10; **1:5 por encima de 0,5 lotes**), "temporal" desde el 16/03/2026. Índices sin comisión. Máximo 20 lotes por
orden. Índices disponibles: NDX100, GER40, SPX500, DJI30, FTSE100, JP225, STX50. Tamaño de contrato y swap: solo en la
plataforma (MT5, cTrader o Match-Trader).

**EAs:** de terceros solo como gestor de riesgo. **EA propio con automatización completa permitido** si se demuestra
autoría: código fuente `.mq5` sin compilar, historial de versiones, pruebas del entorno de desarrollo o explicar la
lógica en una llamada. El `.ex5` solo no vale. Prohibidos: gap trading, HFT, arbitraje, tick scalping, hedging, cuentas
opuestas. **La misma estrategia en varias cuentas propias está permitida.** **Prohibido conectarse con VPN o VPS**:
el MT5 tiene que correr en tu PC, y la IP debe ser siempre de la misma región.

**Tope:** 400.000 $ entre todas las cuentas (web oficial).

**Consecuencia para el ORB:** en las fases el 2 % de riesgo cabe. En Master el tope lo pone el margen: con el stop del
ORB (≈ 0,2 % del precio; GER40 mediana 0,19 %, p10 0,14 %) y 1:5, el nominal máximo da para ≈ 0,6-1,1 % de riesgo según
el día. Con reparto quincenal no hay Striking. **Riesgo fondeado realista: 0,75-1 %** (en FTMO usamos 1,5 %).

## Simulación 1 año, US100 (fp_oficial.py)

Mismo método que dos-orb/ (bloques de 20 días 2022-26, 20.000 MC, coste 0,05 R, recompra al quemar). FundingPips con la
primera compra a −20 % y recompras a −15 %. "Noticias 10 %": se anula el beneficio del 10 % de los días ganadores en
Master (estimación; falta medirlo con el calendario).

**€ netos al año por cuenta, riesgo 2 % en fases / 1 % en fondeada (FTMO 1,5 %):**

| Cuenta | Cuota | Media sin noticias | Media noticias 10 % | Año < 0 | Caja p10 | Media costes ×2 (noticias 10 %) |
|---|---|---|---|---|---|---|
| FTMO 100K | 540 € | 29.300 | — | 7 % | −3.800 | 22.000 |
| FP Standard 100K | 466 € | 24.800 | 18.500 | 4-7 % | −2.900 | 14.500 |
| FP Flex 95 % 100K | 396 € | 26.900 | 19.900 | 5-9 % | −2.100 a −2.500 | 15.100 |
| FTMO 50K | 345 € | 14.200 | — | 9 % | −2.400 | 10.500 |
| FP Standard 50K | 249 € | 12.300 | 9.200 | 4-8 % | −1.600 | 7.100 |
| FP Flex 95 % 50K | 214 € | 13.400 | 9.900 | 6-9 % | −1.100 a −1.350 | 7.500 |
| FTMO 10K | 89 € | 2.750 | — | 11 % | −620 | 2.000 |
| FP Standard 10K | 51 € | 2.450 | 1.820 | 4-8 % | −330 | 1.410 |
| FP Flex 95 % 10K | 46 € | 2.670 | 1.960 | 6-9 % | −240 a −290 | 1.480 |

Con 0,75 % en fondeada, todas las FP bajan un 20-25 %. Ver fp_oficial.csv.

**Lectura:**
- Por cuenta, FTMO gana porque cobra al 1,5 % y sin norma de noticias. FundingPips rinde un 65-90 % de la FTMO del mismo
  tamaño, con un 55-75 % de la caja en riesgo.
- **Por euro arriesgado, FundingPips es igual o mejor**, sobre todo el Flex 95 %: cuota más baja y caja peor de
  −240 € en 10K frente a −620 € en FTMO.
- Flex 95 % y Standard quedan muy parejos; Flex es algo más barato y con más margen (12 %), Standard devuelve la cuota en el
  4º retiro y aprueba antes (8 %).
- Todo depende de dos cosas que hay que medir: el riesgo que deja el margen en Master y cuántas ganancias se comería la
  norma de noticias.

## Recomendación

1. **Sin prisa por Halloween.** `HELLO` da el mismo 20 % en la primera compra.
2. **Abrir la Free Trial** (botón en la web) y anotar en MT5, Especificación de NDX100: tamaño de contrato, spread a las
   15:30-16:00 de Madrid y el margen que pide 1 lote. Con eso fijamos el riesgo de Master.
3. Si cuadra, tercera firma del plan con **una 10K de US100**, 2-Step Flex 95 % o Standard; riesgo 2 % en fases y
   0,75-1 % en Master, y el filtro de noticias USD del EA activado solo en Master.
4. Guardar el `.mq5` fuente y su historial (yes-lab) como prueba de autoría. MT5 en el PC, nunca en VPS.

## Pendiente
- Fecha de fin de Halloween (no publicada).
- Si la norma de noticias afecta a NDX100/GER40 (el texto habla de "divisa afectada").
- Medir el % de operaciones del ORB que abren o cierran a ±5 min de noticias fuertes USD (calendario de FundingPips).
- El artículo "Risk Per Trade Idea" del centro de ayuda ahora pide iniciar sesión; no aparece en las páginas de
  Standard ni Flex.

## Fuentes oficiales (leídas el 30/10/2026)
- https://fundingpips.com (banner Halloween, precios, tope de 400K)
- https://help.fundingpips.com/hc/en-us/articles/34501809112081-2-Step-Standard
- https://help.fundingpips.com/hc/en-us/articles/47835196271249-2-Step-Flex
- https://help.fundingpips.com/hc/en-us/articles/34505029138449-Trading-Conduct-and-Security-Standards
- https://help.fundingpips.com/hc/en-us/articles/44390730743825-Get-Started
