# 1spin4win: detección de compras (2026-10-01)

El HAR manual de Ten Lucky Spins contiene el cliente `tenluckyspins_000264.js`. El constructor `TenLuckySpinsView` activa `useBuyFeature` y declara `buyFeatureMult=67`. El adaptador anterior sólo publicaba SPIN: su OK acreditaba la tirada base sin comprobar compras.

Ahora el discovery inspecciona el constructor del juego correspondiente en los assets ya descargados. Una declaración de compra genera el modo PURCHASE `D1_BUY_FEATURE`, con coste anunciado y cobertura pendiente. No basta la presencia del botón o de código compartido de compras; no se propaga una compra de un juego a otros. Si la inicialización devuelve `bf="f"`, se respeta la desactivación de compra de esa sesión, como hace el cliente oficial.

Una tirada base terminal con compra declarada y sin validar queda PARCIAL. Los OK históricos no se reescriben: hay que volver a probar los juegos para aplicar la detección nueva. Las continuaciones gratuitas siguen siendo distintas de una compra.

El HAR incluye la conexión `wss://gs.1spin4win.com/games`, pero no sus mensajes. El cliente muestra que la compra usa el comando `A/u2` de tipo 1 con un cuarto selector en `data`, y que hay variantes combinadas con apuestas especiales. Sin mensajes enviados y respuestas no se confirma qué recorrido se realizó, aceptación, débito ni cierre. Por eso el modo detectado todavía no se ejecuta automáticamente ni se exporta como compra validada.

Para terminar el contrato hace falta capturar los mensajes de la conexión WS: inicialización, compra, continuaciones, cierre y dos tiradas normales posteriores. Exportar el HAR de Firefox no garantizó incluirlos en esta captura; se pueden guardar los mensajes WS por separado. No publicar claves de sesión.

Verificación: 40 pruebas de detección y contratos existentes D1/Belatra aprobadas. La detección también se comprobó offline contra el cliente real incluido en el HAR. No se enviaron apuestas nuevas para este cambio.
