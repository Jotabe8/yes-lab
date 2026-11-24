"""D0b: US100, días con volumen de ticks FTMO y de QQQ a la vez: VWAP de ticks vs VWAP real."""
import numpy as np
from comun import cargar_precio, vol_duka, vol_etf, vwap, atr
F, X = cargar_precio("US100"); a = atr(X); vd = vol_duka("US100", F); ve = vol_etf("US100", F)
ok = (np.isfinite(vd).sum(1) > 300) & (np.isfinite(ve).sum(1) > 300) & np.isfinite(a)
X, a, vd, ve = X[ok], a[ok], vd[ok], ve[ok]
p = X[:, :, 3]; vt = vwap(X, vd)[0]; vr = vwap(X, ve)[0]; tw = vwap(X, None)[0]
print("días", ok.sum(), "corr perfil de volumen ticks vs QQQ (media por minuto):",
      round(np.corrcoef(np.nanmean(vd, 0), np.nanmean(ve, 0))[0, 1], 3),
      "| corr minuto a minuto:", round(np.corrcoef(np.nan_to_num(vd).ravel(), np.nan_to_num(ve).ravel())[0, 1], 3))
for n1, v1, n2, v2 in [("ticks", vt, "real QQQ", vr), ("twap", tw, "real QQQ", vr), ("ticks", vt, "twap", tw)]:
    da, db = (p - v1) / a[:, None], (p - v2) / a[:, None]
    print(f"{n1} vs {n2}: corr (P−VWAP)/ATR 10:30/12:00/14:00/15:55 " +
          " ".join(f"{np.corrcoef(da[:, k], db[:, k])[0, 1]:.3f}" for k in (60, 150, 270, 385)) +
          f"  signo igual {np.mean(np.sign(da[:, 30:]) == np.sign(db[:, 30:])):.3f}  |ΔVWAP|/ATR mediana {np.median(np.abs(v1 - v2) / a[:, None]):.3f}")
