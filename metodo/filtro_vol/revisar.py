"""Revisión del filtro de volatilidad p90 del ORB US100 (PREREGISTRO.md). Uso: python -m metodo.filtro_vol.revisar"""
import glob
from pathlib import Path

import numpy as np
import pandas as pd

from metodo.embudo import t_agrupado

D = Path(__file__).resolve().parents[1] / "v14" / "base"
df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(D / "US100_*.csv")))])
df["fecha"] = pd.to_datetime(df.fecha)
df = df.drop_duplicates("fecha").sort_values("fecha").reset_index(drop=True)

# percentil del ATR% de ayer frente a los 252 días previos (atr de la fila = ATR hasta ayer)
x = (df.atr / df.px).to_numpy()
pct = np.full(len(x), np.nan)
for i in range(len(x)):
    prev = x[max(0, i - 252):i]
    prev = prev[np.isfinite(prev)]
    if len(prev) >= 120 and np.isfinite(x[i]):
        pct[i] = 100.0 * (prev < x[i]).mean()
df["pct"] = pct
df = df[df.pct.notna()].reset_index(drop=True)
df["bloq"] = df.pct > 90
df["senal"] = df.lado.notna() & df.r.notna()
df["coste"] = 0.00007 * df.px / (0.15 * df.atr)
df["n"] = np.where(df.senal, df.r - df.coste, 0.0)

# episodios de días bloqueados seguidos (días hábiles)
ep = (df.bloq != df.bloq.shift()).cumsum()
df["largo_ep"] = df.groupby(ep).bloq.transform("size").where(df.bloq, 0)

PER = {"2012-17": ("2012-01-01", "2017-12-31"), "2018-26": ("2018-01-01", "2026-12-31"),
       "2012-26": ("2012-01-01", "2026-12-31")}


def tsem(s):
    return t_agrupado(s.n.to_numpy(), s.fecha.dt.to_period("W").astype(str).to_numpy())


def dd(r):
    c = np.cumsum(r)
    return float(np.max(np.maximum.accumulate(np.r_[0, c])[1:] - c)) if len(c) else 0.0


def met(r, anios):
    sh = r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0
    return r.sum() / anios, sh, dd(r)


print(f"Días con percentil: {len(df)} ({df.fecha.min():%Y-%m-%d} → {df.fecha.max():%Y-%m-%d}); "
      f"bloqueados {df.bloq.mean():.1%}; coste medio {df[df.senal].coste.mean():.3f} R")
rng = np.random.default_rng(0)
for nom, (a, b) in PER.items():
    s = df[(df.fecha >= a) & (df.fecha <= b)].reset_index(drop=True)
    anios = (s.fecha.max() - s.fecha.min()).days / 365.25
    op = s[s.senal]
    bl, li = op[op.bloq], op[~op.bloq]
    lg = op[op.largo_ep >= 10]
    print(f"\n=== {nom} ({anios:.1f} años, {len(op)} ops)")
    print(f"F1 bloqueados: {len(bl)} ops, bruto {bl.r.mean():+.3f}, neto {bl.n.mean():+.3f} R (t sem {tsem(bl):+.2f}) "
          f"| permitidos {len(li)}, neto {li.n.mean():+.3f} (t sem {tsem(li):+.2f})")
    print(f"F3 pausas ≥10 días: {len(lg)} ops en {int(((s.largo_ep >= 10) & ~(s.largo_ep >= 10).shift(fill_value=False)).sum())} episodios, "
          f"neto {lg.n.mean() if len(lg) else float('nan'):+.3f} (t sem {tsem(lg) if len(lg) > 1 else 0:+.2f})")
    base = s.n.to_numpy()
    filt = np.where(s.bloq, 0.0, base)
    mb, mf = met(base, anios), met(filt, anios)
    print(f"F2 sin filtro: {mb[0]:.1f} R/año, Sharpe {mb[1]:.2f}, DD {mb[2]:.1f} R | con p90: {mf[0]:.1f} R/año, "
          f"Sharpe {mf[1]:.2f}, DD {mf[2]:.1f} R")
    # placebo: desplazamiento circular de la máscara real (mismos racimos, otros días)
    m = s.bloq.to_numpy()
    shifts = rng.choice(np.arange(20, len(s) - 20), size=min(5000, len(s) - 40), replace=False)
    pl = np.array([met(np.where(np.roll(m, k), 0.0, base), anios) for k in shifts])
    dr, dsh, ddd = mf[0] - mb[0], mf[1] - mb[1], mf[2] - mb[2]
    print(f"   mejora real: R/año {dr:+.1f}, Sharpe {dsh:+.2f}, DD {ddd:+.1f} | placebo p95: "
          f"R/año {np.percentile(pl[:, 0] - mb[0], 95):+.1f}, Sharpe {np.percentile(pl[:, 1] - mb[1], 95):+.2f}, "
          f"DD (p5) {np.percentile(pl[:, 2] - mb[2], 5):+.1f} | p-valor Sharpe {np.mean(pl[:, 1] - mb[1] >= dsh):.3f}")
    print("   por año (neto bloqueados, n):", ", ".join(
        f"{y}: {g.n.mean():+.2f} ({len(g)})" for y, g in bl.groupby(bl.fecha.dt.year)))
