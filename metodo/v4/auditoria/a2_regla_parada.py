"""Auditoría 2: potencia de la regla de parada en real ('parar si R media < 0 tras 100 ops') frente a una
prueba secuencial (SPRT de Wald) entre H1: edge = el del backtest y H0: edge = 0, con la forma real de las R."""
import numpy as np, pandas as pd
s = pd.read_csv("/mnt/project-files/dos-orb/serie_v018_be.csv").R.to_numpy()
c = s - s.mean(); sd = s.std()
rng = np.random.default_rng(1)
print(f"R v018: media {s.mean():.3f}, sd {sd:.2f}")
for mu in (0.12, 0.06, 0.0, -0.06):
    x = rng.choice(c, (20000, 400)) + mu
    m100 = x[:, :100].mean(1)
    print(f"edge real {mu:+.2f}: P(parar tras 100 ops) {np.mean(m100 < 0):.0%}; P(R media 100 ops < +0,04 'alerta') {np.mean(m100 < 0.04):.0%}")
# SPRT gaussiano: log LR acumulado = sum (mu1 x - mu1^2/2)/sd^2 ; parar (edge 0) si < ln(b/(1-a)); confirmar si > ln((1-b)/a)
a, b, mu1 = 0.05, 0.20, 0.12
lo, hi = np.log(b / (1 - a)), np.log((1 - b) / a)
for mu in (0.12, 0.06, 0.0, -0.06):
    x = rng.choice(c, (20000, 2000)) + mu
    llr = np.cumsum((mu1 * x - mu1 ** 2 / 2) / sd ** 2, 1)
    abajo = (llr <= lo).argmax(1).astype(float); abajo[~(llr <= lo).any(1)] = np.inf
    arriba = (llr >= hi).argmax(1).astype(float); arriba[~(llr >= hi).any(1)] = np.inf
    parar = abajo < arriba
    n = np.minimum(abajo, arriba); n = n[np.isfinite(n)]
    print(f"SPRT edge real {mu:+.2f}: P(parar) {parar.mean():.0%}, P(confirmar) {(arriba < abajo).mean():.0%}, ops medianas hasta decidir {np.median(n):.0f}")
