"""v19: momentum de series temporales semanal en una cesta cripto (ver PREREGISTRO.md).
Uso: python -m metodo.v19.tendencia_cripto   (desde la raíz del repo)"""
from __future__ import annotations
import glob, os, sys
import numpy as np, pandas as pd
from metodo.embudo import embudo, t_agrupado, t_requerido
from metodo.sinteticos import velas_paseo, sin_fuga

DAT = "metodo/v4/datos"
CORTE = "2023-01-01"
LUGARES = {  # coste por lado (fracción del nocional), swap largo %/año
    "exchange": (0.0010, 0.00),
    "dz_cfd": (0.0008, 0.20),
    "ftmo": (0.0005, 0.25),
}
N_PRUEBAS = 15


def cargar(patron, excluir_bn=False):
    velas = {}
    for f in sorted(glob.glob(os.path.join(DAT, patron))):
        nom = os.path.basename(f).replace("_spot1d.csv.gz", "").replace("bn_", "")
        if excluir_bn and os.path.basename(f).startswith("bn_"):
            continue
        d = pd.read_csv(f)
        t = d.open_time.astype("int64")
        t = np.where(t > 1e14, t // 1000, t)  # Binance pasó a microsegundos en 2025
        d.index = pd.to_datetime(t, unit="ms").normalize()
        d = d[~d.index.duplicated()][["open", "high", "low", "close"]].astype(float)
        d = d[(d > 0).all(axis=1)]
        if len(d) > 120:
            velas[nom] = d
    return velas


def senal(velas, look=28):
    """Señal de cada día con datos hasta ese cierre: rendimiento de `look` días."""
    c = velas["close"]
    return np.sign(c / c.shift(look) - 1)


def backtest(velas_dict, look=28, coste=0.001, swap=0.0, largo_corto=False, mascara=None, rng=None, p_largo=None):
    """Devuelve DataFrame de operaciones (moneda-semana con posición)."""
    filas = []
    for nom, v in velas_dict.items():
        c = v["close"]
        dias = pd.date_range(c.index[0], c.index[-1], freq="D")
        c = c.reindex(dias).ffill()
        lr = np.log(c).diff()
        sig = np.sign(c / c.shift(look) - 1)
        vol = lr.rolling(30, min_periods=25).std() * np.sqrt(7)
        domingos = c.index[(c.index.dayofweek == 6)]
        domingos = domingos[domingos >= c.index[0] + pd.Timedelta(days=60)]
        domingos = domingos[domingos + pd.Timedelta(days=7) <= c.index[-1]]
        if len(domingos) < 10:
            continue
        s = sig.loc[domingos].to_numpy()
        if not largo_corto:
            s = np.where(s > 0, 1.0, 0.0)
        if rng is not None:  # placebo: misma probabilidad de estar dentro, momento al azar
            p = p_largo[nom]
            s = (rng.random(len(domingos)) < p).astype(float)
        sg = vol.loc[domingos].to_numpy()
        ok = np.isfinite(sg) & (sg > 0) & np.isfinite(s)
        N = np.where(ok, s / np.where(ok, sg, 1), 0.0)
        ret = (c.shift(-7).loc[domingos] / c.loc[domingos] - 1).to_numpy()
        prev = np.concatenate([[0.0], N[:-1]])
        sig_ = np.concatenate([N[1:], [0.0]])
        entrada = np.abs(N - prev) * coste
        salida = np.where(sig_ == 0, np.abs(N), 0.0) * coste  # cierre completo se carga aquí
        sw = np.abs(N) * 7 * swap / 365
        for i in np.flatnonzero(N != 0):
            filas.append((domingos[i] + pd.Timedelta(days=7), nom, N[i] * ret[i], entrada[i] + salida[i] + sw[i], N[i] > 0))
    ops = pd.DataFrame(filas, columns=["fecha", "moneda", "r_bruto", "coste_r", "largo"])
    return ops.sort_values("fecha").reset_index(drop=True)


def resumen(ops, nombre):
    n = ops.r_bruto - ops.coste_r
    g = ops.fecha.dt.to_period("W").astype(str).to_numpy()
    d = ops.fecha < pd.Timestamp(CORTE)
    print(f"{nombre:38s} ops {len(ops):5d} bruto {ops.r_bruto.mean():+.3f} coste {ops.coste_r.mean():.3f} neto {n.mean():+.3f} "
          f"t {t_agrupado(n.to_numpy(), g):5.2f} | ajuste {n[d].mean():+.3f} t {t_agrupado(n[d].to_numpy(), g[d]):5.2f} "
          f"| OOS {n[~d].mean():+.3f} t {t_agrupado(n[~d].to_numpy(), g[~d]):5.2f}")


def main():
    V = cargar("bn_*_spot1d.csv.gz")
    R = cargar("*_spot1d.csv.gz", excluir_bn=True)
    print(f"Universo principal {len(V)} monedas; réplica {len(R)} monedas")
    # lookahead
    sf = sin_fuga(lambda v: senal(v), V["BTC"])
    print("sin_fuga BTC:", sf["detalle"])

    base = backtest(V, coste=0.0)
    p_largo = {}
    for nom, v in V.items():
        tot = backtest({nom: v}, coste=0.0, largo_corto=True)
        p_largo[nom] = (tot.largo.mean() if len(tot) else 0.5)
    print("Fracción de semanas compradas por moneda:", {k: round(x, 2) for k, x in p_largo.items()})

    # Comprar-y-mantener con el mismo tamaño (beta) para comparar
    siempre = backtest(V, coste=0.0, rng=np.random.default_rng(0), p_largo={k: 1.0 for k in V})
    resumen(siempre, "Siempre comprado (beta, bruto)")
    resumen(base, "Principal 28 d (bruto)")

    def placebo(sem):
        return backtest(V, coste=0.0, rng=np.random.default_rng(1000 + sem), p_largo=p_largo).r_bruto.to_numpy()

    def paseo(sem):
        Vp = {k: velas_paseo(v, semilla=sem * 100 + i, por_minuto=False) for i, (k, v) in enumerate(V.items())}
        return backtest(Vp, coste=0.0).r_bruto.to_numpy()

    print("\nPor año (bruto R/op, ops):")
    print(base.groupby(base.fecha.dt.year).r_bruto.agg(["mean", "size", "sum"]).round(3).T.to_string())
    print("\nPor moneda (bruto R/op):")
    print(base.groupby("moneda").r_bruto.agg(["mean", "size"]).round(3).T.to_string())

    resultados = {}
    for lugar, (c, sw) in LUGARES.items():
        ops = backtest(V, coste=c, swap=sw)
        print(f"\n===== {lugar}: coste {c*100:.2f} %/lado, swap {sw*100:.0f} %/año =====")
        resumen(ops, "principal 28 d")
        sin_sw = backtest(V, coste=c, swap=0.0)
        swap_r_por_unidad = (ops.coste_r.mean() - sin_sw.coste_r.mean()) / sw if sw else np.nan
        if sw:
            eq = (sin_sw.r_bruto.mean() - sin_sw.coste_r.mean()) / swap_r_por_unidad
            print(f"swap de equilibrio (neto = 0): {eq*100:.1f} %/año")
        res = embudo(ops[["fecha", "r_bruto", "coste_r"]].copy(), N_PRUEBAS, CORTE,
                     placebo=placebo if lugar == "exchange" else None,
                     paseo=paseo if lugar == "exchange" else None,
                     familia="v19_tendencia_cripto", regla={"look": 28, "lugar": lugar, "universo": "bn20"})
        print(res)
        resultados[lugar] = ops

    print("\n===== Meseta y variantes (exchange) =====")
    c, sw = LUGARES["exchange"]
    for look in (22, 34):
        o = backtest(V, look=look, coste=c, swap=sw)
        resumen(o, f"lookback {look} d")
        embudo(o[["fecha", "r_bruto", "coste_r"]].copy(), N_PRUEBAS, CORTE, familia="v19_tendencia_cripto",
               regla={"look": look, "lugar": "exchange", "universo": "bn20"})
    lc = backtest(V, coste=c, swap=sw, largo_corto=True)
    resumen(lc, "comprado/vendido 28 d")
    resumen(lc[~lc.largo], "  solo patas vendidas")
    embudo(lc[["fecha", "r_bruto", "coste_r"]].copy(), N_PRUEBAS, CORTE, familia="v19_tendencia_cripto",
           regla={"look": 28, "lugar": "exchange", "universo": "bn20", "lado": "ls"})

    print("\n===== Réplica: otro universo =====")
    rep = backtest(R, coste=c, swap=sw)
    rep0 = backtest(R, coste=0.0)
    resumen(rep0, "réplica bruto")
    resumen(rep, "réplica neto exchange")
    p_rep = {}
    for nom, v in R.items():
        tot = backtest({nom: v}, coste=0.0, largo_corto=True)
        p_rep[nom] = tot.largo.mean() if len(tot) else 0.5
    med = [backtest(R, coste=0.0, rng=np.random.default_rng(5000 + s), p_largo=p_rep).r_bruto.mean() for s in range(100)]
    print(f"réplica bruto {rep0.r_bruto.mean():+.3f} vs placebo p50 {np.median(med):+.3f} p95 {np.percentile(med, 95):+.3f}")
    print(rep0.groupby(rep0.fecha.dt.year).r_bruto.agg(["mean", "size"]).round(3).T.to_string())
    embudo(rep[["fecha", "r_bruto", "coste_r"]].copy(), N_PRUEBAS, CORTE, familia="v19_tendencia_cripto",
           regla={"look": 28, "lugar": "exchange", "universo": "replica"})

    # Correlación y DARWIN (mensual)
    print("\n===== Correlación y aporte al DARWIN (mensual) =====")
    m = pd.read_csv("darwinex/reversion_dz/mensual_orb_reversion.csv", index_col=0, parse_dates=True)
    for lugar in ("exchange", "dz_cfd"):
        o = resultados[lugar]
        x = (o.r_bruto - o.coste_r).groupby(o.fecha.dt.to_period("M")).sum()
        x.index = x.index.to_timestamp("M")
        j = pd.concat([m, x.rename("cripto")], axis=1).dropna()
        sr = lambda s: s.mean() / s.std() * np.sqrt(12)
        mix = j.mezcla / j.mezcla.std() + j.cripto / j.cripto.std()
        mejor = max(((a, sr(a * j.mezcla / j.mezcla.std() + (1 - a) * j.cripto / j.cripto.std())) for a in np.linspace(0, 1, 21)),
                    key=lambda z: z[1])
        print(f"{lugar}: meses {len(j)} corr ORB {j.orb.corr(j.cripto):+.2f} corr reversión {j.rev.corr(j.cripto):+.2f} | "
              f"SR ORB+rev {sr(j.mezcla):.2f} cripto {sr(j.cripto):.2f} igual riesgo {sr(mix):.2f} "
              f"mejor peso ORB+rev {mejor[0]:.2f} → {mejor[1]:.2f}")
        h = j.index >= CORTE
        print(f"   solo 2023+: SR ORB+rev {sr(j.mezcla[h]):.2f} cripto {sr(j.cripto[h]):.2f} igual riesgo "
              f"{sr((j.mezcla / j.mezcla.std() + j.cripto / j.cripto.std())[h]):.2f}")
    print(f"\nt_requerido({N_PRUEBAS}) = {t_requerido(N_PRUEBAS):.2f}")


if __name__ == "__main__":
    main()
