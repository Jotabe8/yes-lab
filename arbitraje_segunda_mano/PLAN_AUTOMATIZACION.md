# Plan inicial: aplicación de detección automática de chollos de segunda mano

Fecha: 2026-11-24 · Estado: **propuesta**, sin código todavía. Complementa a `PLAN.md`.

Objetivo: una aplicación que revise anuncios de segunda mano de forma automática, reconozca
qué producto es, lo compare con su precio nuevo y con su precio real de reventa, calcule el
margen neto y avise al móvil solo cuando la compra merece la pena. La compra la sigues
haciendo tú.

---

## 0. La decisión previa: de dónde salen los anuncios

**Las condiciones de uso de Wallapop prohíben esto expresamente.** Según el texto de
`about.wallapop.com/condiciones-de-uso` que aparece citado en los resultados de búsqueda
(no he podido abrir la página desde aquí, así que conviene leerla):

> "No extraer de forma sistemática ni reutilizar parte o todo del contenido de la Plataforma,
> sin nuestro expreso consentimiento por escrito. En particular, no se permite (i) el uso de
> herramientas o robots de búsqueda, ni (ii) la extracción de datos."
>
> "No utilizar herramientas de software externas (bots, etc.), salvo que dicho uso sea
> autorizado o permitido por nosotros."

Un blog de Octoparse sitúa estas cláusulas en el punto 3.1.2 y el 17 de la versión del
10-04-2026 (sin verificar). Técnicamente es fácil: hay scrapers comerciales (Apify,
ScrapingBee) que ya lo hacen. El problema es de reglas, no de técnica: riesgo de **cierre de
cuenta** (la misma con la que compras y vendes) y posible reclamación si se usa de forma
comercial.

Por eso la aplicación se diseña con **fuentes intercambiables**, y cada fuente tiene un nivel
de riesgo:

| Fuente | Cómo | Riesgo | En el MVP |
| --- | --- | --- | --- |
| **eBay (Browse API oficial)** | API pública con registro de desarrollador; anuncios activos, también usados | Bajo (permitido) | Sí |
| **Alertas nativas de Wallapop/Vinted** | Búsquedas guardadas de la propia app; leer las notificaciones que te llegan a ti (correo, si las envía; si solo son push, no sirve) | Bajo | Sí, si llegan por correo (a confirmar) |
| **Ruit** | Herramienta que agrega varios mercados; ver si exporta o avisa | Depende de cómo obtiene los datos (preguntarles) | Prueba en paralelo |
| **Wallapop por scraping** | Endpoint interno de búsqueda o actor de Apify | **Alto**: prohibido por sus condiciones | **No**, salvo permiso escrito o decisión explícita tuya asumiendo el riesgo, y nunca con tu cuenta de compraventa |
| **Wallapop con permiso** | Escribir a Wallapop pidiendo acceso (como Wallapop PRO / socio) | Ninguno | Pedirlo en paralelo, poco probable |

**Decidido (24-11-2026):** Wallapop se usa **solo mediante sus propias alertas** de búsquedas
guardadas; nada de saltarse sus defensas. Como el móvil es un iPhone (no permite reenviar
notificaciones de otras apps), la vía a probar es el PC con Windows encendido 24/7:
Enlace Móvil (Phone Link) muestra las notificaciones del iPhone en Windows, y un pequeño
programa con la API oficial `UserNotificationListener` las leería y las pasaría a la
aplicación. **Sin confirmar** que las notificaciones de Phone Link sean legibles así: es lo
primero que hay que probar. Plan B: revisar a mano las alertas y pegar el anuncio en
`evaluar.py`.

**Recomendación:** construir toda la aplicación (catálogo, valoración, margen, alertas,
libro) con eBay y las alertas como primeras fuentes. Es el 80 % del trabajo y vale para
cualquier fuente. Decidir lo de Wallapop cuando el resto funcione y haya números.

---

## 1. Qué hace la aplicación, paso a paso

```
 Fuentes ──► Normalizador ──► Catálogo ──► Valoración ──► Puntuación ──► Alerta Telegram
 (eBay,       (título → modelo,  (modelo      (precio nuevo,  (margen neto,    (solo si pasa
  alertas,     variante, estado,  canónico,    mediana usado,  descuento vs     los filtros)
  Ruit…)       señales de alarma) EAN)         precio suelo)   nuevo, rotación)       │
                                                                                     ▼
                                    Dashboard ◄── Libro de operaciones ◄── Tú compras
```

