# Cesta larga de índices en cuenta sin swap con reglas de E8 Pro (1 fase). Monte Carlo por bloques.
# Reglas (help center E8 + tradetanto, ago-2026): objetivo 8 %, solo cuenta 2 % del inicial por día,
# pérdida diaria 2,5 % desde el saldo del día, máxima 8 % estática; tras el 1er retiro el suelo sube al
# saldo inicial. Retiro cuando hay ≥ 1 % de beneficio desde el último: se puede pedir el 50 %, se cobra
# el reparto (80 %); el resto queda como colchón. Lo que pase del 2 % diario se pierde también en fondeada.
import os, numpy as np, pandas as pd
AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "..", "datos_tendencia")
IDX = ["US500", "US100", "US30", "GER40", "UK100", "JP225"]
SPREAD = 0.0003            # coste por unidad de rotación
CAP = 100_000
cl = pd.concat({s: pd.read_csv(os.path.join(DATOS, s + ".csv"), index_col=0, parse_dates=True)["Close"] for s in IDX},
               axis=1).ffill().loc["2003-01-01":]
ret = cl.pct_change().fillna(0)
on = (cl > cl.rolling(200).mean()).shift(1, fill_value=False)          # filtro SMA200 al cierre de ayer


def serie(vol_obj):
    vol = ret.rolling(60).std().shift(1) * np.sqrt(252)
    w = (on * (1 / vol)).fillna(0)
    w = w.div(len(IDX))                                                 # peso inverso a la volatilidad
    port = (w * ret).sum(axis=1)
    pv = port.rolling(60).std().shift(1) * np.sqrt(252)
    esc = (vol_obj / pv).clip(upper=8).fillna(0)
    w = w.mul(esc, axis=0)
    w = w.clip(upper=15 / len(IDX))                                     # apalancamiento 1:15
    r = (w * ret).sum(axis=1) - SPREAD * w.diff().abs().sum(axis=1)
    return r.loc["2005-01-01":]


def cuenta(r, split=0.8):
    """Una cuenta durante len(r) días. Devuelve (pasó, cobrado por el trader)."""
    eq = CAP; contado = 0.0; fase = 0; suelo = CAP * 0.92; ultimo = CAP; cobrado = 0.0; pagos = 0
    for x in r:
        base = eq
        g = eq * x
        if g > 0.02 * CAP:                    # lo que pasa del 2 % del inicial en un día se pierde
            g = 0.02 * CAP
        if g < -0.025 * CAP:                  # pérdida diaria (al cierre; margen de 0,3 % por el intradía)
            return fase == 1, cobrado
        eq += g
        if eq - base < -0.022 * CAP or eq < suelo:
            return fase == 1, cobrado
        if fase == 0:
            if eq >= CAP * 1.08:
                fase = 1; eq = CAP; ultimo = CAP
        else:
            if eq - ultimo >= 0.01 * CAP:
                ped = 0.5 * (eq - CAP) if pagos == 0 else 0.5 * (eq - ultimo)
                if ped > 0:
                    cobrado += ped * split; eq -= ped; pagos += 1; suelo = CAP; ultimo = eq
    return fase == 1, cobrado


def mc(r, n=3000, dias=756, bloque=20, semilla=1):
    rng = np.random.default_rng(semilla)
    a = r.values; L = len(a)
    res = []
    for _ in range(n):
        idx = np.concatenate([np.arange(s, s + bloque) for s in rng.integers(0, L - bloque, dias // bloque + 1)])[:dias]
        res.append(cuenta(a[idx]))
    p = np.array([x[0] for x in res]); c = np.array([x[1] for x in res])
    return p.mean(), c.mean(), np.percentile(c, 50)


filas = []
for v in (0.05, 0.075, 0.10, 0.15):
    r = serie(v)
    ra = r.mean() * 252; dd = (r.cumsum() - r.cumsum().cummax()).min()
    for nom, x in (("cesta", r), ("control media 0", r - r.mean())):
        p, c, med = mc(x)
        filas.append(dict(vol=v, serie=nom, rend_anual=ra if nom == "cesta" else 0.0, dd_hist=dd, p_pasa=p,
                          cobro_medio_3a=c, cobro_mediana=med))
T = pd.DataFrame(filas)
pd.set_option("display.width", 200)
print(T.round(3).to_string(index=False)); T.to_csv(os.path.join(AQUI, "ev_e8.csv"), index=False)
print("\nRendimiento anual por periodos (vol 10 %):")
r = serie(0.10); print((r.groupby(r.index.year).sum()).round(3).to_dict())
