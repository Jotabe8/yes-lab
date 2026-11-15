"""Une bid y ask M15 de dukascopy-node en un parquet compacto (enteros en puntos).
uso: python juntar_m15.py PAR carpeta salida.parquet"""
import sys, glob, pandas as pd, numpy as np
par, carpeta, salida = sys.argv[1:4]
def leer(lado):
    fs = sorted(glob.glob(f"{carpeta}/*{lado}*.csv"))
    d = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("timestamp").set_index("timestamp").sort_index()
    return d[["open", "high", "low", "close"]]
b, a = leer("bid"), leer("ask")
d = b.join(a, lsuffix="_b", rsuffix="_a", how="inner")
esc = 1e3 if par.upper().endswith("JPY") else 1e5
out = pd.DataFrame({"t": d.index.astype("int64")})
for c in d.columns:
    out[c] = np.round(d[c].values * esc).astype("int32")
out.attrs["escala"] = esc
out.to_parquet(salida, compression="zstd", index=False)
print(par, len(out), pd.to_datetime(out.t.min(), unit="ms"), pd.to_datetime(out.t.max(), unit="ms"))
