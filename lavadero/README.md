# Bono Lavado · ES La Soledad

App de una sola pantalla para controlar en la caja de la tienda los bonos mensuales de túnel.

## Cómo se usa

1. Escribe la **matrícula** del cliente y pulsa **Comprobar**.
2. Según el color:
   - **Verde, puede lavar:** dale el ticket de túnel de su bono (Básico o Completo) y pulsa **Ticket entregado**.
   - **Ámbar, ya ha lavado hoy:** puede volver mañana. Es un lavado al día.
   - **Rojo, caducado:** cobra el mes y pulsa **Cobrar mes**. Ya puede lavar.
   - **Rojo, no es socio:** rellena el nombre y el teléfono, elige el bono, cobra y pulsa **Cobrar y dar de alta**.
3. Abajo está la lista de socios con su fecha de caducidad. Tocando una fila se comprueba ese socio.

4. En **Avisar por WhatsApp** salen los bonos que caducan esta semana o caducaron hace menos de 15 días. El botón abre WhatsApp con el mensaje ya escrito, y después queda marcado como avisado.

Los precios se cambian en «Precios y copia de seguridad».

## Instalación

Copia `index.html` a la tablet o al ordenador de la tienda y ábrelo con Chrome. Funciona sin internet.

## Importante

Los datos se guardan solo en ese navegador. Una vez a la semana, pulsa «Copiar copia de seguridad» y pega el texto en un correo. Para recuperarla, guarda ese texto en un archivo `.json` y usa «Restaurar copia».

## Avisos automáticos a tu WhatsApp

La app puede mandarte un WhatsApp en cada lavado y en cada alta o cobro, usando el servicio gratuito [CallMeBot](https://www.callmebot.com/), pensado para uso personal.

1. Mira en callmebot.com el número actual de su bot (cambia de vez en cuando) y guárdalo en los contactos del móvil.
2. Envíale por WhatsApp el texto `I allow callmebot to send me messages`.
3. Te contesta con tu clave (*apikey*).
4. En la app, abre «Precios y copia de seguridad» → «Avisos a mi WhatsApp», pon tu móvil y la clave, y pulsa «Enviarme una prueba».

Los avisos solo funcionan abriendo `index.html` directamente en Chrome, con internet. En la vista previa de claude.ai están bloqueados.
