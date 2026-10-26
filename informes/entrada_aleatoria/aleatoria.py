# Entrada aleatoria (moneda) con gestión de riesgo NNFX, D1, forex + oro + índices + materias primas + cripto.
# Pre-registro (2026-10-26): la entrada es una moneda; lo único que se prueba es la gestión.
#   Variantes de gestión fijadas antes de mirar resultados (VARS abajo). Ajuste 2018-2022, prueba 2023-2026.
#   Una variante vale solo si su R neto medio es > 0 en ajuste y prueba, con t >= 2 por bootstrap de bloques,
#   sigue > 0 al doble de costes y su EV por cuota FTMO supera al control de media cero (misma serie, media restada).
# Uso: python3 aleatoria.py DIR_OHLC DIR_D1 SALIDA_DIR [semillas]
import sys, os, numpy as np, pandas as pd
from numba import njit

DIR_OHLC, DIR_D1, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
S = int(sys.argv[4]) if len(sys.argv) > 4 else 100
os.makedirs(OUT, exist_ok=True)
START, IS_END, OOS = "2018-01-01", "2022-12-31", "2023-01-01"

# mercado: (fichero, grupo, coste ida y vuelta, tipo de coste, financiación anual media de la posición)
# coste 'px' = en precio; 'pct' = fracción del precio. Financiación: solo el recargo del broker (la entrada es
# aleatoria, así que el diferencial de tipos se compensa entre largos y cortos de media).
FX = "EURUSD GBPUSD USDJPY AUDUSD USDCAD NZDUSD USDCHF EURJPY GBPJPY AUDNZD EURAUD".split()
MK = {s: (f"{DIR_OHLC}/{s}_D1.csv", "forex", 2.2 * (0.01 if s.endswith("JPY") else 0.0001), "px", 0.010) for s in FX}
MK["XAUUSD"] = (f"{DIR_OHLC}/XAUUSD_D1.csv", "oro", 0.35, "px", 0.025)
for s, f, c in [("US500", "USA500IDXUSD", 0.00015), ("US100", "USATECHIDXUSD", 0.00012), ("US30", "USA30IDXUSD", 0.00008),
                ("GER40", "DEUIDXEUR", 0.00012), ("UK100", "GBRIDXGBP", 0.00015), ("JP225", "JPNIDXJPY", 0.00030),
                ("FRA40", "FRAIDXEUR", 0.00020), ("EU50", "EUSIDXEUR", 0.00040)]:
    MK[s] = (f"{DIR_D1}/{f}.csv", "indices", c, "pct", 0.025)
MK["XAGUSD"] = (f"{DIR_D1}/XAGUSD.csv", "materias", 0.0010, "pct", 0.025)
MK["WTI"] = (f"{DIR_D1}/LIGHTCMDUSD.csv", "materias", 0.0006, "pct", 0.030)
MK["BTCUSD"] = (f"{DIR_D1}/BTCUSD.csv", "cripto", 0.0008, "pct", 0.15)
MK["ETHUSD"] = (f"{DIR_D1}/ETHUSD.csv", "cripto", 0.0012, "pct", 0.15)

# gestión: sl, tp1 (ATR), fracción en tp1, BE tras tp1, trailing (ATR), trailing desde el inicio, tp final, días máx
VARS = {
    "V0 moneda 1:1 (SL=TP=1,5 ATR)":        (1.5, 1.5, 1.0, 0, 0.0, 0, 0.0, 0),
    "V1 NNFX VP (mitad 1 ATR, BE, trail 2)": (1.5, 1.0, 0.5, 1, 2.0, 0, 0.0, 0),
    "V2 NNFX 1 orden (TP 1 ATR)":           (1.5, 1.0, 1.0, 0, 0.0, 0, 0.0, 0),
    "V3 Van Tharp (trail 3 ATR siempre)":   (3.0, 0.0, 0.0, 0, 3.0, 1, 0.0, 0),
    "V4 NNFX VP + máx 20 días":             (1.5, 1.0, 0.5, 1, 2.0, 0, 0.0, 20),
}

def load(f, crypto):
    d = pd.read_csv(f)
    d.columns = [x.lower() for x in d.columns]
    d["date"] = pd.to_datetime(d.date.astype(str).str.replace(".", "-"))
    d = d.rename(columns=dict(open="o", high="h", low="l", close="c"))[["date", "o", "h", "l", "c"]]
    d = d[(d.date >= "2017-08-01") & (d.h > d.l)].sort_values("date")
    if not crypto:   # vela de domingo de Dukascopy -> se funde con el lunes
        d["k"] = d.date + pd.to_timedelta((d.date.dt.weekday == 6).astype(int), "D")
        d = d[d.k.dt.weekday < 5].groupby("k").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"))
    else:
        d = d.set_index("date")[["o", "h", "l", "c"]]
    return d

