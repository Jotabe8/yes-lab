# EV por cuota FTMO de la entrada aleatoria con gestión NNFX. Misma lógica que cartera/equilibrio.py (reglas FTMO
# verificadas el 24/10/2026, presupuesto de cuotas 632 EUR, 1 año, retiro cada 10 días hábiles, recompra al fallar),
# con dos cambios: la serie es el P&L diario de la cartera marcado al cierre (varias posiciones abiertas a la vez)
# y el límite diario y el suelo se comprueban con el peor punto intradía de cada posición (pesimista: suma los
# peores de todas aunque no coincidan en la hora). Sin el tope de -1,5R diario de equilibrio.py.
# Uso: python3 ev_ftmo.py DIR_SALIDA_ALEATORIA
import sys, numpy as np, pandas as pd
OUT = sys.argv[1]
MODO = sys.argv[2] if len(sys.argv) > 2 else "peor"   # "peor": suma de peores intradía; "cierre": solo cierre (optimista)
SER = np.load(f"{OUT}/series.npy", allow_pickle=True).item()
FEE1 = {10: 79, 25: 199, 50: 319, 100: 499, 200: 999}; FEE2 = {10: 89, 25: 250, 50: 345, 100: 540, 200: 1080}

def sim(PC, PW, prod, size, rc, rf, budget=632, N=6000, days=252, block=20, seed=1):
    rng = np.random.default_rng(seed); S, T = PC.shape
    nb = days // block + 1
    starts = rng.integers(0, T - block, (N, nb)); seeds = rng.integers(0, S, (N, nb))
    ti = (starts[:, :, None] + np.arange(block)).reshape(N, -1)[:, :days]
    si = np.repeat(seeds, block, axis=1)[:, :days]
    R = PC[si, ti].astype(float); W = PW[si, ti].astype(float)
    fee = (FEE1 if prod == 1 else FEE2)[size]; maxf = max(1, int(budget // fee))
    bal = np.zeros(N); peak = np.zeros(N); st = np.zeros(N, int)
    fees = np.ones(N); pay = np.zeros(N); best = np.zeros(N); since = np.zeros(N); npass = np.zeros(N); dph = np.zeros(N); refunded = np.zeros(N, bool)
    split = 0.9 if prod == 1 else 0.8; dl = 3.0 if prod == 1 else 5.0
    for t in range(days):
        risk = np.where(st == 2, rf, rc); live = st != 3
        pnl = np.where(live, R[:, t] * risk, 0); worst = np.where(live, W[:, t] * risk, 0)
        floor = (np.maximum(peak, 0) - 10) if prod == 1 else np.full(N, -10.0)
        fail = ((bal + worst <= floor) | (worst <= -dl) | (bal + pnl <= floor) | (pnl <= -dl)) & live
        bal += pnl; dph += live
        best = np.where(pnl > best, pnl, best)
        peak = np.maximum(peak, bal)
        tgt = np.where(st == 0, 10.0, 5.0)
        bd_ok = (best <= 0.5 * bal) if prod == 1 else np.ones(N, bool)
        mind = (dph >= 4) if prod == 2 else np.ones(N, bool)
        ok = (~fail) & (st <= 1) & (bal >= tgt) & bd_ok & mind
        newst = np.where(ok, 2, st) if prod == 1 else np.where(ok & (st == 0), 1, np.where(ok & (st == 1), 2, st))
        reset = ok.copy()
        since = np.where(st == 2, since + 1, 0)
        can = (st == 2) & (~fail) & (since >= 10) & (bal > 0) & (((best <= 0.5 * bal)) if prod == 1 else True)
        payout = np.where(can, bal * split / 100 * size * 1000, 0)
        refund = np.where(can & (~refunded) & (prod == 2), fee, 0); refunded |= can
        pay += payout + refund; reset |= can; since = np.where(can, 0, since)
        npass += ok & (newst == 2)
        rebuy = fail & (fees < maxf); stop = fail & (fees >= maxf)
        fees += rebuy; newst = np.where(rebuy, 0, np.where(stop, 3, newst)); reset |= fail
        refunded = np.where(rebuy, False, refunded)
        st = newst
        for a in (bal, peak, best, dph): a[reset] = 0
    net = pay / 1.12 - fees * fee
    return dict(mean=net.mean(), med=np.median(net), p10=np.percentile(net, 10), p90=np.percentile(net, 90),
                ppos=(net > 0).mean() * 100, pfund=(npass > 0).mean() * 100, cuotas=fees.mean())

RISKS = [0.1, 0.2, 0.3, 0.5, 0.75, 1.0]
rows = []
for (grp, var, mc), (PC, PW, cal) in SER.items():
    if MODO == "cierre": PW = PC
    ctrls = [("real", PC, PW)]
    if mc == 1.0:   # control: misma serie con la media diaria restada (EV que da solo la estructura de FTMO)
        m = PC.mean(); ctrls.append(("media0", PC - m, PW - m))
    for lab, a, b in ctrls:
        for prod in [2, 1]:
            for size in [10, 100]:
                best = None
                for rc in RISKS:
                    for rf in RISKS:
                        d = sim(a, b, prod, size, rc, rf, N=3000)
                        if best is None or d["mean"] > best["mean"]: best = dict(d, rc=rc, rf=rf)
                rows.append(dict(grupo=grp, var=var, costes=mc, serie=lab, prod=f"{prod}-Step", size=size, **best))
                print(rows[-1], flush=True)
D = pd.DataFrame(rows); D.to_csv(f"{OUT}/ev_ftmo_{MODO}.csv", index=False)
pd.set_option("display.width", 250)
print(D.round(1).to_string(index=False))