1. **Fuentes**: cada conector devuelve anuncios con el mismo formato
   (`id, fuente, título, descripción, precio, envío, ubicación, fecha, url, fotos`).
2. **Normalizador**: convierte el texto libre en datos. Reglas para lo fácil y un modelo de
   lenguaje (Claude Haiku) para lo difícil:
   - `modelo` ("Sony A7 III"), `variante` (128 GB, color, kit con objetivo), `estado`.
   - **Señales de alarma**: "para piezas", "bloqueado", "iCloud", "sin cargador", "réplica",
     "sin factura", precio absurdamente bajo (posible estafa).
3. **Catálogo**: lista cerrada de 20–50 modelos que vigilas, con EAN, precio nuevo y
   palabras clave. Lo que no encaja en el catálogo se descarta. Esto es lo que hace el
   sistema fiable: mejor 30 modelos bien conocidos que todo Wallapop.
4. **Valoración**, tres precios por modelo:
   - **Precio nuevo**: Keepa (API oficial de pago, histórico de Amazon) o Idealo (sin API
     oficial; vía actores de terceros) o tabla manual actualizada cada mes.
   - **Mediana de usado**: tus ventas reales + ventas cerradas de eBay (Terapeak a mano; la
     API de ventas cerradas es restringida) + histórico de anuncios que la propia app recoge.
   - **Precio suelo**: tasación de Back Market / CeX (a mano al principio).
5. **Puntuación**:

   ```
   descuento_vs_nuevo = 1 − precio_anuncio / precio_nuevo          (sirve para DETECTAR)
   margen_neto        = mediana_usado × (1 − comisión_venta)        (sirve para DECIDIR)
                        − envíos − reacondicionado − provisión_garantía
                        − p_problema × pérdida − precio_anuncio
   ```

   Ojo: lo que se vende "muy barato respecto a nuevo" no siempre deja margen, porque el
   mercado de usado ya cotiza por debajo de nuevo. **El margen sale de la diferencia con el
   precio de usado, no con el de nuevo.** El descuento sobre nuevo se usa como primer filtro.

   Alerta si: `margen_neto ≥ max(30 €, 25 %)`, sin señales de alarma graves, modelo con
   rotación < 30 días, y `precio_anuncio ≤ precio_suelo + colchón`.
6. **Alerta**: mensaje de Telegram con foto, precio, margen estimado, enlace y botón
   "lo compro / descartar". Lo que pulses alimenta el aprendizaje.
7. **Libro de operaciones**: cada compra con su ID, costes, venta, canal y días en stock →
   margen real, libro REBU, umbrales DAC7 (ver `PLAN.md`).
8. **Dashboard**: página HTML como `docs/index.html` del laboratorio: alertas del día,
   inventario, margen real frente a estimado, error de valoración por modelo.

---

## 2. Tecnología

Mismo estilo que el resto del repo: Python sencillo, pocas dependencias, tests con `unittest`.

| Pieza | Elección | Por qué |
| --- | --- | --- |
| Lenguaje | Python 3 | Como el laboratorio |
| Base de datos | SQLite (`datos/arbitraje.db`) | Un fichero, sin servidor |
| Normalizador | Reglas + Claude Haiku con salida JSON | Barato por anuncio; solo se llama si las reglas no bastan |
| Precio nuevo | Keepa API (o tabla manual en CSV) | Oficial y con histórico |
| Programación | Ejecución cada 15–30 min en un VPS pequeño o en el propio ordenador | GitHub Actions sirve para pruebas, no para tiempo casi real |
| Alertas | Bot de Telegram | Gratis, inmediato, con botones |
| Dashboard | HTML estático generado desde la base | Como `docs/index.html` |
| Secretos | Variables de entorno (claves de eBay, Keepa, Anthropic, Telegram) | Nunca en el repo |

Estructura propuesta:

```
arbitraje_segunda_mano/
  PLAN.md, PLAN_AUTOMATIZACION.md
  app/
    fuentes/        ebay.py, alertas_correo.py, (wallapop.py solo si se decide)
    normalizador.py
    catalogo.py     + catalogo.csv (modelo, EAN, palabras clave, precio nuevo)
    valoracion.py
    puntuacion.py
    alertas.py      (Telegram)
    libro.py
    dashboard.py
    ejecutar.py     (un ciclo completo: fuentes → alerta)
  tests/
```

