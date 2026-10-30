# EV por cuota FTMO (simulador cartera/equilibrio.py de Jorge) para: ORB solo, NNFX D1 walk-forward solo, y los dos juntos.
import numpy as np, pandas as pd
src = open("/mnt/user-data/uploads/Prop Firm Challenges/cartera/equilibrio.py").read().split('if __name__=="__main__":')[0]
src = src.replace('r=pd.read_csv("../walkforward/orb_R_2018_2026.csv",index_col=0,parse_dates=True).iloc[:,0]', "r=SERIE")
src = src.replace("pnl=np.maximum(pnl,-1.5*risk)", "pnl=np.maximum(pnl,-CLIP*risk)").replace("HC=0.05", "HC=0.0")
orb = pd.read_csv("/mnt/user-data/uploads/Prop Firm Challenges/walkforward/orb_R_2018_2026.csv", index_col=0, parse_dates=True).iloc[:, 0] - 0.05
t = pd.read_csv("nnfx_wf_trades.csv", parse_dates=["d"])
nn1 = t.groupby("d").R.sum(); nn2 = t.groupby("d").R2.sum()
a, b = max(orb.index.min(), nn1.index.min()), min(orb.index.max(), nn1.index.max())
def cut(s): return s[(s.index >= a) & (s.index <= b)]
both = cut(orb).add(cut(nn1), fill_value=0)
both2 = cut(orb).add(cut(nn2), fill_value=0)
series = {"ORB US100 solo": (cut(orb), 1.5), "NNFX D1 solo (coste 1x)": (cut(nn1), 99), "NNFX D1 solo (coste 2x, edge ~0)": (cut(nn2), 99),
          "ORB + NNFX (coste 1x)": (both, 99), "ORB + NNFX (coste 2x)": (both2, 99)}
print(f"periodo {a.date()} - {b.date()} | NNFX {len(t)} ops, {t.R.mean():+.3f} R (1x), {t.R2.mean():+.3f} R (2x)")
for nm, (s, clip) in series.items():
    g = {"SERIE": s, "CLIP": clip}; exec(src, g)
    best = {}
    for prod in (1, 2):
        for size in (10, 25, 50, 100, 200):
            for rc in (0.5, 0.75, 1.0, 1.5):
                for rf in (0.5, 0.75, 1.0, 1.5):
                    r = g["sim"](prod, size, rc, rf, 632, N=4000)
                    if r["mean"] > best.get(prod, {"mean": -1e9})["mean"]: best[prod] = r
    for prod, r in best.items():
        print(f"{nm:34s} {'1-Step' if prod==1 else '2-Step'} {r['size']:>3}K reto {r['rc']}% fond {r['rf']}% | neto medio {r['mean']:+7.0f} € mediana {r['med']:+6.0f} | P(neto>0) {r['ppos']:.0f}% | P(pasar) {r['pass1']:.0f}%", flush=True)
