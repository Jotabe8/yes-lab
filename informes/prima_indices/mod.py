exec(open("ev_prima.py").read().split("for div in (False, True):")[0])
for div in (False, True):
    s = port_div(0.025, div); s = s[(s.index >= a) & (s.index <= b)] * 100
    g = {"SERIE": s, "CLIP": 99}; exec(src, g)
    for rc in (1.0, 1.5, 2.0, 3.0):
        for prod in (1, 2):
            r = g["sim"](prod, 200, rc, rc, 632, N=3000, days=756)
            print(f"solo largo {'con' if div else 'sin'} div riesgo {rc} (vol ~{7*rc:.0f} %) 3 años {'1-Step' if prod==1 else '2-Step'} 200K | neto medio {r['mean']:+7.0f} € | P(pasar) {r['pass1']:.0f}%")
