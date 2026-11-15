"""v10: descarga de Databento con tope de coste (15-11-2026).

Uso: python descargar_databento.py coste|bajar  (necesita DATABENTO_API_KEY).
- coste: pide a la API el precio de cada bloque (gratis) y lo imprime.
- bajar: si el total <= TOPE, baja y reduce a features diarias pequeñas en metodo/v10/datos/.
"""
import os, sys, datetime as dt
import numpy as np, pandas as pd, databento as db

TOPE = float(os.environ.get("TOPE_USD", "100"))
INI, FIN = "2018-05-01", "2026-11-14"
ACC = ["QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "AVGO", "GOOGL", "TSLA"]
OUT = os.path.join(os.path.dirname(__file__), "datos"); os.makedirs(OUT, exist_ok=True)
NY = "America/New_York"
cli = db.Historical(os.environ["DATABENTO_API_KEY"])


def dias():
    d = pd.bdate_range(INI, FIN, freq="C", holidays=[])
    return [x for x in d if x.weekday() < 5]


def ventana(d, h0, m0, h1, m1):
    a = pd.Timestamp(d.year, d.month, d.day, h0, m0, tz=NY).tz_convert("UTC")
    b = pd.Timestamp(d.year, d.month, d.day, h1, m1, tz=NY).tz_convert("UTC")
    return a.isoformat(), b.isoformat()


def costes():
    c = {}
    c["imbalance XNAS"] = cli.metadata.get_cost(dataset="XNAS.ITCH", schema="imbalance", symbols=ACC,
                                                 start=INI, end=FIN)
    c["ohlcv-1m NQ"] = cli.metadata.get_cost(dataset="GLBX.MDP3", schema="ohlcv-1m", symbols=["NQ.v.0"],
                                             stype_in="continuous", start=INI, end=FIN)
    muestra = dias()[::200]
    s = sum(cli.metadata.get_cost(dataset="GLBX.MDP3", schema="trades", symbols=["NQ.v.0"], stype_in="continuous",
                                  start=ventana(d, 9, 30, 9, 40)[0], end=ventana(d, 9, 30, 9, 40)[1]) for d in muestra)
    c["trades NQ 9:30-9:40 (estimado)"] = s / len(muestra) * len(dias())
    for k, v in c.items():
        print(f"{k:35s} {v:8.2f} $")
    tot = sum(c.values()); print(f"{'TOTAL':35s} {tot:8.2f} $  (tope {TOPE} $)")
    return tot


def bajar_imbalance():
    df = cli.timeseries.get_range(dataset="XNAS.ITCH", schema="imbalance", symbols=ACC, start=INI, end=FIN).to_df()
    df = df.reset_index(); df["t"] = pd.to_datetime(df["ts_recv"]).dt.tz_convert(NY)
    df["fecha"] = df.t.dt.date; hm = df.t.dt.hour * 100 + df.t.dt.minute
    lado = df.side.map({"B": 1, "A": -1}).fillna(0)
    df["imb_usd"] = lado * df.total_imbalance_qty * df.ref_price; df["par_usd"] = df.paired_qty * df.ref_price
    ape = df[(hm >= 925) & (hm < 930)].sort_values("t").groupby(["fecha", "symbol"]).tail(1)
    ape = ape[ape.t.dt.hour * 100 + ape.t.dt.minute >= 929]
    cie = df[(hm >= 1550) & (hm < 1600)].sort_values("t").groupby(["fecha", "symbol"]).head(1)
    cie = cie[cie.t.dt.hour * 100 + cie.t.dt.minute == 1550]
    for nom, x in (("apertura", ape), ("cierre", cie)):
        x[["fecha", "symbol", "t", "side", "total_imbalance_qty", "paired_qty", "ref_price", "imb_usd", "par_usd"]] \
            .to_csv(f"{OUT}/imbalance_{nom}.csv.gz", index=False)
        print(nom, len(x), "filas")


def bajar_ohlcv():
    df = cli.timeseries.get_range(dataset="GLBX.MDP3", schema="ohlcv-1m", symbols=["NQ.v.0"], stype_in="continuous",
                                  start=INI, end=FIN).to_df().reset_index()
    df["t"] = pd.to_datetime(df["ts_event"]).dt.tz_convert(NY)
    df[["t", "open", "high", "low", "close", "volume"]].to_csv(f"{OUT}/nq_m1.csv.gz", index=False)
    print("ohlcv", len(df))


def bajar_trades():
    filas = []
    for d in dias():
        a, b = ventana(d, 9, 30, 9, 40)
        try:
            x = cli.timeseries.get_range(dataset="GLBX.MDP3", schema="trades", symbols=["NQ.v.0"],
                                         stype_in="continuous", start=a, end=b).to_df()
        except Exception as e:  # festivos o días sin datos
            continue
        if x.empty:
            continue
        t = pd.to_datetime(x.index).tz_convert(NY); m5 = (t.minute < 35)
        comp = x["size"].where(x.side == "B", 0); vend = x["size"].where(x.side == "A", 0)
        filas.append(dict(fecha=d.date(), vol=x["size"].sum(), compra=comp.sum(), venta=vend.sum(),
                          vol5=x["size"][m5].sum(), compra5=comp[m5].sum(), venta5=vend[m5].sum()))
    pd.DataFrame(filas).to_csv(f"{OUT}/nq_delta_0930_0940.csv", index=False); print("trades", len(filas), "días")


if __name__ == "__main__":
    print(cli.metadata.get_dataset_range(dataset="XNAS.ITCH"))
    tot = costes()
    if sys.argv[1:] == ["bajar"]:
        if tot > TOPE:
            sys.exit(f"Coste {tot:.2f} $ por encima del tope {TOPE} $: no se baja nada.")
        bajar_imbalance(); bajar_ohlcv(); bajar_trades()