@njit(cache=True)
def run(o, h, l, c, A, gap, u, cost, cpct, fin, sl_m, tp1_m, f1, be, tr_m, tr_all, tpf_m, maxd, t0):
    n = len(c)
    pc = np.zeros(n); pw = np.zeros(n); pg = np.zeros(n)          # pnl neto al cierre, peor intradía, pnl bruto (R)
    tr_i = np.full(n, -1); tr_R = np.zeros(n); tr_g = np.zeros(n); tr_d = np.zeros(n); tr_c = np.zeros(n); nt = 0
    pos = 0; ent = 0.0; risk = 0.0; sl = 0.0; tp1 = 0.0; tpf = 0.0; w = 0.0; mark = 0.0; done1 = False
    accR = 0.0; accG = 0.0; i0 = 0; cR = 0.0
    pend = 0
    for t in range(t0, n):
        if pos == 0 and pend != 0:
            pos = pend; pend = 0; ent = o[t]; risk = sl_m * A[t - 1]
            sl = ent - pos * risk; tp1 = ent + pos * tp1_m * A[t - 1]; tpf = ent + pos * tpf_m * A[t - 1]
            w = 1.0; mark = ent; done1 = False; i0 = t
            cR = (cost * ent if cpct else cost) / risk
            pc[t] -= cR; accR = -cR; accG = 0.0
        if pos == 0:
            if u[t] != 0: pend = u[t]
            continue
        day = 0.0
        # peor punto intradía con el peso que había al abrir la vela
        adv = l[t] if pos == 1 else h[t]
        if pos * (adv - sl) < 0: adv = sl
        pw[t] += w * pos * (adv - mark) / risk
        closed = False
        if (pos == 1 and l[t] <= sl) or (pos == -1 and h[t] >= sl):     # stop primero si tocan los dos
            px = min(o[t], sl) if pos == 1 else max(o[t], sl)
            day += w * pos * (px - mark) / risk; w = 0.0; closed = True
        else:
            if tp1_m > 0 and not done1 and ((pos == 1 and h[t] >= tp1) or (pos == -1 and l[t] <= tp1)):
                px = max(o[t], tp1) if pos == 1 else min(o[t], tp1)
                day += f1 * pos * (px - mark) / risk; w -= f1; done1 = True
                if be: sl = ent
                if w <= 1e-9: closed = True
            if not closed and tpf_m > 0 and ((pos == 1 and h[t] >= tpf) or (pos == -1 and l[t] <= tpf)):
                day += w * pos * (tpf - mark) / risk; w = 0.0; closed = True
            if not closed and maxd > 0 and t - i0 + 1 >= maxd:
                day += w * pos * (c[t] - mark) / risk; w = 0.0; closed = True
            if not closed:
                day += w * pos * (c[t] - mark) / risk; mark = c[t]
                if tr_m > 0 and (tr_all or done1):
                    ns = c[t] - pos * tr_m * A[t]
                    if pos * (ns - sl) > 0: sl = ns
        if t + 1 < n: sw = w * fin / 365.0 * gap[t + 1] * c[t] / risk   # financiación por las noches hasta la vela siguiente
        else: sw = 0.0
        pc[t] += day - sw; pg[t] += day; accR += day - sw; accG += day
        pw[t] += -cR if t == i0 else 0.0
        if closed:
            tr_i[nt] = i0; tr_R[nt] = accR; tr_g[nt] = accG; tr_d[nt] = t - i0 + 1; tr_c[nt] = cR; nt += 1
            pos = 0
            if u[t] != 0: pend = u[t]
    pw = np.minimum(pw, pc)
    return pc, pw, pg, tr_i[:nt], tr_R[:nt], tr_g[:nt], tr_d[:nt], tr_c[:nt]

