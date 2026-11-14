"""Tendencia de largo plazo en forex D1 con gestión NNFX. Reglas en PREREGISTRO.md (commit 60bc044)."""
import numpy as np, pandas as pd, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PARES = ["AUDNZD", "AUDUSD", "EURAUD", "EURJPY", "EURUSD", "GBPJPY", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]
COSTE_PIPS = dict(EURUSD=0.8, USDJPY=0.9, AUDUSD=1.0, GBPUSD=1.1, USDCAD=1.3, USDCHF=1.3, NZDUSD=1.4,
                  EURJPY=1.5, EURAUD=2.0, GBPJPY=2.5, AUDNZD=2.5)
DIVISA_TIPO = dict(EUR="EZ", USD="US", GBP="GB", JPY="JP", AUD="AU", NZD="NZ", CAD="CA", CHF="CH")


def tipos():
    t = {}
    for c, s in DIVISA_TIPO.items():
        d = pd.read_csv(f"{AQUI}/datos/tipo3m_{s}.csv")
        d.columns = ["fecha", "v"]
        d["fecha"] = pd.to_datetime(d.fecha)
        t[c] = d.set_index("fecha").v.astype(float)
    return t


def cargar(par, T):
    d = pd.read_csv(f"{AQUI}/datos/{par}_D1.csv")
    d["Date"] = pd.to_datetime(d.Date, format="%Y.%m.%d")
    d = d.set_index("Date")[["Open", "High", "Low", "Close"]].astype(float)
    # diferencial de tipos base - cotizada (% anual), con un mes de retraso (dato publicado)
    b, q = par[:3], par[3:]
    dif = (T[b] - T[q]).reindex(d.index.union(T[b].index)).ffill().shift(1).reindex(d.index).ffill().fillna(0)
    d["dif"] = dif.values / 100.0
    return d


def atr_wilder(d, n=14):
    h, l, c = d.High.values, d.Low.values, d.Close.values
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    tr = np.r_[h[0] - l[0], tr]
    a = np.full(len(tr), np.nan)
    a[n - 1] = tr[:n].mean()
    for i in range(n, len(tr)):
        a[i] = (a[i - 1] * (n - 1) + tr[i]) / n
    return a


def senales(d, var):
    c = d.Close
    if var in ("V1", "V2"):
        n = 55 if var == "V1" else 100
        hi = c.rolling(n).max().shift(1); lo = c.rolling(n).min().shift(1)
        sig = np.where(c > hi, 1, np.where(c < lo, -1, 0))
        m = n // 2
        sal_hi = c.rolling(m).max().shift(1).values; sal_lo = c.rolling(m).min().shift(1).values
        # salida largo: cierre < mínimo m; salida corto: cierre > máximo m
        sal_largo = (c.values < sal_lo); sal_corto = (c.values > sal_hi)
    else:
        f, s = c.rolling(50).mean(), c.rolling(200).mean()
        up = (f > s).astype(int).values; ok = s.notna().values
        prev = np.r_[0, up[:-1]]; okp = np.r_[False, ok[:-1]]
        sig = np.where(ok & okp & (up == 1) & (prev == 0), 1, np.where(ok & okp & (up == 0) & (prev == 1), -1, 0))
        sal_largo = (up == 0) & ok; sal_corto = (up == 1) & ok
    return np.asarray(sig), sal_largo, sal_corto


