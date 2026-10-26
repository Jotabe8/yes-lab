# Variante largo/corto: +1 sobre la media de 200, −1 debajo. El corto cobra (tipo − 2,5 %) y paga dividendos.
exec(open("ev_prima.py").read().split("for div in (False, True):")[0])
def market_ls(n, markup, div):
    d = pd.read_csv(M + f"indices/{n}.csv", parse_dates=["Date"]).set_index("Date")
    c = d.Close.astype(float).dropna(); c = c[c > 0]; r = c.pct_change()
    rate = RATE[IDX[n]].reindex(RATE[IDX[n]].index.union(c.index)).ffill().reindex(c.index) / 100
    days = c.index.to_series().diff().dt.days.fillna(1)
    side = np.where(c > c.rolling(200).mean(), 1.0, -1.0); side = pd.Series(side, c.index)
    vol = r.rolling(20).std() * np.sqrt(252); w = ((0.10 / vol).clip(upper=2.0) * side).shift(1)
    fin = np.where(w > 0, (rate + markup), -(rate - markup)) / 360 * days          # coste por unidad de |w|
    dv = DIV[n] / 252 if div else 0
    pnl = w * r - w.abs() * fin + w * dv - w.diff().abs() * 0.0002
    return pnl.dropna()
for div in (False, True):
    s = pd.concat({n: market_ls(n, 0.025, div) for n in IDX}, axis=1, sort=True).mean(axis=1)
    print(f"--- largo/corto {'con' if div else 'sin'} div: 1990-2007 {stats(s,'1990','2007-12-31')} | 2008-2026 {stats(s,'2008','2026-12-31')}")
    s = s[(s.index >= a) & (s.index <= b)] * 100
    for days in (252, 756):
        for prod, r in best(s, 99, days).items():
            print(f"  {days//252} año(s) {'1-Step' if prod==1 else '2-Step'} {r['size']:>3}K reto {r['rc']} fond {r['rf']} | neto medio {r['mean']:+7.0f} € | P(neto>0) {r['ppos']:.0f}% | P(pasar) {r['pass1']:.0f}%", flush=True)
    for rc in (1.0,):
        g = {"SERIE": s, "CLIP": 99}; exec(src, g)
        for prod, size in ((2, 200), (1, 200)):
            r = g["sim"](prod, size, rc, rc, 632, N=3000, days=756)
            print(f"  riesgo moderado 1.0 (vol ~7 %) 3 años {'1-Step' if prod==1 else '2-Step'} {size}K | neto medio {r['mean']:+7.0f} € | P(pasar) {r['pass1']:.0f}%")
