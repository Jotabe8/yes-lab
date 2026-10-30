import numpy as np, pandas as pd, sys
sys.argv = ["x"]; exec(open("prima.py").read().split('if __name__ == "__main__":')[0])
DIV = {"SP500": 0.018, "NDX": 0.008, "DJI": 0.02, "DAX": 0.0, "FTSE": 0.035, "N225": 0.018}
def port_div(markup, div):
    out = {}
    for n in IDX:
        pnl, w = market(n, markup)
        out[n] = pnl + (w.reindex(pnl.index) * DIV[n] / 252 if div else 0)
    return pd.concat(out, axis=1, sort=True).mean(axis=1)
src = open("/mnt/user-data/uploads/Prop Firm Challenges/cartera/equilibrio.py").read().split('if __name__=="__main__":')[0]
src = src.replace('r=pd.read_csv("../walkforward/orb_R_2018_2026.csv",index_col=0,parse_dates=True).iloc[:,0]', "r=SERIE")
src = src.replace("pnl=np.maximum(pnl,-1.5*risk)", "pnl=np.maximum(pnl,-CLIP*risk)").replace("HC=0.05", "HC=0.0")
orb = pd.read_csv("/mnt/user-data/uploads/Prop Firm Challenges/walkforward/orb_R_2018_2026.csv", index_col=0, parse_dates=True).iloc[:, 0] - 0.05
a, b = orb.index.min(), orb.index.max()
def best(serie, clip, days, rcs=(0.5, 0.75, 1.0, 1.5, 2.0)):
    g = {"SERIE": serie, "CLIP": clip}; exec(src, g); out = {}
    for prod in (1, 2):
        for size in (10, 25, 50, 100, 200):
            for rc in rcs:
                for rf in rcs:
                    r = g["sim"](prod, size, rc, rf, 632, N=3000, days=days)
                    if r["mean"] > out.get(prod, {"mean": -1e9})["mean"]: out[prod] = r
    return out
for div in (False, True):
    for mk in (0.025, 0.035):
        s = port_div(mk, div); s = s[(s.index >= a) & (s.index <= b)] * 100     # % diario a vol ~7 %
        print(f"--- índices {'con' if div else 'sin'} dividendos, financ.+{mk*100:.1f}%: {stats(s/100, '2018', '2026-12-31')}")
        for days in (252, 756):
            for nm, ser, clip in (("ORB solo", orb, 1.5), ("índices solos", s, 99), ("ORB + índices x1", orb.add(s, fill_value=0), 99), ("ORB + índices x2", orb.add(2 * s, fill_value=0), 99)):
                if nm == "ORB solo" and (div or mk != 0.025): continue
                for prod, r in best(ser, clip, days).items():
                    print(f"  {days//252} año(s) {nm:18s} {'1-Step' if prod==1 else '2-Step'} {r['size']:>3}K reto {r['rc']} fond {r['rf']} | neto medio {r['mean']:+7.0f} € | P(neto>0) {r['ppos']:.0f}% | P(pasar) {r['pass1']:.0f}%", flush=True)
