"""Prima nocturna en futuros de índices US (preregistro PREREGISTRO_NOCHE_FUTUROS.md).
Uso: python noche_futuros.py [serie_orb.csv]"""
import sys, os
import numpy as np, pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
TB = {2011: .05, 2012: .09, 2013: .06, 2014: .03, 2015: .05, 2016: .32, 2017: .93, 2018: 1.94, 2019: 2.06,
      2020: .36, 2021: .04, 2022: 2.02, 2023: 5.07, 2024: 4.97, 2025: 4.2, 2026: 3.8}
DIV = {"US500": 1.8, "US100": 0.8, "US30": 2.0}
COSTE = {"US500": 0.6, "US100": 0.3, "US30": 0.5}  # pb ida y vuelta


def cargar(s):
    a = pd.read_csv(f"{D}/{s}_2012.csv", parse_dates=["fecha"])
    b = pd.read_csv(f"{D}/{s}.csv", parse_dates=["fecha"])
    df = pd.concat([a[a.fecha < "2018-01-01"], b]).drop_duplicates("fecha").sort_values("fecha").set_index("fecha")
    df = df.dropna(subset=["o930", "p1555"])
    df = df[df.index.dayofweek < 5]
    return df


def piernas(s):
    df = cargar(s)
    dias = pd.Series(df.index, index=df.index).diff().dt.days.shift(-1)  # noches hasta la siguiente sesión
    rf = np.array([TB[y] for y in df.index.year]) / 100
    carry = (DIV[s] / 100 - rf) / 365
    noche = df.o930.shift(-1) / df.p1555 - 1 + carry * dias
    dia = df.p1555 / df.o930 - 1
    out = pd.DataFrame({"noche": noche, "dia": dia}).dropna()
    # filtro de datos malos: saltos nocturnos > 8 % se revisan aparte
    malos = out[out.noche.abs() > 0.08]
    if len(malos):
        print(s, "noches > 8 %:", [(str(i.date()), round(v * 100, 1)) for i, v in malos.noche.items()])
    out["neto"] = out.noche - COSTE[s] / 1e4
    out["neto2"] = out.noche - 2 * COSTE[s] / 1e4
    out["bh"] = out.noche + out.dia  # siempre comprado (aprox. suma de piernas)
    return out


def sh(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(252), x.mean() / x.std() * np.sqrt(len(x))


P = {s: piernas(s) for s in DIV}
print("\nPor mercado (Sharpe anual, t) 2011-09 → 2026-11")
for s, p in P.items():
    f = lambda c: "%.2f (t %.1f)" % sh(p[c])
    print(f"{s:6s} n={len(p):5d} noche bruta {p.noche.mean()*1e4:5.2f} pb/día | neto {f('neto')} | costes x2 {f('neto2')} "
          f"| intradía {f('dia')} | siempre comprado {f('bh')}")

C = pd.concat({s: p for s, p in P.items()}, axis=1)
cart = {c: C.xs(c, axis=1, level=1).mean(axis=1) for c in ["noche", "neto", "neto2", "dia", "bh"]}
cart = pd.DataFrame(cart)
mitad = cart.index[len(cart) // 2]
print("\nCARTERA (principal)")
for c in cart:
    sr, t = sh(cart[c])
    print(f"  {c:6s} media {cart[c].mean()*1e4:5.2f} pb/día  anual {cart[c].mean()*252*100:5.1f} %  Sharpe {sr:.2f}  t {t:.2f}")
print("  1ª mitad neto Sharpe %.2f | 2ª mitad (desde %s) Sharpe %.2f, media %.2f pb" % (
    sh(cart.neto[:mitad])[0], mitad.date(), sh(cart.neto[mitad:])[0], cart.neto[mitad:].mean() * 1e4))
print("  máx. caída neto (suma simple) %.1f %%" % ((cart.neto.cumsum() - cart.neto.cumsum().cummax()).min() * 100))
print("\nPor año, cartera neta (% y Sharpe) vs siempre comprado")
for y, g in cart.groupby(cart.index.year):
    print(f"  {y}: noche {g.neto.sum()*100:6.1f} % SR {sh(g.neto)[0]:5.2f} | siempre comprado {g.bh.sum()*100:6.1f} % SR {sh(g.bh)[0]:5.2f} | intradía {g.dia.sum()*100:6.1f} %")
cart.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "noche_cartera_diaria.csv"), float_format="%.6g")

# Criterio 5: mezcla con el ORB US100 a igual riesgo (mensual 2018-26)
if len(sys.argv) > 1:
    s = pd.read_csv(sys.argv[1], parse_dates=["d"]).set_index("d")
    o = (s.Rbe - 0.05).resample("ME").sum()
    o = o["2018-01":"2026-10"]
    def mezcla(x):
        xm = x.resample("ME").sum().reindex(o.index).fillna(0)
        m = o + xm * (o.std() / xm.std())
        m = m * (o.std() / m.std())
        return m.mean() / m.std() * np.sqrt(12), np.corrcoef(o, xm)[0, 1], xm.mean() / xm.std() * np.sqrt(12)
    sr0 = o.mean() / o.std() * np.sqrt(12)
    print(f"\nORB US100 solo, Sharpe mensual 2018-26: {sr0:.2f}")
    for nom, x in [("noche neto", cart.neto), ("siempre comprado", cart.bh), ("intradía", cart.dia)]:
        srm, cr, srx = mezcla(x)
        print(f"  + {nom:16s}: Sharpe mezcla {srm:.2f} (sube {srm-sr0:+.2f}) | corr mensual {cr:+.2f} | Sharpe propio {srx:.2f}")
