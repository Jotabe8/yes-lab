# Preregistro: continuación del gap de resultados en acciones de EE. UU.

Fecha: 2026-10-25, antes de descargar ni mirar ningún dato. Nada de esto es una recomendación
de inversión.

## Por qué este candidato

Casi todo lo descartado en el proyecto falló por lo mismo: el efecto por operación (0,02-0,07 %)
es del tamaño del coste de un CFD de prop firm. Aquí el movimiento esperado es de otro orden
(la literatura de *post-earnings announcement drift* y de gaps con volumen habla de 1-3 % en los
días siguientes), y el motor es la noticia de cada empresa, no la sesión del índice. Debería
estar poco correlacionado con el ORB US100, que opera la apertura del Nasdaq y cierra el mismo
día.

## Datos

Velas diarias OHLCV de Yahoo (ajustadas por splits, no por dividendos), 2005-2026, descargadas
en GitHub con `lab/acciones.py`. Dos universos:

- **FTMO**: las acciones de EE. UU. que FTMO ofrece como CFD (lista en `lab/acciones.py`,
  a confirmar en el terminal).
- **Amplio**: FTMO más otras 48 grandes compañías, solo para tener potencia estadística.

## Regla (fija, no se ajusta)

Señal al cierre del día *t*:

1. Gap de apertura `O_t / C_{t-1} − 1` de al menos ±3 %.
2. Volumen del día al menos 3 veces la media de los 20 días anteriores (filtra días de
   resultados u otra noticia de la empresa sin necesitar el calendario).
3. El día cierra en la dirección del gap: `C_t / C_{t-1} − 1` del mismo signo y de al menos 3 %.

Operación: entrada al cierre de *t* en la dirección del gap (largos y cortos). Stop a 2 ATR(20)
de la entrada, con el ATR de los 20 días anteriores al evento; si la apertura salta el stop, se
llena en la apertura. Salida al cierre de la 5.ª sesión. Una posición por acción a la vez.
Resultado en R (riesgo = distancia al stop).

Costes: 0,10 % ida y vuelta (spread más comisión) y 0,02 % de swap por noche natural
(7 noches en 5 sesiones), unos 0,24 % por operación. Prueba al doble: 0,48 %.

## Muestras

- 2005-2017: dentro de muestra. Solo para ver la sensibilidad; la regla no se cambia.
- **2018-2026: fuera de muestra. Aquí se decide.**

## Criterio para pasar (todo a la vez, fuera de muestra)

1. Universo amplio: R medio neto > 0 con t ≥ 2 a coste normal, y > 0 al doble.
2. Universo FTMO: R medio neto > 0 a coste normal (mismo signo, aunque tenga menos potencia).
3. Al menos 5 de los 9 años positivos.
4. Correlación del P&L diario con el QQQ por debajo de 0,3 en valor absoluto (y después con
   la serie real del ORB US100 del PC).
5. En el Monte Carlo 2-Step junto al ORB US100, mejor que el control de subir el riesgo del ORB
   a la misma volatilidad.

Si falla, se descarta, sin variantes de rescate (regla de Jorge). La sensibilidad
(mantener 1, 3 y 10 sesiones; gap de 2 y 5 %; volumen ×2 y ×5; sin stop) se informa solo
como contexto.

## Límites conocidos de antemano

- Sesgo de supervivencia: las acciones son las grandes de hoy. Favorece a los largos; por eso
  se miran largos y cortos por separado.
- Pocos eventos en el universo FTMO (estimación previa: 20-40 al año).
- Entrar al cierre en MT5 obliga a operar en los últimos minutos de la sesión de EE. UU.; el
  spread del CFD en ese momento puede ser mayor que el supuesto.
