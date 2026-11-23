"""D0: ¿el VWAP se distingue del TWAP? Compara (P − VWAP)/ATR con tres ponderaciones."""
import numpy as np
from comun import cargar_precio, vol_duka, vol_etf, vwap, atr, MERCADOS
for m in MERCADOS:
    F, X = cargar_precio(m); a = atr(X)
    vt, _, _ = vwap(X, None)
    vd = vol_duka(m, F); ve = vol_etf(m, F)
    pesos = {"duka": vd, "etf": ve}
    p = X[:, :, 3]
    N = X.shape[1]; ks = [60, 150, 270, N - 5] if N == 390 else [60, 180, 300, N - 5]
    print(f"\n{m}: días {len(F)}  {F[0].date()}..{F[-1].date()}")
    if vd is not None:
        print("  minutos con volumen Dukascopy > 0:", f"{np.nanmean(vd > 0):.3f}")
    for nom, w in pesos.items():
        if w is None:
            print(f"  {nom}: sin datos"); continue
        ok = np.isfinite(w).sum(1) > 0.8 * N
        vv, _, sin = vwap(X, w)
        for nom2, ref in [("twap", vt)] + ([("duka", vwap(X, vd)[0])] if nom == "etf" and vd is not None else []):
            da = (p - vv) / a[:, None]; db = (p - ref) / a[:, None]
            g = ok & np.isfinite(a)
            cors = [np.corrcoef(da[g, k], db[g, k])[0, 1] for k in ks]
            signo = np.mean(np.sign(da[g, 30:]) == np.sign(db[g, 30:]))
            dif = np.nanmedian(np.abs(vv[g] - ref[g]) / a[g, None])
            print(f"  {nom} vs {nom2}: días {g.sum()}  corr (P−VWAP)/ATR en minutos {ks}: "
                  + " ".join(f"{c:.3f}" for c in cors) + f"  signo igual {signo:.3f}  |ΔVWAP|/ATR mediana {dif:.3f}")
