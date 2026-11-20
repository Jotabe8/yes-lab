"""v17 ronda 1: cohorte de reglas diarias sobre datos reales para medir QUÉ MÉTRICA DE AJUSTE PREDICE
EL FUERA DE MUESTRA (réplica propia de Wiecki et al. 2016 y Chen-Dim 2025). Ver metodo/v17/PREREGISTRO.md.

Posición decidida al cierre de t y mantenida de cierre t a cierre t+1. R diaria = pos * ΔC / ATR20(t).
Coste: 0,01 ATR por lado (0,02 R por ida y vuelta) por unidad de cambio de posición.
Ajuste 2001-2014 (mitades A 2001-07 y B 2008-14), fuera 2015-2026-11.
Salida: metodo/v17/cohorte.parquet con una fila por regla y sus métricas.
"""
from __future__ import annotations
import itertools, sys
from pathlib import Path
import numpy as np, pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
COSTE_LADO = 0.01
CLASES = {
    "indice": ["GSPC", "NDX", "RUT", "DJI", "GDAXI", "STOXX50E", "ES", "NQ", "RTY", "YM"],
    "divisa": ["6A", "6B", "6C", "6E", "6J", "6N", "6S"],
    "energia": ["CL", "BZ", "HO", "RB", "NG"],
    "metal": ["GC", "SI", "HG", "PL"],
    "agricola": ["ZC", "ZS", "ZM", "ZL", "KE", "HE", "LE"],
    "bono": ["ZN", "ZB", "ZF", "ZT"],
}
FUENTE = {m: "datos_reversion_dz" for m in ["GSPC", "NDX", "RUT", "DJI", "GDAXI", "STOXX50E"]}
FUENTE.update({m: "datos_bonos" for m in ["ZB", "ZF", "ZT"]})


