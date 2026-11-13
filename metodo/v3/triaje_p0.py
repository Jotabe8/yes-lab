"""P0 v3: triaje aritmético antes de tocar datos. Cada idea se puntúa con números que ya existen
(literatura, pruebas previas, costes del lugar más barato operable). Se descarta sin datos si falla
cualquiera de estas tres cuentas:
  1. Potencia: años necesarios para ver el edge NETO con 80 % de probabilidad (t >= 2,4)
     = ((2,4 + 0,84) * sigma / mu_neto)^2 / ops_año  <=  años de historia limpia disponibles.
  2. Margen: mu_bruto >= 2 * coste en el lugar más barato operable.
  3. Valor: ops_año * mu_neto >= 8 R/año (un tercio de lo que da el ORB US100: ~25 R/año).
mu_bruto es la estimación previa ENCOGIDA a la mitad si viene de un artículo (los efectos publicados
caen ~50 % tras publicarse, McLean y Pontiff 2016); si viene de nuestra propia prueba, se usa tal cual.
"""
import pandas as pd
SIG = 1.8   # sigma de R por operación con pago convexo (ORB real); para salidas fijas sin stop usar 1,0
ideas = [
    # nombre, ops/año, mu_bruto (R), coste en el lugar más barato (R), sigma, años de historia limpia, fuente
    ("Deriva pre-FOMC (US500, 24 h antes)", 8, 0.5 * 0.35, 0.02, 1.0, 15, "Lucca-Moench +0,49 % 1994-2011; ~0 después de 2011"),
    ("Víspera de festivo en futuros ES", 9, 0.044, 0.01, 1.0, 25, "nuestra prueba 2026-10-30"),
    ("Gotobi en futuros 6J", 70, 0.106, 0.06, 1.0, 14, "nuestra prueba; 6J 1 tick 1,25 pb ≈ CFD"),
    ("ORB Tokio en futuros NKD", 220, 0.159, 0.10, SIG, 14, "nuestra prueba (CFD coste 0,126 R); NKD tick 5 pts ≈ 0,08 R + tasas"),
    ("OPEX seguir la mañana", 12, 0.10, 0.02, 1.0, 14, "post hoc 13-11; 12 ops/año"),
    ("ORB cripto en futuros CME estándar (BTC+ETH)", 250, 0.20, 0.035, SIG, 5, "nuestra prueba 2024-26 bruto ~0,2 R; BTC 5 BTC / ETH 50 ETH"),
]
filas = []
for n, ops, mb, c, s, hist, fuente in ideas:
    mn = mb - c
    años = ((2.4 + 0.84) * s / mn) ** 2 / ops if mn > 0 else float("inf")
    filas.append(dict(idea=n, ops_año=ops, bruto=mb, coste=c, neto=round(mn, 3),
                      años_necesarios=round(años, 1), historia=hist, R_año=round(ops * mn, 1),
                      potencia="sí" if años <= hist else "NO", margen="sí" if mb >= 2 * c else "NO",
                      valor="sí" if ops * mn >= 8 else "NO", fuente=fuente))
t = pd.DataFrame(filas); t["pasa_P0"] = (t[["potencia", "margen", "valor"]] == "sí").all(axis=1).map({True: "PASA", False: "fuera"})
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
print(t.drop(columns="fuente").to_string(index=False)); t.to_csv("triaje_p0.csv", index=False, sep=";")
