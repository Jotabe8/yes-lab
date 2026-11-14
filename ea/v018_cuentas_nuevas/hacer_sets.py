# Genera .set (UTF-16 LE, como los guarda MT5) del ORB_US100_AGR_v018 a partir de los valores por defecto del .mq5
import re, sys
src = open("ORB_US100_AGR_v018.mq5", encoding="latin-1").read()
base = {}
for m in re.finditer(r'^input\s+\w+\s+(\w+)\s*=\s*("[^"]*"|[^;]+);', src, re.M):
    base[m.group(1)] = m.group(2).strip().strip('"')
def escribe(nombre, cambios, nota):
    v = dict(base); v.update({k: str(x) for k, x in cambios.items()})
    for k in cambios: assert k in base, k
    txt = "; " + nota + "\r\n" + "".join(f"{k}={v[k]}\r\n" for k in base)
    open(nombre, "w", encoding="utf-16").write(txt)
comun = dict(InpModel=2, InpAccountSize=10000, InpRiskP1Pct=2.0, InpRiskP2Pct=2.0, InpRiskFundedPct=1.5,
             InpVolFilter="true", InpVolPct=90, InpVolLookback=252, InpAutoStages="false", InpPush="true", InpLogCsv="true")
escribe("ORB_v018_FTMO_2Step_10K_fase1.set", dict(comun, InpStage=0), "FTMO 2-Step Swing 10K - Fase 1 (2 %) - 14/11/2026")
escribe("ORB_v018_FTMO_2Step_10K_fase2.set", dict(comun, InpStage=1), "FTMO 2-Step Swing 10K - Fase 2 (2 %) - 14/11/2026")
escribe("ORB_v018_FTMO_2Step_10K_fondeada.set", dict(comun, InpStage=2), "FTMO 2-Step Swing 10K - Fondeada (1,5 %, stop a entrada a +2R) - 14/11/2026")
print(len(base), "parametros")
# The5ers High Stakes 10K (2-Step 10 % / 5 %, diaria 5 %, máxima 10 %, 3 días rentables >= 0,5 %, noticias: ninguna orden
# nueva de 2 min antes a 2 min después de una noticia fuerte). Revisar antes la hora del servidor (ver LEEME).
t5 = dict(comun, InpMinTradingDays=3, InpRiskAfterTargetPct=0.6, InpFomcServerHHMM=2055)
escribe("ORB_v018_The5ers_HighStakes_10K_fase1.set", dict(t5, InpStage=0), "The5ers High Stakes 10K - Step 1 (2 %) - 14/11/2026")
escribe("ORB_v018_The5ers_HighStakes_10K_fase2.set", dict(t5, InpStage=1), "The5ers High Stakes 10K - Step 2 (2 %) - 14/11/2026")
escribe("ORB_v018_The5ers_HighStakes_10K_fondeada.set", dict(t5, InpStage=2), "The5ers High Stakes 10K - Pro/fondeada (1,5 %) - 14/11/2026")
