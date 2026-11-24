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

## Dónde abrirla

**https://jotabe8.github.io/yes-lab/lavadero/** (GitHub Pages, rama `claude/practical-galileo-5inths`). Ábrela en Chrome y guárdala en marcadores o en la pantalla de inicio.

También se puede copiar `index.html` a la tablet y abrirlo con Chrome sin internet, pero entonces no salen los avisos de Telegram.

## Importante

Los datos se guardan solo en ese navegador. Una vez a la semana, pulsa «Copiar copia de seguridad» y pega el texto en un correo. Para recuperarla, guarda ese texto en un archivo `.json` y usa «Restaurar copia».

## Avisos automáticos a tu Telegram

La app te manda un mensaje de Telegram en cada lavado y en cada alta o cobro.

1. En Telegram, abre **@BotFather**, envía `/newbot`, elige un nombre (por ejemplo «Lavadero La Soledad») y un usuario que acabe en `bot`. BotFather te da un **token** (algo como `123456789:AAH...`).
2. Busca tu bot en Telegram, pulsa **Iniciar** y escríbele «hola».
3. En la app, abre «Precios y copia de seguridad» → «Avisos a mi Telegram», pega el token y pulsa **Buscar mi chat**.
4. Pulsa **Enviarme una prueba**.

Los avisos solo funcionan abriendo `index.html` directamente en Chrome, con internet. En la vista previa de claude.ai están bloqueados. Quien tenga el token puede escribir como el bot, así que no lo compartas.
