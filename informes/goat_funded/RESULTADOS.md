# Goat Funded Trader (GFT) para el ORB US100 (05/11/2026)

**Conclusión: no la recomiendo como firma del plan.** Los números salen bien porque la cuota es muy barata, pero el
riesgo de que no paguen es alto y no se puede medir: Trustpilot les retiró la nota en agosto de 2026 por infringir sus
normas (reseñas falsas), la nota visible es 1,6/5 con un 91 % de reseñas de 1 estrella, y las quejas son justo del tipo
que afectaría a un EA: pagos denegados por "trading coordinado", "varias cuentas desde el mismo dispositivo" o IP
compartida. Además opera con su propio bróker MT5 (desde abril de 2025), sin regulación (Goat Funded LTD, Santa Lucía).
Si se quiere probar, como mucho **una 2-Step GOAT de 15K con cupón (≈ 45-50 €)**, después de FundingPips y tratando
cualquier retiro como un extra, no como parte del plan.

No pude leer la web oficial (goatfundedtrader.com) desde el contenedor; todo viene de agregadores con fecha, abajo.
Antes de comprar hay que confirmarlo en la web oficial.

## Reglas relevantes para el ORB

| Tema | GFT | ¿Problema para el ORB? |
|---|---|---|
| EAs | Propios permitidos; de terceros solo si se demuestra autoría. Prohibidos HFT, arbitraje | No (el ORB es propio; guardar el .mq5 y el historial de yes-lab) |
| Copy / misma operativa | Copy trading solo entre fondeadas propias de GFT; prohibido en evaluación y hacia/desde cuentas externas. "Operaciones repetidas y muy coordinadas pueden revisarse como copy trading". Hedging entre firmas = baneo | **Sí.** El mismo EA en FTMO y GFT a la misma hora es justo lo que pueden llamar coordinado. Con 1 sola cuenta en GFT el riesgo baja, pero no desaparece |
| Noticias | Permitidas; operaciones abiertas/cerradas ±2 min de noticia fuerte (ForexFactory) con beneficio topado al 1 % del saldo | Poco: el ORB rara vez coincide; se recorta, no se pierde la cuenta |
| Operaciones < 2 min | Beneficio anulado (pérdida se queda) | No |
| Fin de semana / noche | Permitido | No (el ORB cierra en el día) |
| Goat Guard (fondeada) | Cierre con ≈ −2 % flotante; 1ª vez split al 50 %, 2ª cuenta perdida | Obliga a riesgo fondeado ≤ 1 % (al 1,5 % un stop con deslizamiento llega a −2,25 %) |
| Tope de beneficio diario | 3.000 $ | Solo en cuentas ≥ 100K |
| Retiros | Cada 14 días, mínimo 100 $, split 80 % (hasta 100 % con extras), comisión 2 % tras el split. **Los 2 primeros topados al 6 % del saldo inicial o 10.000 $** (el exceso se pierde). 3 días con ≥ +0,5 % por ciclo | Recorta algo los primeros meses |
| Margen >80 % | "Todo o nada": deducciones o cierre | No con el tamaño del ORB |
| Apalancamiento | 1:100 general (agregadores); índices hasta 1:15 en artículos antiguos | Sin confirmar en índices |
| Plataformas | MT5 (bróker propio), cTrader, Match-Trader, TradeLocker | MT5 sí; símbolo, spread y swap de US100 sin confirmar |
| Tope de capital | No publicado | — |

## Modelos 2-Step y precios de lista (propfirmsfinder, verificado 02/11/2026)

| | 5K | 8K | 15K | 25K | 50K | 100K |
|---|---|---|---|---|---|---|
| **GOAT** (8 %/6 %, diaria 4 %, máx 10 % estática) | 36 $ | 56 $ | 98 $ | 148 $ | 288 $ | 458 $ |
| Standard (10 %/5 %, diaria 5 %, máx 10 %) | 52 $ | 108 $ | 208 $ | 228 $ | 338 $ | 594 $ |
| *FTMO 2-Step (10 %/5 %)* | | *10K 89 €* | | *25K 250 €* | *50K 345 €* | *540 €* |

