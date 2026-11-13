"""EV por cuota FTMO 2-Step con operaciones SIN ventaja (bracket TP = m·SL, prob. justa 1/(1+m)) y coste c (en R).
Reto +10 %, verificación +5 %, pérdida diaria 5 %, total 10 % (estáticas). Una operación al día.
Fondeada: cada 10 días hábiles se retira el 80 % del beneficio (cuota devuelta en el 1er retiro), saldo vuelve al inicial.
Política por fase: (f = riesgo por operación, m = TP/SL). En cada fase la apuesta se recorta para no pasar del objetivo
ni del límite total (juego 'audaz' de Dubins-Savage)."""
import numpy as np

def fase(rng, n, f, m, c, objetivo, max_dias=500, recorte=True):
    eq = np.zeros(n); vivo = np.ones(n, bool); ok = np.zeros(n, bool)
    p = 1 / (1 + m)
    for _ in range(max_dias):
        act = vivo & ~ok
        if not act.any(): break
        riesgo = np.full(n, f)
        if recorte:  # no arriesgar más de lo que falta para el objetivo / lo que queda hasta -10 %
            riesgo = np.minimum(riesgo, np.maximum((objetivo - eq) / m, 0.001))
            riesgo = np.minimum(riesgo, eq + 0.10 - 1e-4)
        gana = rng.random(n) < p
        d = np.where(gana, m * riesgo, -riesgo) - c * riesgo
        eq = np.where(act, eq + d, eq)
        vivo &= ~(act & (eq <= -0.10 + 1e-9))
        ok |= act & vivo & (eq >= objetivo - 1e-9)
    return ok

def fondeada(rng, n, f, m, c, cap, cuota, periodos=24, dias=10, reparto=0.8, colchon=None):
    eq = np.zeros(n); vivo = np.ones(n, bool); cobro = np.zeros(n); dev = np.zeros(n, bool)
    p = 1 / (1 + m)
    for _ in range(periodos):
        for _ in range(dias):
            riesgo = np.minimum(f, eq + 0.10 - 1e-4)
            if colchon is not None:  # dejar de operar en el periodo al ganar 'colchon'
                riesgo = np.where(eq >= colchon, 0.0, riesgo)
            gana = rng.random(n) < p
            d = np.where(gana, m * riesgo, -riesgo) - c * riesgo
            eq = np.where(vivo, eq + d, eq)
            vivo &= eq > -0.10 + 1e-9
        pag = vivo & (eq > 0)
        cobro += np.where(pag, eq * cap * reparto + np.where(dev, 0, cuota), 0)
        dev |= pag; eq = np.where(pag, 0.0, eq)
    return cobro

def ev(pol1, pol2, polf, c, cap=100_000, cuota=540, n=200_000, semilla=0, colchon=None):
    rng = np.random.default_rng(semilla)
    a = fase(rng, n, *pol1, c, 0.10)
    b = a & fase(rng, n, *pol2, c, 0.05)
    cobro = np.where(b, fondeada(rng, n, *polf, c, cap, cuota, colchon=colchon), 0)
    return dict(p1=a.mean(), p_pasar=b.mean(), ev=cobro.mean() - cuota, cobro_si_pasa=cobro[b].mean() if b.any() else 0)

if __name__ == "__main__":
    c = 0.01  # US100: 1 punto de coste con stop de 100 puntos
    for nom, p1, p2, pf in [
        ("prudente 1 %/1 %/1 %, 1:1", (0.01, 1), (0.01, 1), (0.01, 1)),
        ("tipo ORB 2 %/2 %/1,5 %, 1:1", (0.02, 1), (0.02, 1), (0.015, 1)),
        ("audaz 4,5 % 1:1 en todo", (0.045, 1), (0.045, 1), (0.045, 1)),
        ("audaz reto 4,5 % 1:2, fondeada 1 %", (0.045, 2), (0.045, 2), (0.01, 1)),
        ("audaz reto 4,5 % 1:2, fondeada 2 %", (0.045, 2), (0.045, 2), (0.02, 1)),
        ("audaz reto 4,5 % 1:2, fondeada 4,5 % 1:2", (0.045, 2), (0.045, 2), (0.045, 2)),
        ("audaz reto 4,5 % 1:1, fondeada 4,5 % 1:3", (0.045, 1), (0.045, 1), (0.045, 3)),
    ]:
        r = ev(p1, p2, pf, c, n=100_000)
        print(f"{nom:45s} p1 {r['p1']:.3f} pasa {r['p_pasar']:.3f}  EV/cuota {r['ev']:8.0f}  cobro medio si pasa {r['cobro_si_pasa']:8.0f}")