---

## 3. Fases

### Fase A — Catálogo y calculadora (1–2 semanas)
- `catalogo.csv` con 20–30 modelos de **una** categoría (consolas o cámaras).
- `puntuacion.py` con la fórmula y comisiones por canal como parámetros; tests.
- Precio nuevo y mediana de usado a mano para arrancar.
- **Listo cuando**: dado un anuncio escrito a mano, la calculadora da un margen que
  coincide con tu cálculo en la hoja de la fase 0 de `PLAN.md`.

### Fase B — Primera fuente y normalizador (2 semanas)
- Conector de eBay Browse API (usados en eBay.es, por modelo del catálogo).
- Normalizador con reglas + Haiku; guardar cada anuncio en SQLite (esto va creando el
  histórico de precios).
- **Listo cuando**: el normalizador acierta modelo y variante en ≥ 90 % de una muestra de
  100 anuncios revisada a mano.

### Fase C — Alertas (1 semana)
- Bot de Telegram, ejecución cada 15–30 min, sin duplicados.
- Fuente de alertas por correo si Wallapop/Vinted las envían.
- **Listo cuando**: llevas 2 semanas recibiendo alertas y al menos la mitad te parecen
  compras razonables (precisión ≥ 50 %).

### Fase D — Operar y medir (4–6 semanas)
- Comprar solo lo que la app marque y pasar la verificación física.
- Libro de operaciones y dashboard.
- **Puerta de decisión** (como un sistema de trading): margen neto real medio ≥ 25 %,
  error de valoración ≤ ±15 %, beneficio por hora > 15 €/h. Si no se cumple, se ajusta el
  catálogo o se para.

### Fase E — Ampliar fuentes (solo si D sale bien)
- Aquí se decide Wallapop: pedir permiso, usar Ruit u otra herramienta, o asumir el riesgo
  con una fuente de terceros. Decisión explícita y anotada.
- Más categorías, valoración con el histórico propio, rebaja automática de precios de venta.

---

## 4. Costes aproximados (a confirmar)

| Concepto | Coste |
| --- | --- |
| eBay Browse API | Gratis con cuenta de desarrollador (con límites de llamadas) |
| Claude Haiku para normalizar | Bajo: se llama solo para anuncios del catálogo que las reglas no resuelven |
| Keepa | Suscripción mensual (consultar tarifa vigente) |
| VPS | Unos pocos euros al mes, o el propio ordenador al principio |
| Telegram | Gratis |

## 5. Riesgos técnicos

- **Emparejar mal el modelo** (p. ej. "PS5 Digital" frente a "PS5 con lector"): margen
  falso. Por eso el catálogo cerrado y la revisión de muestras.
- **Precio de usado desactualizado**: recalcular la mediana cada semana.
- **Anuncios gancho / estafas**: precios demasiado buenos son señal de alarma, no de chollo.
- **Velocidad**: en lo muy líquido (iPhone, PS5) gana el que llega antes; los nichos
  (objetivos, cámaras concretas) aguantan más tiempo publicados y encajan mejor con 15–30 min.

## 6. Pendiente de confirmar

- Texto vigente de las condiciones de Wallapop (abrir la página directamente).
- Si Wallapop/Vinted envían las alertas de búsquedas guardadas por correo.
- Tarifa vigente de Keepa y límites de la eBay Browse API.
- Cómo obtiene Ruit los datos y si permite exportarlos.

## Fuentes

- Condiciones de Wallapop: [about.wallapop.com](https://about.wallapop.com/condiciones-de-uso/), [Octoparse](https://www.octoparse.es/blog/wallapop-api-que-existe-y-como-obtener-datos), [MovilZona](https://www.movilzona.es/noticias/aplicaciones/wallapop-motivos-baneo/)
- Scrapers de terceros: [Apify](https://apify.com/rastriq/wallapop-scraper), [ScrapeUnblocker](https://www.scrapeunblocker.com/scrapers/wallapop/)
- Precio nuevo: [Keepa API (Python)](https://keepaapi.readthedocs.io/en/stable/product_query.html), [Idealo vía Apify](https://apify.com/s-r/idealo-scraper)
- eBay: [Marketplace Insights](https://developer.ebay.com/api-docs/buy/marketplace-insights/resources/item_sales/methods/search)
