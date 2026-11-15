# Control de estructura: ¿un DARWIN SIN ventaja (misma serie, media 0) gana dinero en Darwinex Zero?
import numpy as np, importlib.util
g={}; src=open("gold.py").read().split("\nfilas=[]\nfor esc_nom")[0]; exec(src,g)
o,mix=g["series"](0.05,0)
for nom,ser in [("ORB US100+cripto real",mix),("misma serie con media 0",mix-mix.mean()),("media 0 y vol x1,5",(mix-mix.mean())*1.5)]:
    for perm in (None,"obj10"):
        out,ng,ns=g["sim"](ser,50.0,perm,True,1.6,69000,N=5000)
        print(f"{nom:28s} perm {perm or 'no':5s} | media {out.mean()/3:7.0f} €/año | mediana {np.median(out)/3:7.0f} | P(neg) {(out<0).mean()*100:4.1f} % | GOLD {ng:.1f} SILVER {ns:.1f}")
