import numpy as np, pandas as pd
from embudo import t_requerido

def ftmo_2step_rapido(r_dia, riesgo, cuota=540.0, capital=100_000, meses=12, reparto=0.8, n=3000, semilla=0):
    rng = np.random.default_rng(semilla); r = np.asarray(r_dia, float) * riesgo
    cobros = np.zeros(n); pasa = 0; dias_total = []
    for i in range(n):
        ok, dias_i = True, 0
        for obj in (0.10, 0.05):
            eq, dias = 0.0, 0
            lote = rng.choice(r, 800)
            while True:
                if dias >= len(lote): lote = np.r_[lote, rng.choice(r, 800)]
                d = lote[dias]; dias += 1
                if d <= -0.05 or eq + d <= -0.10 or dias > 750: ok = False; break
                eq += d
                if eq >= obj and dias >= 4: break
            dias_i += dias
            if not ok: break
        if not ok: continue
        pasa += 1; dias_total.append(dias_i)
        eq, total, dev = 0.0, 0.0, False
        for _ in range(meses):
            mes = rng.choice(r, 21); quemada = False
            for d in mes:
                if d <= -0.05 or eq + d <= -0.10: quemada = True; break
                eq += d
            if quemada: break
            if eq > 0: total += eq*capital*reparto + (0 if dev else cuota); dev, eq = True, 0.0
        cobros[i] = total
    return {"p": pasa/n, "ev": float(cobros.mean()-cuota), "dias_med": float(np.median(dias_total)) if dias_total else np.nan}

o = pd.read_csv("ops_noche_6mercados.csv", parse_dates=["fecha"])
neto = (o.r_bruto - o.coste_r).to_numpy()
se = neto.std(ddof=1)/np.sqrt(len(neto)); rec = (t_requerido(12)-1.6449)*se
print(f"neto {neto.mean():+.3f} R/op -> recortado {neto.mean()-rec:+.3f} (recorte {rec:.3f}, n {len(o)})")
dia = o.assign(neto=neto).groupby(o.fecha.dt.date)
r_dia = dia.neto.sum().to_numpy() - rec*dia.size().to_numpy()
ctl = dia.neto.sum().to_numpy() - neto.mean()*dia.size().to_numpy()
vacios = int(len(r_dia)*(252/(len(r_dia)/8.8) - 1))
serie, sctl = np.r_[r_dia, np.zeros(vacios)], np.r_[ctl, np.zeros(vacios)]
print(f"días de calendario simulados: {len(serie)} ({len(r_dia)} con operación)")
for riesgo in (0.004, 0.006, 0.0075, 0.01):
    e = ftmo_2step_rapido(serie, riesgo); c = ftmo_2step_rapido(sctl, riesgo)
    print(f"riesgo {riesgo*100:.2f} %/mercado: EV {e['ev']:+.0f} € (p {e['p']:.0%}, mediana {e['dias_med']:.0f} días hábiles)"
          f" | control {c['ev']:+.0f} € (p {c['p']:.0%})")
