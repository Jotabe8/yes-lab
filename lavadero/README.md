# Bono Lavado · ES La Soledad (prototipo)

App web para controlar en la caja de la tienda los **bonos mensuales de túnel** de la gasolinera.

## Cómo se usa

1. **Alta del socio.** En «Nuevo socio» se registran el nombre, el teléfono, la matrícula y el plan, y se cobra el primer mes (efectivo o tarjeta). La app genera su número de socio (`LS-0001`…) y una tarjeta con código QR.
2. **El socio viene a lavar.** En «Comprobar bono» se escribe la matrícula o se escanea su QR.
   - Verde **Puede lavar**: se saca en el TPV el ticket de túnel del programa de su plan, como lavado de bono, y se pulsa «Registrar lavado». Apuntar el código del ticket es opcional. El cliente introduce el código en el túnel como hasta ahora.
   - Ámbar **Ya ha lavado hoy**: ha llegado al límite diario de su plan.
   - Rojo **Bono caducado**: hay que renovar antes de darle el ticket.
3. **Boxes.** Si el plan incluye monedas para los boxes, la app lleva el saldo del mes y registra cada entrega en monedas.
4. **Renovación.** Desde la ficha o el resumen. Si aún le quedan días, el nuevo mes se suma a continuación.
5. **Resumen.** Socios en vigor, ingresos del mes, lavados por día, quién caduca esta semana (con un aviso para copiar en WhatsApp) y quién no ha renovado.

## Instalación en la tablet

Copia la carpeta `lavadero/` (`index.html` y `qrcode.js`) a la tablet o al ordenador de la tienda y abre `index.html` con Chrome. Las tipografías se cargan de Google Fonts si hay internet. Sin conexión, la app funciona igual con las fuentes del sistema.

Un lector de códigos USB o Bluetooth en modo teclado sirve para leer el QR. Basta con escanear con el cursor en la casilla de búsqueda.

## Limitaciones del prototipo

- **Los datos se guardan solo en ese navegador** (localStorage). Hay que hacer una copia de seguridad semanal desde «Planes y ajustes». Si se borran los datos del navegador, se pierden.
- No funciona en varios dispositivos a la vez y no tiene usuarios ni contraseñas.
- No está conectada al TPV de Repsol ni al túnel Istobal. El ticket se sigue sacando a mano.

## Siguientes pasos (versión real)

1. Servidor con base de datos y acceso desde varios dispositivos, con usuario por empleado.
2. Cobro recurrente con tarjeta o domiciliación SEPA (Stripe), con descuento frente al pago en caja.
3. Activación directa del túnel sin pasar por caja (Smartwash de Istobal o lectura de matrícula).
4. Multi-lavadero, para ofrecerlo a otras estaciones.
