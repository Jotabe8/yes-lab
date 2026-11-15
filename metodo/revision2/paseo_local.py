"""Revisión 2 (PREREGISTRO.md, parte A): motores de gotobi, EIA (metodo/revision/analisis.py de PR #30,
copiado sin cambios como analisis_revision1.py) y subastas del Tesoro (metodo/v4/subastas.py) sobre
paseo aleatorio. Lo único que cambia es la carga: las velas M1 pasan por sinteticos.velas_paseo, año a año.
Uso: python metodo/revision2/paseo_local.py DIR_DATOS_PR30   (carpeta con USDJPY_*_m1.csv.gz, USOIL_*...)"""
import sys, os
import numpy as np, pandas as pd
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metodo.sinteticos import velas_paseo, prueba_motor
import analisis_revision1 as A

DATOS = sys.argv[1]
A.AQUI = os.path.dirname(os.path.abspath(DATOS.rstrip("/")))   # A.cargar lee AQUI/datos/
assert os.path.basename(DATOS.rstrip("/")) == "datos"
cargar_real = A.cargar
N = 20

def paseo_por_anio(m, semilla, tz):
    ys = []
    loc = m.index.tz_convert(tz)
    for y in sorted(set(loc.year)):
        g = m[loc.year == y].copy(); g.index = g.index.tz_convert(tz)
        if len(g) > 100:
            p = velas_paseo(g, semilla=semilla * 100 + y)
            p.index = p.index.tz_convert("UTC"); ys.append(p)
    return pd.concat(ys)

def con_paseo(semilla, tz):
    def cargar(sim):
        m, d1 = cargar_real(sim)
        return paseo_por_anio(m, semilla, tz), d1
    return cargar

out = []
# gotobi: hora de Tokio (sin cambio de horario) -> barajar por minuto UTC es lo mismo
A.cargar = cargar_real
real = A.gotobi("USDJPY"); g_real = real[real.gotobi]
coste_r = ((real[real.fecha >= "2023-01-01"].spread_pct.median() + 0.00005) / g_real.dist_pct).mean()
rs, rs_todos = [], []
for s in range(N):
    A.cargar = con_paseo(s, "UTC"); x = A.gotobi("USDJPY")
    rs.append(x[x.gotobi].r_bruto.values); rs_todos.append(x.r_bruto.values)
out.append(("Gotobi USDJPY (días gotobi)", g_real.r_bruto.mean(), len(g_real), prueba_motor(rs, coste_r), coste_r))
out.append(("Gotobi USDJPY (todos los días, misma hora)", real.r_bruto.mean(), len(real), prueba_motor(rs_todos, coste_r), coste_r))

# EIA: hora de Nueva York (con cambio de horario) -> barajar por minuto de NY
A.cargar = cargar_real
real = A.eia(); w = real[real.dow == 2]
rs, rs_todos = [], []
for s in range(N):
    A.cargar = con_paseo(s, "America/New_York"); x = A.eia()
    rs.append(x[x.dow == 2].r_bruto.values); rs_todos.append(x.r_bruto.values)
out.append(("EIA USOIL (miércoles)", w.r_bruto.mean(), len(w), prueba_motor(rs, w.coste_r.mean()), w.coste_r.mean()))
out.append(("EIA USOIL (todos los días)", real.r_bruto.mean(), len(real), prueba_motor(rs_todos, w.coste_r.mean()), w.coste_r.mean()))

# subastas del Tesoro: motor diario de v4/subastas.py; paseo = rendimientos diarios barajados y centrados
os.chdir(RAIZ)
src = open("metodo/v4/subastas.py").read().split("f_all = nom.auction_date")[0]
ns = {}; exec(compile(src, "subastas.py", "exec"), ns)          # define nom, precio, senal (sin correr la prueba)
p = ns["precio"]("IEF"); r = p.pct_change().dropna()
pos = ns["senal"](r.index, ns["nom"].auction_date)
neto_real = pos * r - pos.diff().abs().fillna(abs(pos.iloc[0])) * 0.0001
rng = np.random.default_rng(3); medias = []
for s in range(200):
    rr = pd.Series(rng.permutation(r.values - r.values.mean()), r.index)
    medias.append(float((pos * rr).mean()))
medias = np.array(medias)
sub = dict(real_bruto_anual=float((pos * r).mean() * 252), paseo_media_anual=medias.mean() * 252,
           paseo_t=medias.mean() / (medias.std(ddof=1) / np.sqrt(len(medias))) if medias.std() > 0 else 0.0,
           paseo_p95_anual=np.percentile(medias, 95) * 252)

print("Prueba del motor sobre paseo aleatorio (revisión 2)\n")
print(f"{'caso':48s} {'R real':>8s} {'ops':>6s} | paseo: R media   t      ops   ×coste  ¿pasa?")
for nombre, rm, n, pm, c in out:
    print(f"{nombre:48s} {rm:+8.3f} {n:6d} |        {pm['media']:+7.4f} {pm['t']:6.2f} {pm['n']:7d}  {abs(pm['media'])/c:5.2f}  {'sí' if pm['pasa'] else 'NO'}")
print(f"\nSubastas IEF: real bruto {sub['real_bruto_anual']:+.2%}/año | paseo (200 barajados) media {sub['paseo_media_anual']:+.3%}/año, "
      f"t de la media {sub['paseo_t']:.2f}, p95 {sub['paseo_p95_anual']:+.2%}/año")
