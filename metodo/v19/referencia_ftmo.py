"""P5 v19: referencia Python sobre las velas D1 de FTMO y comparación semana a semana con el EA.

1) Exporta de MT5 (FTMO) las D1 de cada símbolo a una carpeta: <SIMBOLO>.csv con columnas time;close
   (script ExportarD1.mq5 o el tester), hora del servidor.
2) python -m metodo.v19.referencia_ftmo <carpeta_d1> [TendenciaCripto_semanas.csv]
   Sin el CSV del EA, solo escribe referencia_semanas.csv (las R de modelo por símbolo y semana).
   Con él, empareja por (fecha, símbolo) y aplica los umbrales de metodo/comparar_ops.py.
"""
import glob, os, sys
import numpy as np, pandas as pd
from metodo.comparar_ops import MIN_EMPAREJADAS, MAX_DIF_MEDIA, MAX_DIF_ABS, MIN_CERCANAS, MIN_CORR, MAX_DR


def leer_d1(ruta):
    d = pd.read_csv(ruta, sep=None, engine="python")
    d.columns = [c.lower().strip() for c in d.columns]
    t = pd.to_datetime(d["time"].astype(str).str.replace(".", "-", regex=False)).dt.normalize()
    return pd.Series(pd.to_numeric(d["close"], errors="coerce").values, t).dropna().groupby(level=0).last()


def semanas(c, look=28, vol=30):
    c = c.reindex(pd.date_range(c.index[0], c.index[-1], freq="D")).ffill()
    lr = np.log(c).diff()
    sg = lr.rolling(vol, min_periods=vol).std() * np.sqrt(7)
    dom = c.index[(c.index.dayofweek == 6)]
    dom = dom[dom + pd.Timedelta(days=7) <= c.index[-1]]
    s = (c / c.shift(look) - 1 > 0).loc[dom]
    r = ((c.shift(-7) / c - 1) / sg).loc[dom]
    ok = s & sg.loc[dom].notna()
    return pd.DataFrame({"fecha": dom[ok] + pd.Timedelta(days=7), "r": r[ok].values})


def main():
    carpeta = sys.argv[1]
    filas = []
    for f in sorted(glob.glob(os.path.join(carpeta, "*.csv"))):
        sim = os.path.splitext(os.path.basename(f))[0]
        if sim.startswith(("_", "referencia")):
            continue
        w = semanas(leer_d1(f)); w["simbolo"] = sim; filas.append(w)
    py = pd.concat(filas, ignore_index=True)
    py.to_csv(os.path.join(carpeta, "referencia_semanas.csv"), index=False)
    print(f"Python: {len(py)} semanas compradas, R media {py.r.mean():+.3f}")
    if len(sys.argv) < 3:
        return
    ea = pd.read_csv(sys.argv[2], sep=";")
    ea["fecha"] = pd.to_datetime(ea.fecha.str.replace(".", "-", regex=False))
    desde, hasta = ea.fecha.min(), ea.fecha.max()
    py = py[(py.fecha >= desde) & (py.fecha <= hasta)]
    j = py.merge(ea.rename(columns={"r_modelo": "r_ea"}), on=["fecha", "simbolo"], how="outer", indicator=True)
    par = j[j._merge == "both"]
    f_py = len(par) / max(len(py), 1); f_ea = len(par) / max(len(ea), 1)
    dif = abs(par.r_ea.mean() - par.r.mean())
    ok_media = dif <= max(MAX_DIF_MEDIA * abs(par.r.mean()), MAX_DIF_ABS)
    corr = par.r.corr(par.r_ea); cerca = ((par.r - par.r_ea).abs() <= MAX_DR).mean()
    print(f"emparejadas {len(par)} ({f_py:.0%} de Python, {f_ea:.0%} del EA) | R media Python {par.r.mean():+.3f} EA {par.r_ea.mean():+.3f}"
          f" | corr {corr:.3f} | |ΔR| ≤ {MAX_DR}: {cerca:.0%}")
    pasa = min(f_py, f_ea) >= MIN_EMPAREJADAS and ok_media and corr >= MIN_CORR and cerca >= MIN_CERCANAS
    print("P5:", "PASA" if pasa else "NO PASA")
    print("Solo en Python:\n", j[j._merge == "left_only"][["fecha", "simbolo", "r"]].head(15).to_string())
    print("Solo en el EA:\n", j[j._merge == "right_only"][["fecha", "simbolo", "r_ea"]].head(15).to_string())
    par = par.assign(dr=(par.r - par.r_ea).abs()).sort_values("dr", ascending=False)
    print("Mayores diferencias:\n", par[["fecha", "simbolo", "r", "r_ea", "dr"]].head(15).to_string())


if __name__ == "__main__":
    main()