No hay 10K en 2-Step. Cupones vistos: FIRSTGFT 50 % (primera compra), GFT40/BOGO40 40 %, GFT45 45 % (sep-2026).
Hay que mirar en la web cuál está activo hoy. El 2-Step Pro se retiró el 13/06/2026 (propnavi).

## Simulación 1 año, US100 (gft.py)

Mismo método que FundingPips (bloques de 20 días 2022-26, 20.000 MC, coste 0,05 R, recompra al quemar). GFT con días
de +0,5 %, retiros cada 10 días hábiles al 80 % −2 %, dos primeros topados al 6 %, tope diario 3.000 $, noticias
recortando el 5 % de los días ganadores al 1 %. Sin devolución de cuota. **No incluye el riesgo de impago.**

| Cuenta | Cuota | Media €/año | Mediana | Año < 0 | Caja p10 | Media costes ×2 |
|---|---|---|---|---|---|---|
| FTMO 10K 2/1,5 | 89 € | 2.745 | 2.396 | 11 % | −623 | 1.979 |
| GFT GOAT 8K −50 % 2/1 | 25 € | 1.376 | 1.188 | 6 % | −175 | 1.045 |
| **GFT GOAT 15K −50 % 2/1** | 44 € | 2.599 | 2.246 | 6 % | −306 | 1.980 |
| GFT GOAT 15K −40 % 2/0,75 | 52 € | 2.160 | 1.924 | 6 % | −315 | 1.664 |
| GFT GOAT 25K −40 % 2/1 | 79 € | 4.248 | 3.688 | 6 % | −555 | 3.221 |
| GFT Standard 25K −40 % 2/1 | 122 € | 3.845 | 3.255 | 11 % | −855 | 2.755 |
| FTMO 25K 2/1,5 | 250 € | 6.718 | 5.858 | 12 % | −1.753 | 4.771 |

**Lectura:** sobre el papel, GFT GOAT es lo más barato por euro de caja que hemos visto (15K ≈ FTMO 10K con la mitad de
caja en riesgo). El GOAT es mejor que el Standard para el ORB (8 %/6 % se pasan antes). Pero con riesgo de impago el
cálculo no vale: si la probabilidad de que denieguen un retiro es, por ejemplo, del 30-50 % (lo que sugieren las
quejas), la media real baja a la mitad o menos, y lo que se pierde no es la cuota sino el beneficio ya ganado.

## Si se prueba
1. Primero FundingPips (enero) como 3ª firma, tal como estaba en el plan.
2. Como 4ª, opcional: 1 sola GFT 2-Step GOAT 15K con el mayor cupón, riesgo 2 % en fases y 1 % fondeada.
3. MT5 siempre desde el mismo PC e IP, sin VPN; nunca 2 cuentas GFT a la vez; guardar el .mq5 fuente como prueba.
4. Comprobar en la cuenta: símbolo y spread de US100 a las 15:30-16:00 de Madrid, comisión, apalancamiento de índices.
5. Pedir el primer retiro en cuanto sea posible (mínimo 100 $) para probar que pagan.

## Fuentes (agregadores; la web oficial no se pudo abrir)
- propfirmsfinder.com/prop-firm/goat-funded-trader/challenges/ (precios, 02/11/2026)
- propnavi.io/en/blog/goatfundedtrader-review/ (reglas fondeada, red flags, 22/09/2026)
- propfirmmap.com/trust-check/goatfundedtrader (cronología Trustpilot, 2026)
- trustpilot.com/review/goatfunded.com (1,6/5, quejas jul-ago 2026)
- cryptoslate.com/prop-firms/goat-funded-trader-review/ (pagos, plataformas, entidad, 04/10/2026)
- tradingfinder.com/props/goat-funded-trader/rules (EAs, noticias, copy, 07/01/2026)
- propvator.com/blog/is-copy-trading-allowed-at-goat-funded-trader/ (copy y EA en varias cuentas, 24/08/2026)
