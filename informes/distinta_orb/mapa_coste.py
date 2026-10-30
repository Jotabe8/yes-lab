# Mapa del coste: cuánto pesa el spread frente al movimiento disponible, por mercado, hora de entrada y duración.
# coste relativo = spread (pb) / movimiento medio absoluto (pb) entre la entrada y la salida.
# Es la fracción del movimiento que una señal tiene que acertar "de más" solo para empatar.
import pandas as pd, numpy as np
MERC = ["US100", "US500", "US30", "US2000", "GER40", "UK100", "FRA40", "EU50", "JP225", "XAUUSD", "USOIL"]
H = {"30m": 1, "2h": 4}
filas = []
for k in MERC:
    b = pd.read_pickle(f"b30_{k}.pkl")
    b = b[(b.index >= "2023-01-01") & (b.index.dayofweek < 5)]
    sp = b.spread / b.close * 1e4
    hh = b.index.strftime("%H:%M")
    dia = b.index.normalize()
    # cierre del día de servidor (última barra hasta las 23:00) para "hasta el cierre"
    ult = b[b.index.hour < 23].groupby(dia[b.index.hour < 23]).close.last()
    cierre = ult.reindex(dia).values
    for nom, n in H.items():
        fut = b.close.shift(-n + 1)
        mismo = pd.Series(dia, index=b.index).shift(-n + 1) == dia
        mov = ((fut / b.open - 1).abs() * 1e4).where(mismo)
        t = pd.DataFrame({"h": hh, "sp": sp.values, "mov": mov.values})
        g = t.groupby("h").agg(sp=("sp", "median"), mov=("mov", "mean"))
        for h, r in g.iterrows():
            filas.append(dict(mercado=k, hora=h, horizonte=nom, spread_pb=r.sp, mov_pb=r.mov, coste_rel=r.sp / r.mov))
    mov = (pd.Series(cierre, index=b.index) / b.open - 1).abs() * 1e4
    t = pd.DataFrame({"h": hh, "sp": sp.values, "mov": mov.values})
    for h, r in t.groupby("h").agg(sp=("sp", "median"), mov=("mov", "mean")).iterrows():
        filas.append(dict(mercado=k, hora=h, horizonte="cierre", spread_pb=r.sp, mov_pb=r.mov, coste_rel=r.sp / r.mov))
    # diario: de cierre a cierre (para cuentas sin swap)
    d = b.close.groupby(dia).last()
    filas.append(dict(mercado=k, hora="D1", horizonte="1 día", spread_pb=sp.median(),
                      mov_pb=(d.pct_change().abs() * 1e4).mean(), coste_rel=sp.median() / (d.pct_change().abs() * 1e4).mean()))
df = pd.DataFrame(filas)
df.to_csv("mapa_coste.csv", index=False)
pd.set_option("display.width", 200)
# mejor hora por mercado y horizonte (solo horas con spread razonable)
for hz in ["30m", "2h", "cierre", "1 día"]:
    x = df[df.horizonte == hz]
    x = x[x.mov_pb > 0]
    best = x.loc[x.groupby("mercado").coste_rel.idxmin()].sort_values("coste_rel")
    print(f"\n== Horizonte {hz}: mejor hora de entrada por mercado (2023-26, hora servidor)")
    print(best[["mercado", "hora", "spread_pb", "mov_pb", "coste_rel"]].round(3).to_string(index=False))
print("\n== US100 y GER40 por hora, horizonte 2h")
x = df[(df.horizonte == "2h") & df.mercado.isin(["US100", "GER40", "XAUUSD"])]
print(x.pivot(index="hora", columns="mercado", values="coste_rel").round(3).to_string())
