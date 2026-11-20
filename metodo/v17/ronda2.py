"""v17 ronda 2: calibración del encogimiento (Chen-Dim / Harvey-Liu) en la cohorte real.

¿Cuánto del t de ajuste sobrevive fuera, según lo alto que sea? ¿Cuánto descuenta el recorte del embudo
(t_req − 1,64 errores estándar) y cuánto haría falta? EB jerárquico: varianza de la t verdadera entre familias
y dentro de familia.
"""
import sys
from pathlib import Path
from statistics import NormalDist
import numpy as np, pandas as pd

AQUI = Path(__file__).parent
for arch, corte in (("cohorte.csv.gz", 2015), ("cohorte_2011.csv.gz", 2011)):
    d = pd.read_csv(AQUI / arch)
    for y in ("tx", "t"):
        x = d.dropna(subset=[f"{y}_IS", f"{y}_OOS"]).copy()
        # t fuera reescalado a la longitud del ajuste (t crece con sqrt(n))
        esc = np.sqrt((x.n_IS.clip(lower=1) * 0 + (corte - 2001)) / (2026.9 - corte))
        x["oos_eq"] = x[f"{y}_OOS"] * esc
        x["bin"] = pd.cut(x[f"{y}_IS"], [-9, -3, -2, -1, 0, 1, 2, 2.5, 3, 9])
        print(f"\n=== {arch} (fuera desde {corte}), objetivo {y}: t fuera reescalado a la duración del ajuste ===")
        tab = x.groupby("bin", observed=True).agg(n=("oos_eq", "size"), t_is=(f"{y}_IS", "mean"),
                                                   t_oos=("oos_eq", "mean"), p_pos=("oos_eq", lambda v: (v > 0).mean()))
        tab["retiene"] = tab.t_oos / tab.t_is
        print(tab.round(2).to_string())
        # EB: varianza entre familias×clase×lado y dentro
        g = x.groupby(["clase", "familia", "lado"])[f"{y}_IS"]
        m = g.transform("mean")
        v_dentro, v_entre = (x[f"{y}_IS"] - m).var(), m.var()
        print(f"var t_IS total {x[f'{y}_IS'].var():.2f} = entre grupos {v_entre:.2f} + dentro {v_dentro:.2f} "
              f"(ruido puro dentro ≈ 1; con variantes correlacionadas, menos)")
        # recorte del embudo para el top: t_req(n) - 1.64 en unidades de t
        top = x[x[f"{y}_IS"] >= 3]
        for n in (10, 100, 1000, len(x)):
            rec = NormalDist().inv_cdf(1 - 0.05 / n) - 1.645
            print(f"  recorte del embudo con n_pruebas={n:5d}: t {top[f'{y}_IS'].mean():.2f} → {top[f'{y}_IS'].mean() - rec:.2f}"
                  f" | real fuera {top.oos_eq.mean():.2f} (n {len(top)})")
