"""¿Con qué horquilla real sería operable el ORB cripto en el CFD de FTMO?
neto = bruto medio - (0,065 % comisión + horquilla h) * precio / stop. Periodo 2021-03 → 2026-11 y 2024-26."""
import glob, numpy as np, pandas as pd
def t(x): return x.mean() / x.std() * np.sqrt(len(x))
for act in ("BTCUSD", "ETHUSD"):
    d = pd.concat(pd.read_csv(f) for f in sorted(glob.glob(f"metodo/v3/orb_cripto_medio/medio_{act}_*.csv")))
    d["fecha"] = pd.to_datetime(d.fecha); d = d.set_index("fecha").sort_index(); d = d[(d.index.dayofweek < 5) & (d.index >= "2021-03-01")]
    d = d.dropna(subset=["r10"]); k = d.px / (0.15 * d.atr)
    print(act, "stop medio % del precio 2024-26:", round((0.15 * d.atr / d.px)["2024":].mean() * 100, 2),
          "| nominal para arriesgar 1 %:", round(1 / ((0.15 * d.atr / d.px)["2024":].mean() * 100), 2), "x capital")
    for h in (0.0, 0.0001, 0.0002, 0.0003, 0.0005):
        x = d.r10 - (0.00065 + h) * k; y = x["2024":]
        print(f"   horquilla {h*100:.2f} %: 2021-26 {x.mean():+.3f} R (t {t(x):.2f}) | 2024-26 {y.mean():+.3f} R (t {t(y):.2f})")
