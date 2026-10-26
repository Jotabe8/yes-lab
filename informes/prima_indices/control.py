exec(open("ev_prima.py").read().split("for div in (False, True):")[0])
s0 = port_div(0.025, False); s0 = s0[(s0.index >= a) & (s0.index <= b)] * 100
tests = {"índices reales (sin div, +2,5 %)": s0, "índices con media 0 (control sin edge)": s0 - s0.mean(),
         "índices con media negativa (−2 %/año)": s0 - s0.mean() - 2.0 / 252,
         "ruido normal i.i.d. misma vol, media 0": pd.Series(np.random.default_rng(0).normal(0, s0.std(), len(s0)), s0.index)}
for nm, ser in tests.items():
    for days in (252, 756):
        for prod, r in best(ser, 99, days).items():
            print(f"{days//252} año(s) {nm:42s} {'1-Step' if prod==1 else '2-Step'} {r['size']:>3}K reto {r['rc']} fond {r['rf']} | neto medio {r['mean']:+7.0f} € | P(neto>0) {r['ppos']:.0f}% | P(pasar) {r['pass1']:.0f}%", flush=True)
