"""P4 del PREREGISTRO_P4_Y_BUND.md, parte A: la pata ZN de fin de mes en el DARWIN de Darwinex Zero.
Uso (desde la raíz de yes-lab): python darwinex/bonos_fin_de_mes/p4_darwin.py datos_bonos"""
import sys, os, io, contextlib, numpy as np, pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.argv = [sys.argv[0], sys.argv[1] if len(sys.argv) > 1 else "datos_bonos"]
A = {"__file__": os.path.join(AQUI, "auditoria.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(AQUI, "auditoria.py")).read(), A)
W = A["ventanas"](A["zl"])                                    # ZN limpio, pb por mes y posición
COSTE = 3.0
fin = (W[-1] - COSTE) / 1e4; plac = (W[12] - COSTE) / 1e4     # retorno neto (fracción) por mes
fin.index = fin.index.to_period("M").to_timestamp("M"); plac.index = plac.index.to_period("M").to_timestamp("M")

b = pd.read_csv(os.path.join(RAIZ, "reversion_dz", "mensual_orb_reversion.csv"), index_col=0, parse_dates=True)
b.index = b.index.to_period("M").to_timestamp("M")
b = b["2018-01":"2026-10"]
zn = fin.reindex(b.index).fillna(0.0); zp = plac.reindex(b.index).fillna(0.0)


def sr(m): m = pd.Series(m); return m.mean() / m.std() * np.sqrt(12)
def dd(m): c = pd.Series(m).cumsum(); return (c.cummax() - c).max()
def v6(m): return (pd.Series(m).rolling(6).sum() > 0).mean() * 100


def mezcla(base, pata, ratio=0.5):
    w = ratio * base.std() / pata.std()
    mix = base + w * pata
    return w, mix * base.std() / mix.std()


def fila(nom, x):
    print(f"  {nom:46s} SR {sr(x):5.2f}  peor DD {dd(x):5.1f} R  6 m positivas {v6(x):5.1f} %  peor mes {x.min():5.1f} R")


print("PATA ZN SOLA en la ventana 2018-01 → 2026-10 (neta, meses sin operación = 0)")
print(f"  meses con operación {int((zn != 0).sum())}; media {zn[zn != 0].mean() * 1e4:5.1f} pb; SR anual {sr(zn):4.2f}; "
      f"t {sr(zn) * np.sqrt(len(zn) / 12):4.2f}")
print("\n1) Correlaciones mensuales")
c_orb, c_rev, c_base = zn.corr(b.orb), zn.corr(b.rev), zn.corr(b.mezcla)
print(f"  con ORB {c_orb:+.3f} | con reversión {c_rev:+.3f} | con la base ORB+reversión {c_base:+.3f}")

print("\n2-4) DARWIN (en R del ORB, mezcla reescalada a la vol de la base)")
w, mix = mezcla(b.mezcla, zn)
zh = zn.where(zn == 0, zn - zn[zn != 0].mean() * 0.5)
_, mixh = mezcla(b.mezcla, zh)
_, mixp = mezcla(b.mezcla, zp)
fila("base ORB + reversión", b.mezcla); fila("base + ZN fin de mes (peso 0,5)", mix)
fila("base + ZN con ventaja a la mitad", mixh); fila("placebo: base + ZN ventana sesión 12", mixp)
for r in (0.25, 0.75, 1.0):
    _, m = mezcla(b.mezcla, zn, r); fila(f"   (informativo) peso {r}", m)
fila("(informativo) ORB solo", b.orb)
_, mo = mezcla(b.orb, zn); fila("(informativo) ORB + ZN, sin reversión", mo)
d_real = sr(mix) - sr(b.mezcla)

print("\n5) Bootstrap por bloques de 3 meses (10.000)")
bb, zz = b.mezcla.values, zn.values; L = len(bb); rng = np.random.default_rng(1); ds = []
for _ in range(10000):
    st = rng.integers(0, L - 3, L // 3 + 1); ix = np.concatenate([np.arange(a, a + 3) for a in st])[:L]
    ds.append(sr(bb[ix] + w * zz[ix]) - sr(bb[ix]))
ds = np.array(ds)
print(f"  ΔSharpe real {d_real:+.3f}; bootstrap mediana {np.median(ds):+.3f}, p10 {np.percentile(ds, 10):+.3f}, "
      f"P(Δ>0) {(ds > 0).mean() * 100:.1f} %")

print("\n6) Monte Carlo 36 meses (dz_sim_base.py, cuenta de futuros 50 €/mes)")
src = open(os.path.join(RAIZ, "reversion_dz", "dz_sim_base.py")).read().split("filas=[]")[0] \
    .replace("../dos-orb/serie_v018_be.csv", os.path.join(RAIZ, "reversion_dz", "serie_v018_be.csv"))
B = {}; exec(src, B)
mc = {}
for nom, mm in [("base ORB + reversión", b.mezcla), ("base + ZN", mix), ("base + ZN ventaja a la mitad", mixh)]:
    for perm in (None, "obj10"):
        out, al, rd = B["sim"](mm.values, esc=0.45, perm=perm, cuota=50.0)
        mc[(nom, perm)] = out.mean() / 3
        print(f"  {nom:32s} perm {perm or 'no':5s} DARWIN/año {np.median(rd) * 100:5.1f} %  asign. {al.mean():4.1f}  "
              f"neto €/año {out.mean() / 3:6.0f}  mediana 36 m {np.median(out):6.0f}  P(neg) {(out < 0).mean() * 100:4.1f} %")

print("\nCRITERIOS")
crit = [("1 |corr| ORB y reversión ≤ 0,20", max(abs(c_orb), abs(c_rev)) <= 0.20),
        ("2 ΔSharpe ≥ +0,10 y peor DD no peor", d_real >= 0.10 and dd(mix) <= dd(b.mezcla)),
        ("3 ventaja a la mitad > base", sr(mixh) > sr(b.mezcla)),
        ("4 placebo sesión 12 no iguala", sr(mixp) - sr(b.mezcla) < d_real),
        ("5 bootstrap P(Δ>0) ≥ 80 %", (ds > 0).mean() >= 0.80),
        ("6 MC €/año > base (sin permanente)", mc[("base + ZN", None)] > mc[("base ORB + reversión", None)])]
for n, ok in crit: print(f"  {n:40s} {'PASA' if ok else 'FALLA'}")
print("P4 A:", "PASA" if all(ok for _, ok in crit) else "FALLA")

print("\nTamaño en la cuenta de futuros (1 M$)")
vol_base_pct = b.mezcla.std() * 0.45                          # 1 R = 0,45 % del DARWIN (dz_sim_base)
vol_pata_pct = w * zn.std() * b.mezcla.std() / (b.mezcla + w * zn).std() * 0.45
nom_zn = 1000 * A["z"].iloc[-1]
frac = vol_pata_pct / (zn.std() * 100)                        # fracción del capital en ZN
print(f"  vol mensual DARWIN {vol_base_pct:.2f} %; la pata usa {frac * 100:.0f} % del capital en nominal ZN "
      f"= {frac * 1e6 / nom_zn:.1f} contratos de {nom_zn:,.0f} $")
