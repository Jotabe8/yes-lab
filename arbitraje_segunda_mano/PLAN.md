# Plan: sistema de arbitraje de segunda mano (España)

Fecha: 2026-11-24 · Estado: **investigación / propuesta**, nada en marcha todavía.

La idea es tratar la compraventa igual que el laboratorio trata una estrategia: buscar una
ventaja medible (precio de compra por debajo del precio de salida), descontar **todos** los
costes, validar con poco capital y solo escalar si los números aguantan.

---

## 1. Conclusiones de la investigación

| Tema | Lo que hay | Qué implica para el sistema |
| --- | --- | --- |
| **Datos de compra (Wallapop)** | No hay API pública documentada. Existen scrapers de terceros (Apify, ScrapingBee, Bright Data) que leen la búsqueda pública vía un endpoint interno, y avisan de detección de bots y bloqueos. No he podido confirmar qué dicen exactamente sus condiciones de uso sobre automatización. | El "radar" de anuncios es la parte técnicamente fácil pero **la de más riesgo de cuenta**. Leer las condiciones (`es.wallapop.com/toc`) antes de automatizar; nunca automatizar con la cuenta con la que se compra/vende. |
| **Datos de precio de salida (eBay)** | La Marketplace Insights API da ventas cerradas de 90 días, pero es de acceso restringido (hay que solicitarlo y que eBay apruebe el modelo de negocio). Terapeak (Seller Hub) tiene los datos pero sin API. | Al principio, precio de referencia **manual o semi-manual** (Terapeak, "vendidos" de eBay, tasaciones de recompra) y construir una base de datos propia de ventas reales. |
| **Precio "suelo" de liquidez** | Back Market Renove da una oferta en ~2 minutos para móviles, incluso rotos; CeX/WeBuy compra tecnología. | Útil como **stop-loss**: si lo que compras siempre se puede liquidar por X, el riesgo máximo por operación está acotado. |
| **Categorías** | Las guías de reventa coinciden en: electrónica (móviles, portátiles, tablets), cámaras y objetivos, consolas y retro, LEGO (sobre todo retirados/precintados), zapatillas. Márgenes citados por blogs: orientativos, no fiables. Advierten que envío y comisiones se comen el margen en artículos baratos. | Ticket medio alto (≥ 80–100 €) y productos **identificables por modelo/referencia** para poder automatizar la valoración. |
| **Comisiones** | Wallapop: el envío y la protección los paga normalmente el comprador; PRO es suscripción (cifras de terceros: desde ~10 €/mes hasta ~30 €, sin confirmar). Vinted Pro existe en España con obligaciones fiscales y muchas quejas de alta (NIF/VIES) en 2026. eBay cobra comisión por venta (consultar tabla vigente). | La calculadora debe tener las comisiones **por canal** como parámetros, y revisarlas cada trimestre. |
| **Hacienda (DAC7)** | Desde 2024 las plataformas informan a Hacienda de quien supere 30 ventas o 2.000 € al año. No es un impuesto nuevo, pero hace visible la actividad. | Un sistema de arbitraje supera esos umbrales enseguida. Hay que tributar el beneficio desde el día uno, y contar con que es visible. |
| **Actividad habitual** | Comprar para revender con ánimo de lucro de forma continuada es actividad económica → alta de autónomo/sociedad, IAE y IVA. Existe el **REBU**: IVA solo sobre el margen cuando compras a particulares (se declara en el 303/390; la factura debe indicarlo). | El REBU encaja casi perfecto con este negocio. Hablar con un gestor antes de la fase 3. |
| **Garantía** | Un vendedor profesional responde ante consumidores: por defecto 3 años; se puede pactar menos en segunda mano, nunca por debajo de 1 año. Entre particulares rige el Código Civil (más corto). | Coste oculto al profesionalizarse: hay que provisionar devoluciones/reparaciones (p. ej. 3–5 % de ventas) y comprar solo lo que puedas probar. |

---

## 2. Cómo funciona el sistema (arquitectura)

```
 [1 Radar]  →  [2 Valoración]  →  [3 Puntuación]  →  [4 Decisión HUMANA]  →  [5 Verificación]
  anuncios      precio salida       margen neto          comprar / negociar     IMEI, bloqueo,
  nuevos        esperado            y rotación                                  prueba física
                                                                                     ↓
              [8 Aprendizaje]  ←  [7 Contabilidad]  ←  [6 Reventa multicanal]
              recalibrar precios   libro REBU, DAC7     publicar, retirar al vender
```

