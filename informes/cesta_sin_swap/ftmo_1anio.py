# Un año de la cesta de índices (IndexBasket) en FTMO 2-Step Swing 100K, con swap real y sin swap.
# Reglas FTMO 2-Step: fase 1 +10 %, fase 2 +5 %, pérdida diaria 5 % del inicial (desde el saldo del día),
# máxima 10 % estática, mínimo 4 días; fondeada: reparto 80 %, retiros cada 14 días, cuota devuelta en el 1er retiro.
import os, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..", "..")
IDX = {"US500": "USD", "US100": "USD", "US30": "USD", "GER40": "EUR", "UK100": "GBP", "JP225": "JPY"}
CAP, CUOTA, RECARGO, SPREAD = 100_000, 540.0, 0.065, 0.0003
cl = pd.concat({s: pd.read_csv(os.path.join(RAIZ, "datos_tendencia", s + ".csv"), index_col=0, parse_dates=True)["Close"]
                for s in IDX}, axis=1, sort=True).ffill().loc["2003-01-01":]
ret = cl.pct_change().fillna(0)
on = (cl > cl.rolling(200).mean()).shift(1, fill_value=False)
fred = {"USD": "DFF", "EUR": "IR3TIB01EZM156N", "GBP": "IR3TIB01GBM156N", "JPY": "IR3TIB01JPM156N"}
tip = {}
for k, f in fred.items():
    d = pd.read_csv(os.path.join(RAIZ, "datos_macro", "fred", f + ".csv")); d.columns = ["d", "v"]
    s = pd.Series(pd.to_numeric(d.v, errors="coerce").values, pd.to_datetime(d.d)).dropna() / 100
    tip[k] = s.reindex(cl.index, method="ffill").bfill()
gap = pd.Series(np.r_[1, np.diff(cl.index.values).astype("timedelta64[D]").astype(float)], cl.index)


def serie(vol_obj, swap):
    vol = ret.rolling(60).std().shift(1) * np.sqrt(252)
    w = (on * (1 / vol)).fillna(0) / len(IDX)
    pv = (w * ret).sum(axis=1).rolling(60).std().shift(1) * np.sqrt(252)
    w = w.mul((vol_obj / pv).clip(upper=8).fillna(0), axis=0).clip(upper=15 / len(IDX))
    r = (w * ret).sum(axis=1) - SPREAD * w.diff().abs().sum(axis=1)
    if swap:
        tasa = pd.concat({s: tip[c] + RECARGO for s, c in IDX.items()}, axis=1)
        r -= (w.shift(1).fillna(0) * tasa).sum(axis=1) / 365 * gap   # noches que la posición de ayer pasó abierta
    return r.loc["2005-01-01":]


def anio(r, recompra):
    """Un año (252 días). Devuelve € netos para Jorge y si llegó a fondeada."""
    neto = -CUOTA; i = 0; fondeo = False
    while i < 252:
        eq = CAP; fase = 1; dias = 0; ultimo_pago = None; pagado = False
        while i < 252:
            base = eq; eq += eq * r[i]; i += 1; dias += 1
            if eq - base < -0.05 * CAP or eq < 0.90 * CAP:
                break
            if fase in (1, 2) and dias >= 4 and eq >= CAP * (1.10 if fase == 1 else 1.05):
                fase += 1; eq = CAP; dias = 0
                if fase == 3: fondeo = True; ultimo_pago = i
            elif fase == 3 and i - ultimo_pago >= 10 and eq > CAP:     # cada 14 días naturales
                neto += 0.8 * (eq - CAP) + (CUOTA if not pagado else 0); pagado = True
                eq = CAP; ultimo_pago = i
        else:
            break
        if not recompra or i >= 252:
            break
        neto -= CUOTA                                                    # recompra tras perder la cuenta
    return neto, fondeo


def mc(r, recompra, n=5000, bloque=20, semilla=2):
    rng = np.random.default_rng(semilla); a = r.values; L = len(a)
    out = [anio(np.concatenate([a[s:s + bloque] for s in rng.integers(0, L - bloque, 252 // bloque + 1)])[:252], recompra)
           for _ in range(n)]
    x = np.array([o[0] for o in out]); f = np.array([o[1] for o in out])
    return dict(media=x.mean(), p10=np.percentile(x, 10), mediana=np.median(x), p90=np.percentile(x, 90),
                prob_fondeo=f.mean(), prob_ganar=(x > 0).mean())


filas = []
for v in (0.10, 0.15, 0.20):
    for swap in (True, False):
        r = serie(v, swap)
        for nom, x in (("cesta", r), ("control media 0", r - r.mean())):
            for rec in (False, True):
                filas.append(dict(vol=v, swap="FTMO" if swap else "sin swap", serie=nom,
                                  recompra="sí" if rec else "no", rend_anual=x.mean() * 252, **mc(x, rec)))
T = pd.DataFrame(filas)
pd.set_option("display.width", 220)
print(T.round(3).to_string(index=False)); T.to_csv(os.path.join(AQUI, "ftmo_1anio.csv"), index=False)
