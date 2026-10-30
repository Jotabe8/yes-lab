# FundingPips para los ORB (30/10/2026)

**Conclusión: FundingPips sirve como firma adicional, sobre todo en cuentas de 10K, pero no sustituye a FTMO y no
hace falta correr por Halloween.** El descuento de Halloween (20 % a clientes nuevos, código `HALLOWEEN`) es el
mismo 20 % que da siempre el código de bienvenida `HELLO` en la primera compra. El cambio de verdad frente a lo que
pensábamos: el EA propio está permitido si se demuestra que es tuyo (el `.mq5` fuente vale), así que el motivo por
el que se descartó FundingPips el 26/10 ya no aplica.

## Reglas que importan (2-Step Standard)

| | FundingPips 2-Step Standard | FTMO 2-Step |
|---|---|---|
| Objetivos | **8 % / 5 %** | 10 % / 5 % |
| Días mínimos | 3 por fase | 4 |
| Pérdida diaria / máxima | 5 % / 10 % estática (diaria sobre el mayor de saldo o equity a las 00:00 UTC+3) | 5 % / 10 % |
| Precio de lista 10K / 25K / 50K / 100K | 63 / 168 / 285 / 544 $ (≈ 56 / 150 / 254 / 486 €) | 89 / 250 / 345 / 540 € |
| Reparto | 60 % semanal, **80 % quincenal**, 90 % a demanda (consistencia 35 %), 100 % mensual (consistencia 35 % + 7 días ≥ 0,5 %) | 80 % (90 % con Scaling) |
| Cuota devuelta | en el **4º** retiro | en el 1º |
| EAs | propio permitido con prueba de autoría (código fuente); de terceros solo como gestor | permitido |
| Noticias | **solo en fondeada (Master)**: se quita el beneficio de operaciones abiertas o cerradas a < 5 min de una noticia fuerte de la divisa afectada (10 min en discursos) | Swing: sin restricción |
| Riesgo por idea (Striking System) | Master ≥ 25K: flotante de −1,2 % (o 1 %) en una idea = aviso; avisos repetidos bajan el reparto y cierran la cuenta | no |
| Apalancamiento índices | fases: 1:20; **Master: escalonado por lotes, 1:5 por encima de 0,5 lotes** (temporal desde 16/03/2026) | por confirmar en MT5 |
| Otros | fin de semana: cierre automático el viernes; 30 días sin cerrar operación = cuenta perdida; copiar la misma estrategia entre tus cuentas permitido; tope 300-400K entre todas las cuentas (las fuentes difieren); índices sin comisión; MT5 sí | |

**Consecuencia para el ORB:** en fondeada no se puede arriesgar el 1,5 % como en FTMO. Con el stop del ORB (≈ 0,2 % del
precio; GER40 mediana 0,19 %, p10 0,14 % en el tester) y apalancamiento 1:5, el nominal máximo da para ≈ 0,6-1,1 % de
riesgo según el día, y en cuentas ≥ 25K el Striking avisa con −1,2 % flotante. Riesgo fondeado realista: **0,75-1 %**.
En las fases (1:20) el 2 % sí cabe.

## Simulación 1 año (fp_vs_ftmo.py, fp_10k.py)

Mismo método que dos-orb/ (bloques de 20 días 2022-26, 20.000 MC, coste 0,05 R, recompra al quemar, retiro cada 10 días
hábiles al 80 %). FundingPips con la primera compra al −20 % y recompras a precio de lista. "Noticias 10 %" = se anula el
beneficio del 10 % de los días ganadores en fondeada (estimación: no tengo el calendario de noticias "restringidas").

**€ netos al año por cuenta, US100:**

| Cuenta | Cuota | Media | Mediana | Año < 0 | Caja p10 | Media costes ×2 |
|---|---|---|---|---|---|---|
| FTMO 100K (2/1,5 %) | 540 € | 29.300 | 25.700 | 7 % | −3.800 | 22.000 |
| FP 100K (2/1 %, sin noticias) | 389 € | 24.900 | 22.900 | 4 % | −2.800 | 19.900 |
| FP 100K (2/1 %, noticias 10 %) | 389 € | 18.600 | 16.600 | 7 % | −2.800 | 14.600 |
| FP 100K (2/0,75 %, noticias 10 %) | 389 € | 14.200 | 12.700 | 7 % | −2.800 | 11.100 |
| FTMO 50K (2/1,5 %) | 345 € | 14.200 | 12.500 | 9 % | −2.400 | 10.500 |
| FP 50K (2/1 %, noticias 10 %) | 204 € | 9.200 | 8.300 | 7 % | −1.500 | 7.200 |
| **FTMO 10K (2/1,5 %)** | 89 € | 2.750 | 2.400 | 11 % | −620 | 2.000 |
| **FP 10K (2/1 %, sin noticias)** | 45 € | 2.450 | 2.260 | 4 % | −330 | 1.950 |
| **FP 10K (2/1 %, noticias 10 %)** | 45 € | 1.820 | 1.620 | 8 % | −330 | 1.410 |
| FP 10K (2/1,5 %, sin noticias)* | 45 € | 3.220 | 2.870 | 6 % | −380 | 2.520 |

