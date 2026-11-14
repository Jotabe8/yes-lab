# Preregistro v4 ronda 6 (13-11-2026, antes de descargar)

Ronda 5 (candidato 7, corto de perpetuos recién listados frente a BTC, 877 listados 2020-2026): **NO PASA**.
V1 30 días +0,116 %/día t 2,23 (< 2,4), 2ª mitad +0,071 %, costes ×2 t 2,13. Mediana por evento +4,9 %, 62 % ganadores,
pero la peor pérdida de un evento es −494 % (COAI) y 2025 sale −0,1 %: cola de ruina. No se rescata con un stop (sería
una variante elegida tras ver los datos). Placebo no ejecutado (ya falla el listón principal).

## Candidato 8: ciclo de las subastas del Tesoro de EE. UU. (Lou, Yan y Zhang 2013)

- Pagador: los creadores de mercado primarios que tienen que absorber la oferta nueva de cada subasta piden un
  descuento (los rendimientos suben los días previos) y lo devuelven al colocar el papel después. Pagador
  identificable y persistente mientras el Tesoro emita deuda en subastas programadas (calendario público semanas antes).
- Eventos: todas las subastas de Notes y Bonds nominales (2 a 30 años, nuevas y reaperturas; sin TIPS, FRN ni letras)
  de fiscaldata.treasury.gov, 2003-2026.
- Instrumento V1: IEF (7-10 años), precio ajustado por cupones (Yahoo). Coste 0,01 % por unidad de cambio de posición.
- Señal (conocida de antemano): para el rendimiento del día d (cierre d−1 → cierre d), posición −1 si hay una subasta
  en los días hábiles [d, d+4] (los 5 días que acaban en la subasta, incluida) y +1 si hubo una en [d−4, d−1] (los 4
  días hábiles posteriores); si coinciden las dos cosas, se suman y se toma el signo (0 si se anulan).
- Pasa si: t neto (diario) ≥ 2,4; 2ª mitad > 0; costes ×2 > 0; supera el p95 del placebo (rotación circular de la
  serie de posición, desfase al azar ≥ 20 días, 200 repeticiones).
- Réplica obligatoria si pasa: TLT (20+ años) y futuro ZN=F con la misma señal, y el subperiodo 2009-2026 (fuera de
  la muestra del artículo, 1980-2008).
- V2 (informativo): solo subastas de 10 y 30 años. V3 (informativo): solo la pata previa (corto) y solo la posterior.
