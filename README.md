# Laboratorio de Trading

Laboratorio **simulado** para investigar estrategias en acciones/ETFs, cripto y forex. No opera con dinero real y nada de lo que produce es una recomendación de inversión.

## Qué hay

| Ruta | Qué hace |
| --- | --- |
| `lab/fetch.py` | Descarga cierres diarios (Yahoo Finance y Binance) a `docs/data/*.json` |
| `lab/backtest.py` | Backtester de cruce de medias y momentum con costes, métricas y walk-forward |
| `lab/nnfx.py` | Portfolio NNFX de 5 pares (largo y corto, SL/TP por ATR) con costes y walk-forward |
| `informes/nnfx-portfolio.md` | Resultados del portfolio NNFX frente a comprar y mantener |
| `docs/index.html` | Dashboard: backtester en el navegador, calculadora de posición y diario simulado |
| `.github/workflows/actualizar-datos.yml` | Actualiza los datos de lunes a viernes a las 22:15 UTC |
| `tests/` | Tests con `unittest`, sin dependencias externas |

Instrumentos: SPY, IBEX 35, Banco Santander, BTC, ETH, EUR/USD, GBP/USD, USD/JPY, NZD/USD, USD/CHF, EUR/AUD y GBP/JPY. Los pares forex guardan también apertura, máximo y mínimo.

## Uso

```bash
python -m unittest -v                          # tests
python -m lab.fetch --years 10                 # descarga datos
python -m lab.backtest spy --strategy sma --fast 50 --slow 200
python -m lab.backtest btc --strategy mom --look 126 --walk-forward
python -m lab.nnfx --walk-forward             # portfolio NNFX de 5 pares
```

El backtest imprime siempre el resultado con costes normales y con costes al doble, frente a comprar y mantener.

## Dashboard con GitHub Pages

En *Settings → Pages*, elige la rama `main` y la carpeta `/docs`. El dashboard carga los datos de `docs/data/` y, si no los encuentra, usa series sintéticas marcadas como tales.

## Reglas del backtester

- La señal del cierre del día t se opera desde el día t+1, sin mirar al futuro.
- Cada cambio de posición paga comisión más deslizamiento.
- Walk-forward: elige parámetros en 3 años y los mide en el año siguiente, avanzando año a año.
- Solo posiciones largas y sin apalancamiento (salvo `lab/nnfx.py`, que opera en ambos sentidos con riesgo fijo por operación).

## Límites de los datos

Yahoo Finance no tiene API oficial: sus términos restringen el uso a fines personales y puede fallar o cambiar sin aviso. Binance publica sus datos de mercado sin clave. Los detalles están en el informe de fuentes de datos del proyecto.