\* En 10K no hay Striking; si el margen deja el 1,5 % depende del tamaño de contrato del NAS100 en FundingPips (míralo en la
cuenta de prueba gratis).

Otras variantes: el reparto **100 % mensual no sirve** al ORB (la regla del 35 % de consistencia lo bloquea: mediana ≈ 0,
56 % de años negativos); **2-Step Pro** (diaria 3 %, máx. 6 %) rinde un tercio (8.350 € en 100K, 21 % años negativos).
Combinación US100 100K + GER40 50K: FTMO 36.600 € / FP 17.900 € (caja −5.000 / −3.300).

**Lectura:**
- En cuentas grandes FTMO gana: cobra con el 1,5 % de riesgo y sin norma de noticias. Una FP 100K rinde el 50-85 % de
  una FTMO 100K con el 75 % de la caja.
- En 10K FundingPips es igual o mejor por euro arriesgado: cuesta la mitad (45 € frente a 89 €) y la caja en el 10 %
  peor es −330 € frente a −620 €. Encaja con el presupuesto de 100-200 €/mes.
- Como tercera firma (repartir riesgo de firma y sumar capacidad fuera del tope de FTMO) compite con The5ers y E8.

## Recomendación

1. **No hace falta comprar antes de que acabe Halloween:** `HELLO` da el mismo 20 % en la primera compra (según
   cryptoslate excluye la de 100K). Halloween solo añade un 15 % para clientes que ya hayan comprado.
2. Antes de comprar, abrir la **cuenta de prueba gratis** de FundingPips en MT5 y mirar en Especificación del NAS100
   (y DE40): tamaño de contrato, spread a las 15:30-16:00 hora de Madrid y margen con 2-3 lotes. Así sabremos si en Master
   cabe el 1 % (o el 1,5 % en 10K).
3. Si cuadra, usar FundingPips como la tercera firma del plan (enero) con **2-Step Standard 10K, US100**, riesgo 2 % en
   fases y 1 % en Master, reparto **quincenal 80 %**, y el filtro de noticias USD del EA activado solo en Master.
4. Tener a mano el `.mq5` fuente por si piden la prueba de autoría.

## Pendiente de verificar (las webs oficiales no se pudieron leer desde aquí)
- Fecha de fin de la promoción de Halloween (ninguna fuente la publica).
- Si la norma de noticias se aplica a NAS100/DE40 (las fuentes hablan de "divisa afectada").
- Si el apalancamiento escalonado sigue vigente y cómo cuenta los lotes (por símbolo o total).
- Si el Striking System es 1 % o 1,2 % y si aplica a 25K.
- Spreads y swap reales (el ORB no deja posiciones de noche).

## Fuentes
- Halloween: https://forexpropreviews.com/fundingpips-halloween-sale-offers-up-to-20-off/ (29/10/2026)
- Web oficial (código HELLO, 2-Step 8 %/5 %/5 %/10 %): https://fundingpips.com
- Reglas por modelo: https://tradetanto.com/learn/fundingpips-rules ; https://proptradingvibes.com/blog/fundingpips-rules
- Precios y Striking: https://cryptoslate.com/prop-firms/fundingpips-review/ ; https://www.proptradingvibes.com/blog/fundingpips-account-types
- Apalancamiento escalonado: https://proptradingvibes.com/blog/fundingpips-dynamic-leverage
- EAs, noticias, copia entre cuentas: https://pickmytrade.io/prop-firm-faq/fundingpips/ ; https://blog.pickmytrade.io/fundingpips-review-rules-payouts-automation/
- Centro de ayuda oficial (bloqueado desde el contenedor): https://help.fundingpips.com/hc/en-us/articles/34501809112081-2-Step-Standard