def operar(d, atr, entradas, sal_largo, sal_corto, par):
    """entradas: lista de (i_senal, dir). Devuelve lista de dicts por operación. Ignora entradas solapadas."""
    O, H, L, C = d.Open.values, d.High.values, d.Low.values, d.Close.values
    dif = d.dif.values; fechas = d.index
    pip = 0.01 if par.endswith("JPY") else 0.0001
    coste = COSTE_PIPS[par] * pip
    n = len(C); ops = []; libre = 0
    for i, s in entradas:
        if i < libre or i + 1 >= n or np.isnan(atr[i]):
            continue
        e = O[i + 1]; a = atr[i]; st = 1.5 * a
        sl = e - s * st; tp = e + s * a
        A_abierta = B_abierta = True; pA = pB = None; be = False; j = i + 1; jA = jB = None
        sal = sal_largo if s == 1 else sal_corto
        while j < n and (A_abierta or B_abierta):
            # apertura (huecos)
            o = O[j]
            stop_act = e if be else sl
            if j > i + 1:
                if (s == 1 and o <= stop_act) or (s == -1 and o >= stop_act):
                    if A_abierta: pA, jA, A_abierta = o, j, False
                    if B_abierta: pB, jB, B_abierta = o, j, False
                    break
                if A_abierta and ((s == 1 and o >= tp) or (s == -1 and o <= tp)):
                    pA, jA, A_abierta = o, j, False; be = True; stop_act = e
            # dentro de la vela: stop primero
            golpe_sl = (s == 1 and L[j] <= stop_act) or (s == -1 and H[j] >= stop_act)
            if golpe_sl:
                if A_abierta: pA, jA, A_abierta = stop_act, j, False
                if B_abierta: pB, jB, B_abierta = stop_act, j, False
                break
            if A_abierta and ((s == 1 and H[j] >= tp) or (s == -1 and L[j] <= tp)):
                pA, jA, A_abierta = tp, j, False; be = True
            # salida por indicador al cierre -> apertura siguiente
            if sal[j]:
                k = min(j + 1, n - 1)
                if A_abierta: pA, jA, A_abierta = O[k], k, False
                if B_abierta: pB, jB, B_abierta = O[k], k, False
                j = k; break
            j += 1
        if A_abierta or B_abierta:  # fin de datos
            k = n - 1
            if A_abierta: pA, jA = C[k], k
            if B_abierta: pB, jB = C[k], k
        libre = max(jA, jB) + 1
        rA = s * (pA - e) / st; rB = s * (pB - e) / st
        bruto = 0.5 * rA + 0.5 * rB
        c_r = coste / st  # ida y vuelta de las dos mitades = coste sobre la posición completa
        # swap por día natural de cada mitad
        def sw(jx, recargo):
            dias = (fechas[jx] - fechas[i + 1]).days
            difm = dif[i + 1:jx + 1].mean() if jx > i + 1 else dif[i + 1]
            return (s * difm - recargo) * e * dias / 365.0 / st
        swap = 0.5 * sw(jA, 0.015) + 0.5 * sw(jB, 0.015)
        swap3 = 0.5 * sw(jA, 0.03) + 0.5 * sw(jB, 0.03)
        ops.append(dict(par=par, fecha=fechas[i + 1], dir=s, dias=(fechas[max(jA, jB)] - fechas[i + 1]).days,
                        bruto=bruto, coste=c_r, swap=swap, swap3=swap3, rA=rA, rB=rB,
                        neto=bruto - c_r + swap, estres=bruto - 2 * c_r + swap3))
    return ops


def correr(var, datos, modo="real", rng=None):
    todas = []
    for par, (d, atr) in datos.items():
        sig, sl_, sc_ = senales(d, var)
        if modo == "real":
            ent = [(i, int(sig[i])) for i in np.nonzero(sig)[0]]
        elif modo == "contrario":
            ent = [(i, -int(sig[i])) for i in np.nonzero(sig)[0]]
            sl_, sc_ = sc_, sl_  # el canal contrario se mide respecto al lado tomado
        else:  # aleatorio: mismo nº de entradas efectivas que el real, días y lado al azar
            n_real = len(operar(d, atr, [(i, int(sig[i])) for i in np.nonzero(sig)[0]], sl_, sc_, par))
            validos = np.arange(200, len(d) - 2)
            ent = []; libre = 0; ops_par = []
            # se generan candidatos al azar ordenados y se toman hasta igualar n_real
            cand = np.sort(rng.choice(validos, size=min(len(validos), n_real * 6), replace=False))
            dirs = rng.choice([-1, 1], size=len(cand))
            ent = list(zip(cand, dirs))
            # salida por canal según lado: se calcula con las señales del canal del lado aleatorio
            ops_par = operar(d, atr, ent, sl_, sc_, par)
            sel = rng.choice(len(ops_par), size=min(n_real, len(ops_par)), replace=False)
            todas += [ops_par[k] for k in sel]
            continue
        todas += operar(d, atr, ent, sl_, sc_, par)
    return pd.DataFrame(todas)


