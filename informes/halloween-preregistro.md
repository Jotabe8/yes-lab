# Efecto Halloween ("Sell in May"): diseño de la prueba, fijado antes de ejecutarla

Fecha: 2026-10-25. Candidata del informe semanal del 25 de octubre. Se sube antes de ver ningún
resultado. Nada de esto es una recomendación de inversión.

Nota para el proyecto de prop firms: con 2 operaciones al año no sirve como EA para un
challenge (no llega al objetivo en plazo y choca con la regla de consistencia). Se prueba para
la cartera del laboratorio, no para FTMO.

## Cómo se evita el sobreajuste

1. **Cero parámetros.** La regla es la del artículo (Bouman y Jacobsen, 2002; Jacobsen y Zhang,
   2021): invertido del 1 de noviembre al 30 de abril y en liquidez del 1 de mayo al 31 de
   octubre. No se prueban otras fechas de entrada ni de salida para elegir, así que no hace falta
   walk-forward: no hay nada que ajustar.
2. **La unidad es el año, no el día.** El efecto es una diferencia entre dos semestres, así que la
   prueba compara, año a año, el retorno de noviembre-abril con el de mayo-octubre siguiente. Con
   10 años por mercado hay pocas observaciones, y se dice así.
3. **Muchos mercados, lista cerrada.** SPY, IBEX 35 y Santander (Yahoo, 2016-2026) y, como
   confirmación, los índices D1 de Dukascopy del PC de Jorge: US500, US100, US30, GER40, FRA40,
   EU50, UK100, Nikkei, Hang Seng y ASX 200 (2011/2013-2025). No se quita ninguno a posteriori.
4. **Placebo de las 12 rotaciones.** Se calcula la misma diferencia para los 12 semestres posibles
   (empezando en cada mes). Si noviembre-abril no queda claramente arriba, el resultado es ruido.
5. **Fuera de la muestra del artículo.** Jacobsen y Zhang usan datos hasta 2017. Se publica aparte
   el resultado de 2018 en adelante, que es fuera de muestra real.

## Criterio de aprobado

Con todos los mercados y años juntos:

- Diferencia media invierno − verano > 0 con t > 2.
- Al menos dos tercios de los mercados con diferencia media positiva.
- Noviembre-abril entre las 2 mejores de las 12 rotaciones.
- Como estrategia en SPY, IBEX y Santander con costes (0,15 % por lado, el valor del laboratorio,
  y al doble): Sharpe mayor o igual que comprar y mantener. La liquidez no cobra interés, lo que
  perjudica a la estrategia.

Si falla cualquiera de las cuatro, se descarta y no se reajusta.
