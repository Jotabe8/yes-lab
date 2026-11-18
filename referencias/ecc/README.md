# ECC (affaan-m) – qué sirve para trading y catálogo para futuros proyectos

Revisado el 18/11/2026. Repo de origen: <https://github.com/affaan-m/ECC> (antes "everything-claude-code"), versión 2.2.3, commit `3f14a10`, licencia MIT (copia en `LICENSE`). Tiene 327 skills, 72 agentes y 98 comandos.

Esta carpeta es **solo de referencia**. Las skills copiadas no están en `.claude/skills`, así que Claude no las carga automáticamente. Están en inglés y sin adaptar a MQL5.

## Contenido de esta carpeta

| Ruta | Origen |
| --- | --- |
| `skills/loop-design-check/` | `skills/loop-design-check` de ECC |
| `skills/benchmark-optimization-loop/` | `skills/benchmark-optimization-loop` de ECC (con `references/`) |
| `skills/recursive-decision-ledger/` | `skills/recursive-decision-ledger` de ECC |
| `skills/council/` | `skills/council` de ECC |
| `skills/santa-method/` | `skills/santa-method` de ECC |
| `skills/cpp-coding-standards/` | `skills/cpp-coding-standards` de ECC |
| `skills/mle-workflow/` | `skills/mle-workflow` de ECC |
| `agents/silent-failure-hunter.md` | `agents/silent-failure-hunter.md` de ECC |

## Veredicto rápido

ECC no trae nada de MQL5, MetaTrader ni backtesting de EAs. Para el trading, lo que vale es la **metodología de proceso**, no el código: hay 3 piezas que merece la pena adaptar ya y otras 5 de apoyo. Lo que suena a trading (cripto, wallets, mercados de predicción) no aplica a los EAs ORB.

No conviene instalar el plugin completo: sus hooks ejecutan comandos y consume mucho contexto. Lo recomendable es adaptar solo las piezas de prioridad Alta.

## 1. Útil para el proyecto de trading

| Pieza | Qué hace | Cómo aplicarlo a los EAs | Prioridad |
| --- | --- | --- | --- |
| `loop-design-check` | Revisa un proceso iterativo contra 5 modos de fallo. La regla central es anti-Goodhart: cada criterio de "hecho" va con su frontera (qué NO se puede hacer) y se valida por reconciliación contra una referencia externa, no por autoevaluación. | Checklist anti-sobreoptimización antes de aceptar un EA. Criterio decidible (p. ej. PF fuera de muestra ≥ X y DD ≤ Y) + fronteras (prohibido retocar parámetros tras ver el OOS). La paridad backtest–MT5 hace de "reconciliación". | Alta |
| `benchmark-optimization-loop` | Baseline congelado (datos, métrica y evaluador fijos), una hipótesis por variante y una puerta de promoción: solo se promueve si la mejora se repite o se explica, y si hay rollback claro. | Protocolo para pasar de una versión a otra (ORB v018 → v019): congelar periodo, spread y comisiones; cambiar una sola cosa por prueba; promover solo si mejora en todos los tramos. | Alta |
| `recursive-decision-ledger` | Registro append-only (JSONL + resumen en Markdown) donde cada candidato se marca accept / watch / reject / needs replay. Regla explícita: la confianza acumulada no es aprobación; por defecto, paper o demo. | Libro de decisiones de los sistemas (GER40 descartado, ORB "en juego" V2, US100…) con estado, motivo y gate siguiente. Encaja como capa de registro sobre el embudo P0–P6. | Alta |
| `council` | Cuatro voces (arquitecto, escéptico, pragmático, crítico) en subagentes sin el contexto de la conversación, para evitar el anclaje. Pensado para decisiones go/no-go. | Decisiones caras e irreversibles: comprar cuentas, meter un EA sin demo, subir el riesgo. | Media |
| `silent-failure-hunter` (agente) | Busca errores tragados, fallbacks peligrosos y logs sin contexto. | Revisión de código MQL5: `OrderSend` sin comprobar `retcode`, `GetLastError` ignorado, valores por defecto que ocultan un fallo de datos. Hay que adaptar los ejemplos, que están en TS/Python. | Media |
| `santa-method` | Dos revisores independientes con la misma rúbrica; los dos tienen que aprobar. | Validar un informe de backtest antes de comprar retos. Gasta bastantes tokens. | Media-baja |
| `cpp-coding-standards` | C++ Core Guidelines. | MQL5 tiene sintaxis tipo C++: aplican las partes de funciones, constantes y manejo de errores; el resto no. | Baja |
| `mle-workflow` | Workflow de ML en producción, con buenas secciones sobre fuga de datos futuros, splits temporales y un registro de observaciones. | Solo si algún día se mete ML en un filtro del EA (relevante para la carpeta `ml/`). | Baja (futuro) |

## 2. Suena a trading pero no sirve

- `llm-trading-agent-security`: seguridad para agentes LLM que firman transacciones con wallets cripto. Un EA no es un LLM ni tiene wallet.
- `prediction-market-oracle-research`, `prediction-market-risk-review`, `ito-baskets`: mercados de predicción y la plataforma Itô.
- `defi-amm-security`, `evm-token-decimals`, `nodejs-keccak256`, `agent-payment-x402`, `roundhouse-x402`: blockchain y DeFi.
- `latency-critical-systems`: feeds y gateways de baja latencia. Un ORB intradía no lo necesita.
- `market-research`: estudio de mercado de negocio (competidores, due diligence), no análisis de mercados financieros.

