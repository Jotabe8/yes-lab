# v14d · Hurst sobre los descartados prometedores · resultados (16-11-2026)

Preregistro PREREGISTRO_DESCARTADOS.md (subido antes de calcular). Salidas: salida_descartados_orb.txt y
salida_descartados_gotobi.txt. Datos gotobi: M1 Dukascopy bid/ask 2012-26, 45/45 par-año (metodo/v14/gotobi/).

## Veredicto: 0 de 4 pasan → DESCARTADO, sin rescates

| Prueba | Base neto | Persistente neto (t) | Placebo p-valor | Sharpe filtrado / base | Resultado |
|---|---|---|---|---|---|
| ORB sin condición GER40+UK100+JP225+oro · H5 | +0,064 | +0,070 (2,27) | 0,39 | 0,55 / 0,73 | NO |
| ORB sin condición · Hhoy | +0,064 | +0,033 (1,11) | 0,93 | 0,27 / 0,73 | NO |
| Gotobi USDJPY · H5 | +0,012 | +0,016 (0,51) | 0,42 | 0,13 / 0,13 | NO |
| Gotobi USDJPY · Hhoy | +0,012 | +0,005 (0,14) | 0,62 | 0,04 / 0,13 | NO |

- ORB sin condición: el régimen persistente no separa nada (GER40, JP225 y oro igual o mejor en antipersistente;
  solo UK100 mejora con H5 y empeora con Hhoy). Es azar.
- Gotobi: con entrada al ask y salida al bid reales (2012-26) el "bruto" queda en +0,038 R en USDJPY (+0,044 desde
  2018, +0,032 antes), y la comisión (0,026 R) lo deja en +0,012 R t 0,53. El filtro no lo sube: +0,016 y +0,005.
  EURJPY mejora algo con días persistentes (+0,04) pero GBPJPY no, y no hay coste medido de los cruces.
- Conclusión de toda la serie v14: Hurst/DFA en M1 no aporta información útil a ninguna estrategia del proyecto
  (2 sistemas con ventaja, 2 descartados prometedores, 1 sistema propio). Lo único abierto es el seguimiento en
  real del ORB US100 (PREREGISTRO_SEGUIMIENTO.md), que es gratis.
