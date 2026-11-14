# Compara la réplica del port (orb_mnq_ref.py) con la serie v018 (serie_v018_be.csv) día a día.
import pandas as pd, numpy as np
F=pd.read_csv("ref_ftmo.csv",parse_dates=["d"]); D=pd.read_csv("ref_duka.csv",parse_dates=["d"])
ini=F.d.min(); X=pd.concat([D[D.d<ini],F]).set_index("d").sort_index()
S=pd.read_csv("serie_v018_be.csv",parse_dates=["d"]).set_index("d").sort_index(); S=S[~S.index.duplicated()]
X=X[(X.index>=S.index.min())&(X.index<=S.index.max())]
op=X.R_reto.notna(); so=S.index
both=X.index[op].intersection(so); solo_port=X.index[op].difference(so); solo_serie=so.difference(X.index[op])
print(f"Periodo {S.index.min():%Y-%m-%d} a {S.index.max():%Y-%m-%d}")
print(f"Operaciones: port {op.sum()} | serie v018 {len(S)} | comunes {len(both)} ({100*len(both)/len(S):.1f} % de la serie)")
print(f"  solo en el port {len(solo_port)} | solo en la serie {len(solo_serie)}")
# motivo de los días de la serie que el port no opera
m=X.reindex(solo_serie)
print("  días de la serie sin operación en el port, motivo:", m.bloqueo.fillna("sin señal/sin datos").value_counts().to_dict())
print("  días del port que la serie no tiene, motivo de la serie: (filtro de vol/noticias de la serie)", len(solo_port))
for a,b,nm in (("R_reto","R","reto (trailing 3R/1R)"),("R_fond","Rbe","fondeada (BE 2R)")):
    x=X.loc[both,a]; y=S.loc[both,b]
    same=(np.sign(x.round(3))==np.sign(y.round(3))).mean()*100
    print(f"{nm}: corr {np.corrcoef(x,y)[0,1]:.3f} | mismo signo {same:.1f} % | |dif|<0,05R {((x-y).abs()<0.05).mean()*100:.1f} % | media port {x.mean():+.3f} serie {y.mean():+.3f}")
    for per,(i,j) in {"2018-21":("2018","2021-12-31"),"2022-26":("2022","2027")}.items():
        k=[d for d in both if pd.Timestamp(i)<=d<=pd.Timestamp(j)]
        print(f"   {per}: n {len(k)} port {X.loc[k,a].mean():+.3f} serie {S.loc[k,b].mean():+.3f}")
# todas las operaciones del port (con sus filtros) frente a la serie completa
for a,b in (("R_reto","R"),("R_fond","Rbe")):
    print(f"Todas: port {a} n {X[a].notna().sum()} media {X[a].mean():+.3f} | serie {b} n {len(S)} media {S[b].mean():+.3f}")
print("Futuros (sin horquilla, el coste se resta en $): Rf_reto", round(X.Rf_reto.mean(),3), "Rf_fond", round(X.Rf_fond.mean(),3))
X.to_csv("ref_combinada.csv")
