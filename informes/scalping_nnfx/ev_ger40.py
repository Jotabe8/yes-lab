# EV por cuota FTMO de GER40 retroceso EMA20 (casilla que pasó coste_bajo.py) y correlación con el ORB US100.
# Reutiliza sim() de ../entrada_aleatoria/ev_ftmo.py (reglas FTMO del 24/10/2026, presupuesto 632 EUR, 1 año).
# Uso: python3 ev_ger40.py SALIDA ORB_CSV
import sys, numpy as np, pandas as pd
OUT, ORB = sys.argv[1], sys.argv[2]
src = open(__file__.replace("scalping_nnfx/ev_ger40.py", "entrada_aleatoria/ev_ftmo.py")).read()
exec(src.split("SER = ")[0].replace("OUT = sys.argv[1]", "") + "FEE1 = {10: 79, 25: 199, 50: 319, 100: 499, 200: 999}; FEE2 = {10: 89, 25: 250, 50: 345, 100: 540, 200: 1080}\n" + src.split("FEE2 = {10: 89, 25: 250, 50: 345, 100: 540, 200: 1080}")[1].split("RISKS =")[0])
X = pd.read_csv(f"{OUT}/ger40_e1_trades.csv", parse_dates=["t"])
cal = pd.bdate_range("2018-01-01", X.t.max())
day = X.groupby(X.t.dt.normalize()).R.sum().reindex(cal, fill_value=0.0)
orb = pd.read_csv(ORB, index_col=0, parse_dates=True).iloc[:, 0].reindex(cal)
both = pd.concat([day, orb], axis=1).dropna(); both = both[(both.iloc[:, 0] != 0) & (both.iloc[:, 1] != 0)]
print("correlación diaria con el ORB US100 (días con las dos): %.3f, n=%d" % (both.corr().iloc[0, 1], len(both)))
rows = []
for per, a in [("2018-26", "2018"), ("2023-26", "2023")]:
    s = day[day.index >= a].values[None, :]
    for lab, ser in [("real", s), ("media0", s - s[s != 0].mean() * (s != 0))]:
        for prod in [2, 1]:
            for size in [10, 100]:
                best = None
                for rc in [0.5, 1.0, 1.5, 2.0]:
                    for rf in [0.5, 1.0, 1.5, 2.0]:
                        d = sim(ser, ser, prod, size, rc, rf, N=6000)
                        if best is None or d["mean"] > best["mean"]: best = dict(d, rc=rc, rf=rf)
                rows.append(dict(periodo=per, serie=lab, prod=f"{prod}-Step", size=size, **best))
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/ev_ger40.csv", index=False)
pd.set_option("display.width", 250); print(D.round(1).to_string(index=False))
