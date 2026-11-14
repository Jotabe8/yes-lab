"""Auditoría 1: ftmo_2step remuestrea días i.i.d. ¿Cambia el EV si se respetan rachas (bloques de días)?"""
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
import metodo.embudo as E

s = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv", parse_dates=["d"]).set_index("d").R
r = s.to_numpy()
print("ORB v018: días", len(r), "media", r.mean().round(3), "autocorr |R| lag1", np.corrcoef(abs(r[1:]), abs(r[:-1]))[0,1].round(3),
      "autocorr R lag1", np.corrcoef(r[1:], r[:-1])[0,1].round(3))

def ftmo_bloques(r_dia, B, riesgo=0.01, cuota=540, capital=100_000, n=4000, semilla=0):
    rng = np.random.default_rng(semilla); N = len(r_dia)
    def flujo():
        while True:
            i = rng.integers(N)
            for k in range(B):
                yield r_dia[(i + k) % N]
    pasa, cobros = 0, np.zeros(n)
    for j in range(n):
        g = flujo(); ok = True
        for obj in (0.10, 0.05):
            eq, dias = 0.0, 0
            while True:
                d = next(g) * riesgo; dias += 1
                if d <= -0.05 or eq + d <= -0.10 or dias > 750: ok = False; break
                eq += d
                if eq >= obj and dias >= 4: break
            if not ok: break
        if not ok: continue
        pasa += 1; eq, tot, dev = 0.0, 0.0, False
        for _ in range(12):
            q = False
            for _ in range(21):
                d = next(g) * riesgo
                if d <= -0.05 or eq + d <= -0.10: q = True; break
                eq += d
            if q: break
            if eq > 0: tot += eq * capital * 0.8 + (0 if dev else cuota); dev, eq = True, 0.0
        cobros[j] = tot
    return pasa / n, cobros.mean() - cuota

for riesgo in (0.01, 0.02):
    for B in (1, 5, 21, 63):
        p, ev = ftmo_bloques(r, B, riesgo=riesgo)
        p0, ev0 = ftmo_bloques(r - r.mean(), B, riesgo=riesgo)
        print(f"riesgo {riesgo:.0%} bloque {B:>2}: p pasar {p:.0%} EV {ev:+7.0f} € | control media 0: p {p0:.0%} EV {ev0:+6.0f} €")
