"""T0 v9 (tanda 1): triaje aritmético de familias nuevas, misma fórmula que metodo/v3/triaje_p0.py.
mu_bruto en R; si viene de un artículo, ya encogido a la mitad. sigma 1,0 para salidas fijas sin stop,
1,8 para pago convexo con stop corto."""
import pandas as pd
ideas = [
 ("Ruptura en el dato programado (NFP/IPC/FOMC, 6 mercados)", 150, 0.20, 0.04, 1.8, 15, "sin artículo; análogo al ORB en días de información máxima; ops correlacionadas (~100 indep.)"),
 ("Prima del día de anuncio macro (Savor-Wilson) intradía", 36, 0.5*0.10, 0.01, 1.0, 15, "11 pb/día vs σ 110 pb 1958-2009"),
 ("Subasta del Tesoro 13:00 en futuros ZN (DZ)", 150, 0.40, 0.35, 1.0, 15, "concesión ~0,5 pb de rendimiento ≈ 3 pb precio vs coste 2,2 pb"),
 ("Reacción del US100 a la subasta de 10/30 años", 24, 0.03, 0.01, 1.0, 15, "sin artículo; efecto en acciones mínimo"),
 ("Día de la semana / lunes (French 1980) intradía", 250, 0.5*0.02, 0.01, 1.0, 15, "efecto desaparecido tras 1987"),
 ("Quincena / día de paga (día 15) intradía", 24, 0.5*0.10, 0.01, 1.0, 15, "Lakonishok-Smidt; cambio de mes ya t 0,2"),
 ("Sol en Nueva York (Hirshleifer-Shumway 2003)", 250, 0.5*0.03, 0.01, 1.0, 15, "~3 pb/día de diferencia"),
 ("Ciclo lunar (Yuan-Zheng-Zhu 2006)", 250, 0.5*0.02, 0.01, 1.0, 15, "3-5 %/año entre fases"),
 ("Liquidación VIX (miércoles) en US500", 12, 0.5*0.20, 0.01, 1.0, 15, "Griffin-Shams 2018; 12 ops"),
 ("Hueco de fin de semana BTC vs CME (folklore 'se cierra')", 52, 0.05, 0.05, 1.0, 9, "coste CFD cripto 0,15 % ida y vuelta"),
 ("Prima Coinbase/Kimchi como dirección BTC", 250, 0.03, 0.05, 1.0, 8, "folklore; coste ≈ efecto"),
 ("Emisiones de Tether (Griffin-Shams 2020)", 50, 0.5*0.10, 0.05, 1.0, 8, "efecto de 2017-18"),
 ("Estacionalidad transversal materias primas (Keloharju 2016) DZ", 12, 0.5*0.25, 0.01, 1.0, 26, "SR mensual publicado ~0,5 anual"),
 ("Almacén de gas EIA jueves 10:30 (NG en DZ)", 52, 0.05, 0.03, 1.8, 15, "Gay et al. 2009: incorporación rápida"),
 ("Liquidez neta Fed (TGA/RRP) → US500 día siguiente", 250, 0.02, 0.01, 1.0, 10, "folklore"),
 ("Put/call CBOE contrario → US500 intradía", 250, 0.5*0.04, 0.01, 1.0, 15, "Pan-Poteshman es de acciones"),
 ("Flujos NISA a principio de mes → USDJPY", 24, 0.10, 0.03, 1.0, 2, "desde 2024"),
 ("Compras de ETF del BoJ (tarde JP225 tras mañana < −0,5 %)", 40, 0.20, 0.09, 1.0, 0, "terminaron en marzo de 2024: no operable"),
]
f = []
for n, ops, mb, c, s, hist, fu in ideas:
    mn = mb - c
    años = ((2.4 + 0.84) * s / mn) ** 2 / ops if mn > 0 else float("inf")
    f.append(dict(idea=n, ops_año=ops, bruto=round(mb, 3), coste=c, neto=round(mn, 3), años_necesarios=round(años, 1),
                  historia=hist, R_año=round(ops * mn, 1), potencia="sí" if años <= hist else "NO",
                  margen="sí" if mb >= 2 * c else "NO", valor="sí" if ops * mn >= 8 else "NO", fuente=fu))
t = pd.DataFrame(f); t["T0"] = (t[["potencia", "margen", "valor"]] == "sí").all(axis=1).map({True: "PASA", False: "fuera"})
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 58)
print(t.drop(columns="fuente").to_string(index=False)); t.to_csv("T0_tanda1.csv", index=False, sep=";")
