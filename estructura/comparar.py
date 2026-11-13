import numpy as np, pandas as pd, sys
sys.path.insert(0, "estructura"); import sim_estructura as s
R = pd.read_csv("/mnt/project-files/cuentas-3000/serie_v018_be.csv").R.values
def emp(rng, n, f, objetivo, serie, max_dias=500):
    eq = np.zeros(n); vivo = np.ones(n, bool); ok = np.zeros(n, bool)
    for _ in range(max_dias):
        act = vivo & ~ok
        if not act.any(): break
        d = rng.choice(serie, n) * f
        eq = np.where(act, eq + d, eq)
        vivo &= ~(act & ((eq <= -0.10) | (d <= -0.05)))
        ok |= act & vivo & (eq >= objetivo)
    return ok
def emp_f(rng, n, f, serie, cap=100_000, cuota=540, periodos=24):
    eq = np.zeros(n); vivo = np.ones(n, bool); cobro = np.zeros(n); dev = np.zeros(n, bool)
    for _ in range(periodos):
        for _ in range(10):
            d = rng.choice(serie, n) * f
            eq = np.where(vivo, eq + d, eq); vivo &= (eq > -0.10) & ~(d <= -0.05)
        pag = vivo & (eq > 0); cobro += np.where(pag, eq * cap * 0.8 + np.where(dev, 0, cuota), 0); dev |= pag; eq = np.where(pag, 0, eq)
    return cobro
if __name__ == "__main__":
  rng = np.random.default_rng(0); n = 100_000
  for nom, serie in (("ORB v018", R), ("ORB v018 con media 0", R - R.mean())):
      a = emp(rng, n, 0.02, 0.10, serie); b = a & emp(rng, n, 0.02, 0.05, serie)
      c = np.where(b, emp_f(rng, n, 0.015, serie), 0)
      print(f"{nom:25s} pasa {b.mean():.3f} EV/cuota {c.mean()-540:7.0f}")
  for c in (0.0, 0.01, 0.03, 0.05):
      r = s.ev((0.045, 1), (0.045, 1), (0.045, 1), c, n=60_000)
      print(f"sin ventaja audaz 4,5 %, coste {c:.2f} R: pasa {r['p_pasar']:.3f} EV {r['ev']:6.0f}")
