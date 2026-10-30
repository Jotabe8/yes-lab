# Serie diaria (por fecha de cierre) del NNFX D1 elegido por walk-forward 2017-2026 con la biblioteca pandas-ta.
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, "/mnt/project-files/ea-pons-nnfx"); sys.path.insert(0, "/tmp/claude-0/info"); import grid_vp2x; sys.modules["grid_vp2"] = grid_vp2x
import grid_lib as L
G = grid_vp2x
D = G.load("/tmp/claude-0/mt5"); P, kb = L.prep(D); G.T.BASELINES = {k: None for k in kb}
rows = []
for y in range(2017, 2027):
    r, _ = G.search(P, (y - 8) * 10000 + 101, (y - 1) * 10000 + 1231); sp = r[0][1]
    R, C, Dd = G.run(P, sp, y * 10000 + 101, y * 10000 + 1231)
    rows += [(d, a, a - c) for a, c, d in zip(R, C, Dd)]; print(y, sp, len(R), R.mean(), flush=True)
df = pd.DataFrame(rows, columns=["d", "R", "R2"]); df["d"] = pd.to_datetime(df.d.astype(str))
df.to_csv("/tmp/claude-0/info/nnfx_wf_trades.csv", index=False)
print(len(df), df.R.mean(), df.R2.mean())
