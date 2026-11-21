"""Parte B del PREREGISTRO_P4_Y_BUND.md: réplica de las compras de fin de mes en el Bund a 10 años.
Uso (desde la raíz de yes-lab): python darwinex/bonos_fin_de_mes/bund.py datos_bonos datos_bund"""
import sys, os, io, contextlib, numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
DB = sys.argv[2] if len(sys.argv) > 2 else "datos_bund"
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "datos_bonos"]
A = {"__file__": os.path.join(AQUI, "auditoria.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(AQUI, "auditoria.py")).read(), A)
ventanas, par, t, linea = A["ventanas"], A["par"], A["t"], A["linea"]

d = pd.read_csv(os.path.join(DB, "bbsis_zar_10y.csv"), skiprows=8, header=None, usecols=[0, 1], names=["d", "v"])
y = pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d, errors="coerce")).dropna()
y = y[y.index.dayofweek < 5]
print(f"Bund 10 a (Bundesbank, par): {y.index[0].date()} → {y.index[-1].date()}, {len(y)} sesiones")
r = pd.Series(par(y.shift(1).values, y.values), y.index).dropna()
W = ventanas(r); w = W[-1]

print("\nB) RÉPLICA (bruto/neto en pb, coste 3 pb)")
linea("Bund 1998-2026 (principal)", w["1998":"2026-10"])
linea("Bund 2019-2026", w["2019":"2026-10"])
linea("   placebo sesión 12", W[12]["1998":"2026-10"])
m = W["1998":"2026-10"].mean(); otras = m.drop([-1, -2, -3])
pct = (otras < m[-1]).mean() * 100
print(f"   placebo completo: fin de mes {m[-1]:5.1f} | resto media {otras.mean():5.1f} máx {otras.max():5.1f} "
      f"(pos {otras.idxmax()}) | percentil {pct:.0f}")
print("     ", " ".join(f"{k}:{v:.1f}" for k, v in m.items()))
x = w["1998":"2026-10"] - 3; h = len(x) // 2
print("   neto por año:", {k: round(v) for k, v in x.groupby(x.index.year).sum().items()})

zn = pd.read_csv(os.path.join(AQUI, "ventanas_zn.csv"), index_col=0, parse_dates=True)["zn_limpio_pb"]
zn.index = zn.index.to_period("M"); wb = w.copy(); wb.index = wb.index.to_period("M")
j = pd.concat([zn, wb], axis=1, keys=["zn", "bund"]).dropna()["2001":"2026-10"]
c = j.zn.corr(j.bund)
comb = (j.zn / j.zn.std() + j.bund / j.bund.std()) / 2 * j.zn.std()
cz = j.zn - 3; cc = comb - 3 * (1 + j.zn.std() / j.bund.std()) / 2   # coste de las dos patas a igual riesgo
print(f"\nVALOR PROPIO (2001-2026, {len(j)} meses): corr mensual ZN-Bund {c:+.3f}; "
      f"t ZN solo {t(cz):4.2f} | t ZN + Bund a igual riesgo {t(cc):4.2f}")

crit = [("t neto 1998-2026 ≥ 2,0", t(x) >= 2.0), ("2.ª mitad > 0", x.iloc[h:].mean() > 0),
        ("placebo completo percentil ≥ 95", pct >= 95), ("2019-2026 neto > 0", (w["2019":"2026-10"] - 3).mean() > 0)]
print("\nCRITERIOS RÉPLICA")
for n, ok in crit: print(f"  {n:36s} {'PASA' if ok else 'FALLA'}")
print("Réplica Bund:", "PASA" if all(ok for _, ok in crit) else "FALLA")
print("Valor propio:", "PASA" if (c <= 0.6 and t(cc) > t(cz)) else "FALLA")

print("\nINFORMATIVO: CFD del Bund de Dukascopy (bid D1, 2016-2026, saltos de vencimiento sustituidos)")
k = pd.read_csv(os.path.join(DB, "bundtreur-d1-bid-2016-05-02-2026-11-18.csv"))
k.index = pd.DatetimeIndex(pd.to_datetime(k.timestamp, unit="ms")).normalize(); k = k[k.index.dayofweek < 5]
kr = k.close.pct_change().dropna(); ref = r.reindex(kr.index)
dif = kr - ref; sd = dif.rolling(250, min_periods=60).std().shift(1)
salto = (dif.abs() > 4 * sd) & ref.notna()
kl = kr.where(~salto, ref).dropna()
print(f"  saltos sustituidos {int(salto.sum())}; correlación diaria con Bundesbank {kr.corr(ref):.2f}")
wk = ventanas(kl)[-1]
linea("CFD Bund 2016-2026", wk["2016-06":"2026-10"])
linea("Bundesbank mismo tramo", w["2016-06":"2026-10"])