def carga(m):
    d = pd.read_csv(RAIZ / FUENTE.get(m, "datos_diversificadora") / f"{m}.csv", parse_dates=["Date"])
    d = d.set_index("Date").sort_index().dropna()
    d = d[(d.High >= d.Low) & (d.Close > 0) & (d.High > d.Low)]
    d = d[~d.index.duplicated()].loc["2000-01-01":]
    tr = pd.concat([d.High - d.Low, (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()], axis=1).max(axis=1)
    d["ATR"] = tr.rolling(20).mean()
    d["ret"] = (d.Close.shift(-1) - d.Close) / d.ATR      # R de mantener 1 unidad del cierre t al t+1
    return d.dropna()


def mantener(sen: np.ndarray, h: int) -> np.ndarray:
    """Señal en t → posición durante h sesiones (t..t+h-1), sin acumular."""
    s = pd.Series(sen.astype(float))
    return s.rolling(h, min_periods=1).max().to_numpy()


def reglas(d):
    """Genera (familia, params, lado, pos) para un mercado. Rejillas ordenadas (vecinos = índice ±1)."""
    O, H, L, C = (d[c].to_numpy() for c in ("Open", "High", "Low", "Close"))
    A = d.ATR.to_numpy()
    ibs = (C - L) / (H - L)
    c1 = np.r_[np.nan, C[:-1]]
    up, dn = C > c1, C < c1
    dow = d.index.dayofweek.to_numpy()
    out = []
    # F1 IBS reversión (largo: IBS bajo y cierre bajista; corto: espejo)
    for i, thr in enumerate([0.1, 0.2, 0.3]):
        for j, h in enumerate([1, 3, 5]):
            out.append(("ibs", (i, j), 1, mantener((ibs < thr) & dn, h)))
            out.append(("ibs", (i, j), -1, -mantener((ibs > 1 - thr) & up, h)))
    # F2 ruptura Donchian
    for i, n in enumerate([10, 20, 55]):
        mx = pd.Series(C).rolling(n).max().to_numpy(); mn = pd.Series(C).rolling(n).min().to_numpy()
        for j, h in enumerate([5, 10, 20]):
            out.append(("donchian", (i, j), 1, mantener(C >= mx, h)))
            out.append(("donchian", (i, j), -1, -mantener(C <= mn, h)))
    # F3 media móvil (solo un lado por regla)
    for i, n in enumerate([20, 50, 100, 200]):
        sma = pd.Series(C).rolling(n).mean().to_numpy()
        out.append(("sma", (i, 0), 1, (C > sma).astype(float)))
        out.append(("sma", (i, 0), -1, -(C < sma).astype(float)))
    # F4 días seguidos en contra → reversión
    for i, k in enumerate([2, 3, 4]):
        rd = pd.Series(dn.astype(float)).rolling(k).sum().to_numpy() == k
        ru = pd.Series(up.astype(float)).rolling(k).sum().to_numpy() == k
        for j, h in enumerate([1, 2, 5]):
            out.append(("seguidos", (i, j), 1, mantener(rd, h)))
            out.append(("seguidos", (i, j), -1, -mantener(ru, h)))
    # F5 día de la semana (posición del cierre del día d-1 al cierre de d → señal en dow==d-1)
    for i in range(5):
        s = (dow == (i - 1) % 5).astype(float)
        out.append(("diasemana", (i, 0), 1, s))
        out.append(("diasemana", (i, 0), -1, -s))
    # F6 momentum de serie temporal
    for i, lb in enumerate([20, 60, 120, 250]):
        m = C - np.r_[np.full(lb, np.nan), C[:-lb]]
        out.append(("tsmom", (i, 0), 1, (m > 0).astype(float)))
        out.append(("tsmom", (i, 0), -1, -(m < 0).astype(float)))
    # F7 vela grande en contra → reversión
    rng_ = (C - c1) / np.r_[np.nan, A[:-1]]
    for i, k in enumerate([1.0, 1.5, 2.0]):
        for j, h in enumerate([1, 3, 5]):
            out.append(("vela_grande", (i, j), 1, mantener(rng_ < -k, h)))
            out.append(("vela_grande", (i, j), -1, -mantener(rng_ > k, h)))
    # F8 NR-k (rango más estrecho de k días) y seguir la dirección de la vela
    rg = H - L
    for i, k in enumerate([4, 7]):
        nr = pd.Series(rg).rolling(k).min().to_numpy() == rg
        for j, h in enumerate([1, 3, 5]):
            out.append(("nr", (i, j), 1, mantener(nr & (C > O), h)))
            out.append(("nr", (i, j), -1, -mantener(nr & (C < O), h)))
    # F9 cambio de mes: largo los últimos k y primeros m días
    ym = d.index.to_period("M")
    pos_mes = pd.Series(1, index=d.index).groupby(ym).cumsum().to_numpy()
    tam = pd.Series(1, index=d.index).groupby(ym).transform("size").to_numpy()
    desde_fin = tam - pos_mes            # 0 = último día
    for i, k in enumerate([1, 2, 3]):
        for j, m in enumerate([1, 3, 5]):
            # posición al cierre de t para el día t+1: t es uno de los k-1 últimos días... aproximación:
            s = (desde_fin < k) | (pos_mes < m)
            out.append(("cambio_mes", (i, j), 1, s.astype(float)))
    return out


def metricas(r: np.ndarray, idx: pd.DatetimeIndex) -> tuple:
    """Media diaria, t por semana (suma semanal), nº de días con posición."""
    s = pd.Series(r, index=idx)
    w = s.groupby(idx.to_period("W")).sum()
    w = w[w.index.isin(w.index)]
    n = len(w)
    t = w.mean() / w.std(ddof=1) * np.sqrt(n) if n > 2 and w.std(ddof=1) > 0 else 0.0
    return float(s.mean()), float(t), int((r != 0).sum())


def main():
    filas = []
    corte = int(sys.argv[1]) if len(sys.argv) > 1 else 2015     # primer año fuera de muestra
    mitad = 2001 + (corte - 2001) // 2
    tramos = {"A": ("2001-01-01", f"{mitad - 1}-12-31"), "B": (f"{mitad}-01-01", f"{corte - 1}-12-31"),
              "IS": ("2001-01-01", f"{corte - 1}-12-31"), "OOS": (f"{corte}-01-01", "2026-12-31")}
    for clase, ms in CLASES.items():
        for m in ms:
            try:
                d = carga(m)
            except FileNotFoundError:
                print("falta", m); continue
            ret = d.ret.to_numpy()
            for fam, par, lado, pos in reglas(d):
                pos = np.nan_to_num(pos)
                cambio = np.abs(np.diff(np.r_[0.0, pos]))
                neto = pos * ret - COSTE_LADO * cambio
                bruto = pos * ret
                f = {"clase": clase, "mercado": m, "familia": fam, "p1": par[0], "p2": par[1], "lado": lado}
                for nom, (a, b) in tramos.items():
                    msk = (d.index >= a) & (d.index <= b)
                    if msk.sum() < 200:
                        for c in ("t", "mu", "tx", "mux", "expo"):
                            f[f"{c}_{nom}"] = np.nan
                        f[f"n_{nom}"] = 0
                        continue
                    mu, t, n = metricas(neto[msk], d.index[msk])
                    f[f"mu_{nom}"], f[f"t_{nom}"], f[f"n_{nom}"] = mu, t, n
                    # sin deriva: lo que aporta el momento de entrada, no la exposición (como el placebo)
                    rx = pos[msk] * (ret[msk] - ret[msk].mean()) - COSTE_LADO * cambio[msk]
                    f[f"mux_{nom}"], f[f"tx_{nom}"], _ = metricas(rx, d.index[msk])
                    f[f"expo_{nom}"] = float(np.mean(pos[msk]))
                    if nom == "IS":
                        f["vol_IS"] = float(np.std(neto[msk]))
                        f["bruto_IS"] = float(bruto[msk].mean())
                        f["coste_IS"] = float((COSTE_LADO * cambio[msk]).mean())
                        eq = np.cumsum(neto[msk]); f["dd_IS"] = float(np.max(np.maximum.accumulate(eq) - eq))
                    if nom == "OOS":
                        f["vol_OOS"] = float(np.std(neto[msk]))
                        eq = np.cumsum(neto[msk]); f["dd_OOS"] = float(np.max(np.maximum.accumulate(eq) - eq))
                filas.append(f)
        print(clase, len(filas), flush=True)
    df = pd.DataFrame(filas)
    df.to_csv(Path(__file__).parent / ("cohorte.csv.gz" if corte == 2015 else f"cohorte_{corte}.csv.gz"), index=False)
    print(df.shape)


if __name__ == "__main__":
    main()
