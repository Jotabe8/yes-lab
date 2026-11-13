# Preregistro: reversión intradía del hueco nocturno en acciones, neutral al mercado (13-11-2026)

Hipótesis (Lou, Polk y Skouras 2019, "A tug of war"; Berkman et al. 2012): los inversores minoristas y
las órdenes de apertura empujan de más el precio de noche (noticias, órdenes acumuladas); durante la
sesión los institucionales lo corrigen. En el corte transversal, las acciones que más suben de noche
tienden a hacerlo peor durante el día, y al revés. Neutral al mercado: debería tener correlación
baja con el ORB US100. Distinto de lo descartado: CO-OC se probó entre índices, no entre acciones.

Regla (fija):
- Universo: las 71 acciones grandes de EE. UU. del estudio del ORB (23 FTMO + 48), M1 bid/ask Dukascopy.
- Señal: hueco = apertura 9:30 / cierre 16:00 del día anterior − 1, menos la mediana del día.
- 9:35 NY: comprar las 5 de hueco más negativo y vender las 5 de hueco más positivo, mismo nominal.
- Salida 15:55 NY. Sin stop (cesta neutral). Variante 2: entrada a las 9:31.
- Coste: horquilla real a la entrada y a la salida + 0,004 % por lado.
- Métrica: rentabilidad diaria de la cesta (media larga − media corta) en %; R = cesta con
  volatilidad diaria normalizada a 1 % (para EV por cuota).
Periodo: ajuste 2018-2022; fuera de muestra 2023-2026 abierto una vez.
Placebo: mismas acciones y días, orden aleatorio (200 réplicas).
Puertas: bruto >= 3x coste, > p95 placebo; neto con coste x2 > 0, >= 60 % años +; OOS > 0 t >= 1;
EV 2-Step > control; corr diaria con ORB US100 < 0,3.
