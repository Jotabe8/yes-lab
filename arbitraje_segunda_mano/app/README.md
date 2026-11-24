# App de arbitraje · fase A (catálogo y calculadora)

| Fichero | Qué hace |
| --- | --- |
| `catalogo.csv` | Modelos vigilados: palabras clave, exclusiones y precios (nuevo, mediana de usado, suelo, días de venta) |
| `catalogo.py` | Normaliza el texto del anuncio, reconoce el modelo y detecta señales de alarma |
| `puntuacion.py` | Margen neto, decisión de compra y **precio máximo de compra** por modelo |
| `evaluar.py` | Línea de comandos |
| `../../tests/test_arbitraje.py` | Tests |

```bash
python -m unittest tests.test_arbitraje
python -m arbitraje_segunda_mano.app.evaluar --precios-maximos --envio 5   # precios para las alertas
python -m arbitraje_segunda_mano.app.evaluar "PS5 slim con lector, 2 mandos" 330 --envio 5
```

## Precios del catálogo

Solo tres modelos tienen precios, y son **estimaciones de partida** (24-11-2026):

| Modelo | Mediana usado | Fuente |
| --- | --- | --- |
| PS5 Slim con lector | 450 € | Precio pedido en anuncios de Wallapop (450-500 €); la venta real suele ser menor |
| PS5 Slim Digital | 400 € (nuevo 599,99 €) | Anuncios de Wallapop; PVP oficial según 3DJuegos |
| Sony A7 III (cuerpo) | 900 € | MPB 814-1.159 € (tienda, con garantía); un particular vende algo por debajo |

El resto está vacío: hay que rellenar `mediana_usado` (ventas reales, no precios pedidos),
`precio_suelo` (tasación de CeX / Back Market) y `dias_venta` antes de fiarse del margen.

## Parámetros por defecto (`Parametros`)

Embalaje 3 €, reacondicionado 5 €, 5 % de probabilidad de que la compra salga mal,
umbral de compra: margen ≥ 30 € **y** ≥ 25 % del coste. Comisión de Wallapop 0 % (paga el
comprador); la de eBay está sin configurar a propósito.

## Avisos automáticos

- **Gmail (en la nube):** una tarea programada lee cada hora, de 8:00 a 23:00 (hora de Madrid),
  los avisos de búsquedas guardadas de eBay/Wallapop, los pasa por `evaluar.py` y manda un
  correo solo con los que dejan margen. Los ya revisados quedan con la etiqueta
  `arbitraje/revisado`.
- **Windows (`../windows/prueba_notificaciones.ps1`):** prueba si las notificaciones de
  Wallapop que llegan del iPhone por Enlace Móvil se pueden leer. No envía nada.
