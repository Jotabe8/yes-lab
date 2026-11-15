# Compara el backtest de NinjaTrader (ORB_MNQ_Lucid en Modo validacion) con la réplica Python (ref_combinada.csv).
# Uso: python3 comparar_nt.py ORB_MNQ_Backtest_ops.csv
#  (el CSV lo escribe el EA en Documentos\NinjaTrader 8\ORB_MNQ\ cuando "Modo validacion" = True)
# La réplica usa el CFD US100 (FTMO/Dukascopy) y NinjaTrader el futuro MNQ: los precios no son idénticos, así que se
# espera el mismo lado casi siempre y una correlación alta de R, no una copia exacta.
import sys, numpy as np, pandas as pd
nt = pd.read_csv(sys.argv[1], sep=";")
nt["d"] = pd.to_datetime(nt.Fecha, format="%Y.%m.%d")
nt["dir"] = np.where(nt.Lado == "LONG", 1, -1)
nt["R"] = nt.dir * (nt.PrecioSalida - nt.PrecioEntrada) / nt.StopPts
nt = nt.drop_duplicates("d").set_index("d")
ref = pd.read_csv("ref_combinada.csv", parse_dates=["d"]).set_index("d")
fase = nt.Fase.iloc[0] if "Fase" in nt else "reto"
col = "Rf_fond" if fase == "fondeada" else "Rf_reto"
ref = ref[(ref.index >= nt.index.min()) & (ref.index <= nt.index.max())]
r_op = ref[ref[col].notna()]
com = nt.index.intersection(r_op.index)
print(f"Periodo {nt.index.min():%Y-%m-%d} a {nt.index.max():%Y-%m-%d} | fase {fase}")
print(f"Operaciones NinjaTrader {len(nt)} | réplica {len(r_op)} | comunes {len(com)} ({100*len(com)/max(1,len(r_op)):.1f} % de la réplica)")
lado = (nt.loc[com, "dir"] == r_op.loc[com, "lado"]).mean() * 100
x, y = nt.loc[com, "R"], r_op.loc[com, col]
print(f"Mismo lado {lado:.1f} % | corr R {np.corrcoef(x, y)[0,1]:.3f} | R media NT {x.mean():+.3f} réplica {y.mean():+.3f}")
print(f"Stop en puntos: NT mediana {nt.StopPts.median():.2f} | réplica {r_op.stop_pts.median():.2f}")
solo_nt = nt.index.difference(r_op.index); solo_ref = r_op.index.difference(nt.index)
print("Solo en NT:", len(solo_nt), list(solo_nt[:10].strftime("%Y-%m-%d")))
print("Solo en la réplica:", len(solo_ref), list(solo_ref[:10].strftime("%Y-%m-%d")))
print("Criterio para darlo por bueno (como el GER40 en MT5): >= 95 % de días comunes, >= 95 % mismo lado, corr >= 0,9 y R media parecida.")
