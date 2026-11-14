"""Candidato 4 v4 (PREREGISTRO_V4_R3.md): corto de los dos ETF 3x de cada par, reajuste mensual."""
import numpy as np, pandas as pd
D = "metodo/v4/datos/"
t = lambda x: x.mean() / x.std() * np.sqrt(len(x))
PARES = [("TQQQ", "SQQQ"), ("UPRO", "SPXU"), ("SPXL", "SPXS"), ("UDOW", "SDOW"), ("TNA", "TZA"), ("SOXL", "SOXS"),
         ("FAS", "FAZ"), ("TECL", "TECS"), ("LABU", "LABD"), ("ERX", "ERY"), ("NUGT", "DUST"), ("YINN", "YANG")]
AMPLIOS = PARES[:5]
def px(s):
    d = pd.read_csv(D + f"{s}.csv", index_col=0, parse_dates=True)
    p = pd.to_numeric(d["Adj Close"], errors="coerce"); return p[p > 0].dropna()
def par(a, b, frec="MS", lado="ambos", com=0.0005, prest=0.04):
    pa, pb = px(a), px(b); idx = pa.index.intersection(pb.index); idx = idx[idx >= "2012-01-01"]
    pa, pb = pa[idx], pb[idx]
    grupo = idx.to_period("M" if frec == "MS" else "W")
    out = []
    for _, g in pd.Series(idx, idx).groupby(grupo):
        d0 = g.index[0]; i0 = idx.get_loc(d0)
        if i0 == 0: continue
        prev = idx[i0 - 1]                                   # se abre al cierre del día anterior al 1er día del periodo
        dias = g.index
        va = pa[dias] / pa[prev]; vb = pb[dias] / pb[prev]   # valor relativo de cada corto (1 = sin cambio)
        wa, wb = {"ambos": (0.5, 0.5), "alcista": (1, 0), "bajista": (0, 1)}[lado]
        valor = 1 - wa * (va - 1) - wb * (vb - 1)            # capital del par
        v = pd.concat([pd.Series([1.0], [prev]), valor])
        r = v.pct_change().dropna()
        r.iloc[0] -= 2 * com * (wa + wb)                     # abrir y cerrar (cierre cargado al empezar, mismo total)
        r -= (wa * va.shift(1).fillna(1) + wb * vb.shift(1).fillna(1)).values * prest / 252
        out.append(r)
    return pd.concat(out)
def cartera(pares, **kw):
    return pd.concat({a: par(a, b, **kw) for a, b in pares}, axis=1).mean(axis=1)
def informe(nom, r):
    mitad = r.index[len(r) // 2]; vol = r.std() * np.sqrt(252); esc = 0.15 / vol
    eq = (r * esc).cumsum(); dd = (eq.cummax() - eq).max(); an = r.mean() * 252 * esc
    print(f"{nom:34s} anual {r.mean()*252:+.1%} vol {vol:.1%} Sharpe {r.mean()/r.std()*np.sqrt(252):.2f} t {t(r):.2f} | 1ª {r[:mitad].mean()*252:+.1%} 2ª {r[mitad:].mean()*252:+.1%} | vol15: DD {dd:.0%} DD/anual {dd/an if an>0 else np.inf:.1f}")
r1 = cartera(PARES); informe("V1 todos, mensual", r1)
informe("V1 costes ×2 (préstamo 8 %)", cartera(PARES, com=0.001, prest=0.08))
informe("V2 índices amplios", cartera(AMPLIOS))
informe("   resto (sectoriales)", cartera(PARES[5:]))
informe("V3 semanal", cartera(PARES, frec="W"))
informe("control: solo corto del alcista", cartera(PARES, lado="alcista"))
informe("control: solo corto del bajista", cartera(PARES, lado="bajista"))
print("por par V1 (anual %, t):", {a: (round(par(a, b).mean()*252*100, 1), round(t(par(a, b)), 2)) for a, b in PARES})
print("por año V1 %:", (r1.groupby(r1.index.year).mean() * 252 * 100).round(1).to_dict())
print("peor día", round(r1.min(), 4), r1.idxmin().date(), "| peor mes", round(r1.resample("ME").sum().min(), 4), r1.resample("ME").sum().idxmin().date())
for a, b in (("2020-02-15", "2020-04-30"), ("2022-01-01", "2022-12-31"), ("2025-03-25", "2025-04-30")):
    print(f"  {a}→{b}: {r1[a:b].sum():+.1%}")
r1.rename("r").to_frame().to_csv("metodo/v4/letf_v1_diaria.csv")
