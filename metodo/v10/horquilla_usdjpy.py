"""Horquilla real de USDJPY en Dukascopy M1 (bid/ask, hora servidor NY+7) a las horas del gotobi (08:00 y 09:55 JST).
Se ejecutó en el PC de Jorge (data/USDJPY_M1_DUKA.csv, 2018-01 -> 2026-10) el 15-11-2026."""
import sys, pandas as pd
d = pd.read_csv(sys.argv[1], parse_dates=["time"])
ny = (d.time - pd.Timedelta(hours=7)).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
jst = ny.dt.tz_convert("Asia/Tokyo"); d["hm"] = jst.dt.strftime("%H:%M"); d["y"] = jst.dt.year
for hm in ["07:55", "08:00", "08:01", "08:05", "09:30", "09:54", "09:55", "10:00", "16:00"]:
    s = d[d.hm == hm]; print(hm, "mediana pips", round(s.spread.median() * 100, 3), "media", round(s.spread.mean() * 100, 3))
print(d[d.hm.isin(["08:00", "09:55"])].groupby(["y", "hm"]).spread.median().mul(100).round(3).unstack())