def atr(d, n=14):
    pc = d.c.shift(); tr = pd.concat([d.h - d.l, (d.h - pc).abs(), (d.l - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

DATA = {}
for s, (f, g, cost, ct, fin) in MK.items():
    d = load(f, g == "cripto"); d["A"] = atr(d)
    d["gap"] = np.r_[1, np.diff(d.index.values).astype("timedelta64[D]").astype(float)]
    DATA[s] = d
CAL = pd.bdate_range(START, min(d.index.max() for d in DATA.values()))   # calendario común (laborables)
END_FX = max(DATA["EURUSD"].index.max(), CAL[-1])
CAL_FX = pd.bdate_range(START, DATA["EURUSD"].index.max())

def to_cal(idx, x, cal):   # suma fines de semana de cripto en el lunes siguiente
    s = pd.Series(x, idx)
    k = idx + pd.to_timedelta(np.where(idx.weekday == 5, 2, np.where(idx.weekday == 6, 1, 0)), "D")
    return s.groupby(k).sum().reindex(cal, fill_value=0.0).values

def simulate(var, seed, mult_cost=1.0, groups=None, cal=CAL):
    sl_m, tp1_m, f1, be, tr_m, tr_all, tpf_m, maxd = VARS[var]
    rng = np.random.default_rng(seed)
    PC = np.zeros(len(cal)); PW = np.zeros(len(cal)); PG = np.zeros(len(cal)); NOPEN = np.zeros(len(cal)); T = []
    for s, d in DATA.items():
        g = MK[s][1]
        if groups and g not in groups: continue
        u = np.where(rng.random(len(d)) < 0.5, 1, -1).astype(np.int64)
        t0 = int(np.searchsorted(d.index.values, np.datetime64(START)))
        pc, pw, pg, ti, tR, tg, td, tc = run(d.o.values, d.h.values, d.l.values, d.c.values, d.A.values, d.gap.values, u,
                                           MK[s][2] * mult_cost, MK[s][3] == "pct", MK[s][4], sl_m, tp1_m, f1, be, tr_m, tr_all, tpf_m, maxd, t0)
        PC += to_cal(d.index, pc, cal); PW += to_cal(d.index, pw, cal); PG += to_cal(d.index, pg, cal)
        T.append(pd.DataFrame(dict(sym=s, grp=g, date=d.index[ti], R=tR, G=tg, dias=td, coste=tc)))
    T = pd.concat(T); T = T[T.date <= cal[-1]]
    return PC, PW, PG, T

def boot_t(daily, ntr, block=20, B=2000, seed=0):
    """t del R medio por operación con bootstrap de bloques sobre días (la serie ya promedia las semillas)."""
    rng = np.random.default_rng(seed); n = len(daily); nb = n // block + 1
    m = daily.sum() / ntr; ms = np.empty(B)
    for b in range(B):
        st = rng.integers(0, n - block, nb); idx = (st[:, None] + np.arange(block)).ravel()[:n]
        ms[b] = daily[idx].sum() / ntr
    return m / ms.std()

if __name__ == "__main__":
    rows = []; yrs = []; seriesF = {}
    for grp_name, groups, cal in [("forex+oro", ["forex", "oro"], CAL_FX), ("todos", None, CAL)]:
        for var in VARS:
            for mc in [1.0, 2.0]:
                acc = []; PCm = np.zeros(len(cal)); PGm = np.zeros(len(cal)); store_pc = []; store_pw = []
                for sd in range(S):
                    PC, PW, PG, T = simulate(var, 1000 + sd, mc, groups, cal)
                    T["seed"] = sd; acc.append(T); PCm += PC / S; PGm += PG / S
                    if mc == 1.0 or True: store_pc.append(PC); store_pw.append(PW)
                T = pd.concat(acc); ntr = len(T) / S
                seriesF[(grp_name, var, mc)] = (np.array(store_pc, dtype=np.float32), np.array(store_pw, dtype=np.float32), cal)
                for per, a, b in [("2018-22", START, IS_END), ("2023-26", OOS, "2027-01-01"), ("todo", START, "2027-01-01")]:
                    msk = (cal >= a) & (cal <= b); tt = T[(T.date >= a) & (T.date <= b)]; nn = len(tt) / S
                    ps = tt.groupby("seed").R.mean()
                    rows.append(dict(grupo=grp_name, var=var, costes=mc, periodo=per, ops_año=nn / (msk.sum() / 252),
                                     bruto=tt.G.mean(), neto=tt.R.mean(), coste_R=tt.coste.mean(), acierto=(tt.R > 0).mean() * 100,
                                     dias=tt.dias.mean(), t_bruto=boot_t(PGm[msk], nn), t_neto=boot_t(PCm[msk], nn),
                                     sem_p5=ps.quantile(.05), sem_p95=ps.quantile(.95)))
                if mc == 1.0:
                    T["y"] = T.date.dt.year
                    for (y, g2), x in T.groupby(["y", "grp"]): yrs.append(dict(grupo=grp_name, var=var, año=y, mercado=g2, neto=x.R.mean(), n=len(x) / S))
                    for s2, x in T.groupby("sym"): yrs.append(dict(grupo=grp_name, var=var, año="todo", mercado=s2, neto=x.R.mean(), n=len(x) / S))
                print(grp_name, var, mc, "hecho", flush=True)
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/resumen.csv", index=False)
    pd.DataFrame(yrs).to_csv(f"{OUT}/por_año_mercado.csv", index=False)
    np.save(f"{OUT}/series.npy", {k: v for k, v in seriesF.items()}, allow_pickle=True)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    print(R.round(3).to_string(index=False))