## 3. Catálogo para futuros proyectos

Agrupado por el tipo de proyecto en que podría usarse. Los nombres son los de las carpetas `skills/` o `agents/` del repo de origen; no están copiados aquí.

### Contenido, redes y vídeo (serie de animación, ingresos pasivos con IA)

- Redes: `content-engine`, `crosspost`, `social-publisher` (13 plataformas), `x-api`, `short-video-distribution` (TikTok, Shorts, Reels).
- Vídeo: `video-editing`, `remotion-video-creation`, `manim-video`, `videodb`, `ui-demo`.
- Generación con IA: `fal-ai-media` (imagen, vídeo y voz) y la familia `taste`, `taste-distillation`, `taste-application`, `tasteforge-video` (extraer un estilo visual de vídeos de referencia y aplicarlo).
- Voz de marca: `brand-voice`, `brand-discovery`, `article-writing`.

### Prospección comercial y ventas (boxeo/artes marciales, PASTORI)

- Leads y outreach: `lead-intelligence`, `social-graph-ranker`, `connections-optimizer`, `email-ops`, `investor-outreach` (sus plantillas de cold email sirven para otros fines).
- Campañas: `marketing-campaign` + agente `marketing-agent`.
- Competencia: cadena `competitive-platform-analysis` → `benchmark-methodology` → `competitive-report-structure`, además de `market-research` y `product-lens`.

### Agentes y automatización (Estación Imperial, Proyecto prueba)

- Arquitectura: `agentic-os`, `autonomous-agent-harness`, `agent-harness-construction`, `agent-architecture-audit`.
- Bucles y orquestación: `continuous-agent-loop`, `autonomous-loops`, `team-agent-orchestration`, `devfleet`, `dmux-workflows`, `gan-style-harness`, `loop-design-check`.
- Seguridad y control: `agent-security-hardening`, `operator-approval-loop`, `enterprise-agent-ops`.
- Memoria y datos: `unified-memory`, `knowledge-ops`, `data-scraper-agent`.
- Coste: `cost-aware-llm-pipeline`, `prompt-caching-strategy`.

### Apps web y producto

- Planificación: `blueprint`, `product-capability`, `orch-build-mvp`.
- Frontend: `frontend-patterns`, `react-patterns`, `nextjs-turbopack`, `vue-patterns`, `design-system`, `make-interfaces-feel-better`, `frontend-design-direction`.
- Backend: `backend-patterns`, `api-design`, `fastapi-patterns`, `postgres-patterns`.
- Despliegue y QA: `deployment-patterns`, `docker-patterns`, `e2e-testing`, `browser-qa`, `seo`.

### Python y datos (backtesting en Python, dashboards)

- `python-patterns`, `python-testing`, `tdd-workflow`, `verification-loop`.
- `dashboard-builder`, `clickhouse-io`, `data-throughput-accelerator`, `regex-vs-llm-structured-text`.
- ML: `ml-adoption-playbook`, `pytorch-patterns`, `mle-workflow`.

### Infraestructura doméstica (VPS, acceso remoto al PC de trading)

- `homelab-wireguard-vpn`: el más útil, para entrar al PC de trading desde fuera de forma segura.
- `homelab-network-setup`, `homelab-pihole-dns`, `homelab-vlan-segmentation`.

### Investigación

- `deep-research`, `exa-search`, `research-ops`, `osint-investigation`.
- `scientific-thinking-literature-review`, `scientific-db-openalex-database`: buscar papers académicos, por ejemplo sobre estrategias de ruptura de apertura.

### Negocio y documentos

- `investor-materials`, `finance-billing-ops`, `customer-billing-ops`, `master-agreement-generator`.
- `energy-procurement` está pensado para empresas e industria; poco útil para una tarifa doméstica.

### Seguridad de la propia configuración de Claude

- `security-scan` (AgentShield), `safety-guard`, `gateguard`, `mcp-dependency-review`.

### Descartable

- Sanidad: `healthcare-*`, `hipaa-compliance`.
- Logística e industria: `carrier-relationship-management`, `customs-trade-compliance`, `returns-reverse-logistics`, `inventory-demand-planning`, `production-scheduling`, `quality-nonconformance`.
- Redes empresariales: `cisco-ios-patterns`, `network-bgp-diagnostics`, `netmiko-ssh-automation` y relacionadas.
- Lenguajes y frameworks no usados: Kotlin, Swift, Rust, Go, Java/Spring/Quarkus, Perl, Laravel, Rails, Flutter, Godot, .NET.
- Localización: `bengali-nlp`, `yoruba-localization-testing`.
- Mantenimiento interno de ECC: `ecc-*`, `skill-*`, comandos `epic-*`, `hookify*`.

## 4. Siguiente paso posible

Convertir `loop-design-check`, `benchmark-optimization-loop` y `recursive-decision-ledger` en una única skill propia en español, orientada a MQL5 y prop firms, que complemente `embudo-ea-prop` y `backtest-expert`.
