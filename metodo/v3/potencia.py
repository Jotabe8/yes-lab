"""Potencia del embudo: ¿con qué probabilidad sobrevive un edge REAL a nuestras puertas?

Se simulan series de R con la forma del ORB v018 real (asimetría, colas, 31 % de aciertos):
se remuestrean las R del ORB centradas y se les suma un edge verdadero mu. Se comparan:
  v1: embudo actual -> ajuste 5 años con t >= 2 y >= 60 % de años +, luego OOS 3,8 años con media > 0 y t >= 1
  v3: hipótesis preregistrada (<= 3 variantes) -> toda la historia (11 años) t >= 2,4, y la mitad final > 0
  v3m: igual, pero el mismo mecanismo agrupado en 3 mercados (correlación 0,3 entre ellos)
Falsos positivos: mu = 0 y se elige la mejor de k variantes independientes.
"""
import numpy as np, pandas as pd
rng = np.random.default_rng(7)
R = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv").R.values
R0 = R - R.mean()                    # forma del ORB sin edge
OPS = 210                            # operaciones por año (ORB)

def serie(mu, años, n=OPS):
    return rng.choice(R0, size=(int(años * n),)) + mu

def t(x): return x.mean() / x.std(ddof=1) * np.sqrt(len(x))

def v1(mu, n=OPS):
    a = serie(mu, 5, n); o = serie(mu, 3.8, n)
    yrs = np.array_split(a, 5)
    return t(a) >= 2 and np.mean([y.mean() > 0 for y in yrs]) >= .6 and o.mean() > 0 and t(o) >= 1

def v3(mu, n=OPS, años=11, mercados=1, rho=.3):
    m = int(años * n)
    if mercados == 1:
        x = serie(mu, años, n)
    else:   # media de varios mercados con correlación rho (factor común)
        com = rng.choice(R0, m); xs = [np.sqrt(rho) * com + np.sqrt(1 - rho) * rng.choice(R0, m) + mu for _ in range(mercados)]
        x = np.mean(xs, axis=0)
    return t(x) >= 2.4 and x[m // 2:].mean() > 0

def tasa(f, sims=2000, **kw): return np.mean([f(**kw) for _ in range(sims)])

def mejor_de_k(f_is, k):
    """falso positivo: k variantes sin edge, se elige la de mayor t en ajuste"""
    return f_is(k)

def fp_v1(k, n=OPS):
    best = max((serie(0, 5, n) for _ in range(k)), key=t)
    yrs = np.array_split(best, 5); o = serie(0, 3.8, n)
    return t(best) >= 2 and np.mean([y.mean() > 0 for y in yrs]) >= .6 and o.mean() > 0 and t(o) >= 1

def fp_v3(k, n=OPS):
    best = max((serie(0, 11, n) for _ in range(k)), key=t)
    return t(best) >= 2.4 and best[len(best) // 2:].mean() > 0

if __name__ == "__main__":
    filas = []
    for mu in (0.05, 0.08, 0.10, 0.12, 0.15, 0.20):
        filas.append({"edge real (R/op)": mu,
                      "v1 actual": tasa(v1, mu=mu),
                      "v1 con 12 ops/año": tasa(v1, mu=mu, n=12),
                      "v3 11 años": tasa(v3, mu=mu),
                      "v3 11 años, 3 mercados": tasa(v3, mu=mu, mercados=3),
                      "v3 con 12 ops/año": tasa(v3, mu=mu, n=12)})
    p = pd.DataFrame(filas).round(2)
    print("Probabilidad de que un edge REAL pase las puertas (forma de R del ORB, sigma 1,8 R)")
    print(p.to_string(index=False))
    fp = pd.DataFrame([{"variantes miradas": k, "v1 falso positivo": tasa(fp_v1, sims=1000, k=k),
                        "v3 falso positivo": tasa(fp_v3, sims=1000, k=k)} for k in (1, 3, 10, 30)]).round(3)
    print("\nFalsos positivos (sin edge, se elige la mejor de k variantes)")
    print(fp.to_string(index=False))
    sd = R.std(ddof=1)
    print("\nOperaciones necesarias para ver un edge con 80 % de probabilidad (t >= 2,4): n = ((2,4+0,84) sigma / mu)^2, sigma =", round(sd, 2))
    for mu in (0.05, 0.10, 0.15, 0.20, 0.30):
        n = ((2.4 + .84) * sd / mu) ** 2
        print(f"  mu {mu:.2f} R -> {n:7.0f} ops = {n/210:5.1f} años a 210 ops/año = {n/12:6.0f} años a 12 ops/año")
    p.to_csv("potencia.csv", index=False); fp.to_csv("potencia_falsos.csv", index=False)