def resumen(df, col="neto"):
    x = df[col]; return x.mean(), x.mean() / x.std(ddof=1) * np.sqrt(len(x)), len(x)


if __name__ == "__main__":
    T = tipos()
    datos = {}
    for p in PARES:
        d = cargar(p, T); datos[p] = (d, atr_wilder(d))
    rng = np.random.default_rng(20261114)
    salida = []
    def out(s=""):
        print(s); salida.append(s)
    for var in ["V1", "V2", "V3"]:
        df = correr(var, datos)
        df.to_csv(f"{AQUI}/ops_{var}.csv", index=False)
        m, t, n = resumen(df)
        out(f"\n=== {var} === ops {n}  ({n/21.2:.0f}/año en 11 pares), días medios {df.dias.mean():.0f}")
        out(f"bruto {df.bruto.mean():+.3f} R | coste {df.coste.mean():.3f} R | swap {df.swap.mean():+.3f} R | "
            f"neto {m:+.3f} R t {t:.2f} | estrés (coste×2, recargo 3%) {df.estres.mean():+.3f} R")
        out(f"mitad A {df.rA.mean():+.3f} R (TP 1 ATR alcanzado {np.mean(df.rA > 0.6):.0%}) | mitad B {df.rB.mean():+.3f} R")
        h1 = df[df.fecha < "2016-01-01"]; h2 = df[df.fecha >= "2016-01-01"]
        out(f"2005-15 neto {h1.neto.mean():+.3f} (n {len(h1)}) | 2016-26 neto {h2.neto.mean():+.3f} (n {len(h2)}, t {resumen(h2)[1]:.2f})")
        pp = df.groupby("par").neto.mean()
        out("por par: " + ", ".join(f"{k} {v:+.2f}" for k, v in pp.items()) + f"  -> {int((pp > 0).sum())}/11 +")
        ya = df.groupby(df.fecha.dt.year).neto.sum()
        out("R neta por año: " + ", ".join(f"{k} {v:+.1f}" for k, v in ya.items()))
        out(f"largos neto {df[df.dir==1].neto.mean():+.3f} | cortos {df[df.dir==-1].neto.mean():+.3f}")
        con = correr(var, datos, "contrario")
        out(f"placebo lado contrario: bruto {con.bruto.mean():+.3f} neto {con.neto.mean():+.3f}")
        if var == "V1" or "--todos" in sys.argv:
            reps = [correr(var, datos, "aleatorio", rng) for _ in range(200)]
            pn = np.array([r.neto.mean() for r in reps]); pb = np.array([r.bruto.mean() for r in reps])
            out(f"placebo entrada aleatoria (200): neto media {pn.mean():+.3f} p95 {np.percentile(pn,95):+.3f} | "
                f"bruto media {pb.mean():+.3f} p95 {np.percentile(pb,95):+.3f} | real supera en neto al {np.mean(pn < m):.0%}")
            crit = [t >= 2.4, h2.neto.mean() > 0, df.estres.mean() > 0, m > np.percentile(pn, 95), (pp > 0).sum() >= 7]
            out(f"CRITERIOS t≥2,4 {crit[0]} | 2ª mitad>0 {crit[1]} | estrés>0 {crit[2]} | >p95 placebo {crit[3]} | ≥7/11 pares {crit[4]}")
            out("VEREDICTO: " + ("PASA" if all(crit) else "NO PASA"))
    open(f"{AQUI}/salida.txt", "w").write("\n".join(salida) + "\n")