1. **Radar**: búsquedas guardadas por referencia exacta (p. ej. "Sony A7 III", "iPhone 14 Pro
   128"), filtradas por precio máximo y zona. Empezar con las **alertas nativas** de las apps;
   pasar a un scraper de baja frecuencia (o un actor de Apify) solo si la fase 1 demuestra que
   llegar el primero vale dinero.
2. **Valoración**: para cada referencia, mediana de ventas reales recientes (base propia +
   eBay vendidos/Terapeak) y precio suelo de recompra (Back Market / CeX).
3. **Puntuación** (la "señal"):

   ```
   margen_neto = P_venta_esperado × (1 − comisión_canal)
               − envío − embalaje − reparación/limpieza
               − provisión_garantía − coste_riesgo (p_fraude × pérdida)
               − precio_compra
   ```

   Comprar solo si `margen_neto ≥ max(30 €, 25 % del precio de compra)` **y** la referencia
   tiene rotación < 30 días en el histórico, **y** `precio_compra ≤ precio_suelo + colchón`
   (riesgo máximo acotado).
4. **Decisión humana**: la compra, la negociación y los mensajes se quedan manuales (con
   plantillas). Automatizar mensajes es lo que más rápido banea cuentas y además es donde se
   detectan estafas.
5. **Verificación**: lista de control por categoría (IMEI y lista negra, cuenta iCloud/Google
   desvinculada, contador de disparos, piezas LEGO, número de serie). Pago siempre dentro de la
   plataforma.
6. **Reventa**: anuncio desde plantilla con fotos propias; publicar en 2–3 canales y retirar
   al vender. Precio inicial = percentil 60–70 del histórico, rebaja programada cada 7 días.
7. **Contabilidad**: cada unidad con su ID, compra, costes, venta y canal → margen por
   operación, libro REBU, control de umbrales DAC7.
8. **Aprendizaje**: comparar precio esperado frente a real y días en stock; ajustar la
   valoración por referencia. Esto es la ventaja que se acumula con el tiempo.

---

## 3. Categorías para empezar

Elegir **1–2** y ser experto en ellas:

| Prioridad | Categoría | Por qué | Cuidado con |
| --- | --- | --- | --- |
| 1 | Cámaras y objetivos (Sony, Canon, Fuji, Nikon) | Modelos claros, ticket alto, vendedores particulares que tasan mal | Hongos en lentes, contador de disparos |
| 1 | Consolas y portátiles de juego (Switch, PS5, Steam Deck) | Referencias estándar, mucha liquidez | Baneos de consola, joysticks con drift |
| 2 | iPhone / iPad | Liquidez máxima y precio suelo claro (Back Market) | Bloqueo iCloud, robados, pantallas no originales |
| 2 | LEGO retirado / precintado | Precio estable, fácil de verificar si está precintado | Capital inmovilizado mucho tiempo, cajas dañadas |
| — | Evitar al inicio: ropa barata, lujo (falsificaciones), voluminosos (envío) | | |

---

## 4. Plan por fases (con puertas de decisión)

### Fase 0 — Validación manual (4–6 semanas, 300–800 € de capital)
- Sin código. Hoja de cálculo con la fórmula de la sección 2.
- Objetivo: **10–20 operaciones** en una categoría, apuntando todo (también el tiempo invertido).
- **Puerta**: seguir solo si margen neto medio ≥ 25 %, días en stock medianos ≤ 21 y beneficio
  por hora > 15 €/h. Si no, cambiar de categoría o parar.

### Fase 1 — Base de datos y calculadora (2–4 semanas)
- Módulo Python en este repo: `arbitraje_segunda_mano/` con
  - `precios.py`: histórico de ventas por referencia (CSV/SQLite), mediana y percentiles.
  - `calculadora.py`: margen neto por canal con comisiones parametrizadas.
  - `libro.py`: inventario y operaciones (ID, compra, costes, venta, canal) → informe mensual.
  - tests con `unittest`, como el resto del laboratorio.
- **Puerta**: el error del precio esperado frente al real debe estar dentro de ±15 %.

### Fase 2 — Radar y alertas (3–4 semanas)
- Revisar condiciones de uso de cada plataforma antes de tocar nada.
- Radar de baja frecuencia sobre búsquedas concretas (o actor de Apify ~1 €/1.000 anuncios),
  puntuación automática y aviso al móvil (Telegram) solo cuando pasa los filtros.
- **Puerta**: comparar frente a la fase 0 si las alertas aumentan las operaciones buenas por
  semana. Si no aportan, no merece el riesgo de cuenta.

### Fase 3 — Profesionalizar y escalar
- Gestor: alta, IAE, **REBU**, modelo de factura, garantía (pactar 1 año por escrito).
- Cuentas PRO donde compense, segundo canal de venta (eBay / Vinted Pro / Back Market como
  salida), reinversión con límite de capital inmovilizado.
- **Reglas de riesgo** (como en trading): máximo 20 % del capital en una referencia, stock con
  más de 45 días → liquidar al precio suelo, no comprar si el colchón sobre el suelo es negativo.

---

## 5. Métricas a seguir

- Margen neto por operación (€ y %), beneficio por hora de trabajo.
- Días en stock (mediana y p90) y rotación del capital.
- Tasa de incidencias: devoluciones, fraudes, productos defectuosos.
- Error de valoración (esperado vs. real) por referencia.
- Ventas acumuladas del año frente a los umbrales DAC7.

## 6. Riesgos principales

1. **Bloqueo de cuentas** por automatizar o por actuar como profesional sin cuenta Pro.
2. **Fraude** (robados, iCloud bloqueado, falsificaciones) → verificación y pago en plataforma.
3. **Competencia**: hay muchos revendedores con alertas; la ventaja está en el nicho y en la
   rapidez de decisión, no en el scraping en sí.
4. **Costes ocultos**: tiempo, desplazamientos, garantía, stock que no rota.
5. **Fiscal**: actividad visible por DAC7; tributar desde el principio.

## 7. Pendiente de confirmar (no lo he podido verificar)

- Texto exacto de las condiciones de uso de Wallapop y Vinted sobre acceso automatizado.
- Tarifas vigentes de Wallapop PRO, Vinted Pro y eBay para profesionales en España.
- Epígrafe de IAE y si conviene autónomo o sociedad (gestor).
- Acceso a la Marketplace Insights API de eBay (solicitud a eBay).

## Fuentes

- Hacienda / DAC7: [elderecho.com](https://elderecho.com/plataformas-digitales-informaran-hacienda-ventas-superiores-2-000-euros-o-30-operaciones), [taxdown.es](https://taxdown.es/blog/dac7-hacienda-wallapop-vinted-ebay), [nota de Hacienda](https://www.hacienda.gob.es/Documentacion/Publico/GabineteMinistro/Notas%20Prensa/2024/CONSEJO-MINISTROS/30-01-24-NP-CM-RD-Reglamento-Trasposicion-DAC7.pdf)
- REBU: [manual IVA 2026 AEAT](https://sede.agenciatributaria.gob.es/Sede/ayuda/manuales-videos-folletos/manuales-practicos/manual-iva-2026/capitulo-06-regimenes-especiales-iva/reg-espec-bienes-usados-obj-coleccion/requisitos-rebu.html), [infoautonomos](https://www.infoautonomos.com/blog/autonomos-regimen-especial-bienes-usados-rebu/)
- Garantía: [Comunidad de Madrid](https://www.comunidad.madrid/consumo/productos-segunda-mano-garantias), [Ministerio de Consumo (DSCA)](https://www.dsca.gob.es/es/consumo/novedades/derechos-compra-empresas-bienes-segunda-mano-reacondicionados)
- eBay: [Marketplace Insights API](https://developer.ebay.com/api-docs/buy/marketplace-insights/resources/item_sales/methods/search), [foro sobre acceso](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Marketplace-Insights-API-access/m-p/34838736)
- Wallapop: [Wallapop PRO](https://es.wallapop.com/wallapop-pro), [Envíos](https://es.wallapop.com/envios-wallapop), [scraper Apify](https://apify.com/ahmed_jasarevic/wallapop-scraper), [ScrapingBee](https://www.scrapingbee.com/scrapers-v2/wallapop-api), [precios PRO (Subger)](https://subger.com/es/service/wallapop)
- Vinted Pro: [ayuda Vinted](https://www.vinted.com/help/3/918-vinted-pro), [Vinted ES](https://vinted.es/our-platform), [reclamaciones OCU](https://www.ocu.org/reclamar/lista-reclamaciones-publicas/problema-registro-vinted-pro/c364a5ca6cb65768d7)
- Recompra: [Back Market Renove](https://www.backmarket.es/es-es/buyback/smartphones)
- Categorías: [fitsmallbusiness](https://fitsmallbusiness.com/best-products-buy-sell-for-profit/), [salehoo](https://www.salehoo.com/items-to-flip), [linnworks](https://www.linnworks.com/blog/ebay-reselling/)
