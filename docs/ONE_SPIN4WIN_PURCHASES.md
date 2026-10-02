# 1spin4win: compras y tiradas normales (2026-10-02)

El cliente de Ten Lucky Spins declara compra x67. La primera captura Firefox incluía el cliente y handshake sin mensajes WS. La nueva captura HAR Browser sí incluye 42 frames, en `_webSocketFrames`: una compra, quince continuaciones de bonus y cinco apuestas normales posteriores. Se analizan los frames y no los contadores del resumen del exportador, que registraba cero operaciones.

## Contrato observado

Se usa un único WebSocket `wss://gs.1spin4win.com/games` y el sobre `A/u2`, con `key` de la sesión actual y `type="1"`:

- Tirada normal: `data="<lines>,<betIndex>,<playmode>"`.
- Compra del perfil observado: `data="<lines>,<betIndex>,<playmode>,1"`.
- Continuaciones gratuitas: tres campos, sin volver a enviar el selector de compra.

El HAR muestra `10,0,0,1` seguido de `st=5`, `b8=0`, `b9=15`. Quince continuaciones avanzan el contador hasta `st=12`, `b8=b9=15`; el premio se acredita en el saldo. El siguiente envío ya descuenta una apuesta normal: no debe consumirse como continuación gratuita. La captura se adjuntó tarde y no demuestra el saldo anterior a la compra; x67 es el coste declarado por el cliente, no una medición independiente del débito de esta captura.

## Ejecución en Tester Spin

La cola ejecuta las repeticiones de SPIN y luego las repeticiones de PURCHASE, registradas por separado. Cada intento conserva sus requests, respuestas y resultado. Si la auditoría de regreso está activa, agrega dos apuestas normales en la misma sesión y las etiqueta como comprobaciones de regreso, separadas de las continuaciones gratuitas. La compra lleva el cuarto selector sólo en su primer envío, exige respuesta con bonus reconocido y continúa hasta el cierre. El estado 12 sólo se considera cerrado si sus contadores son positivos y completos. No se lanza otra compra si la sesión ya contiene un bonus activo, ni cuando el servidor deshabilita la compra con `bf="f"`.

La detección usa el constructor específico del juego y el serializer común demostrado: el perfil de compra por defecto pone `sideBet=2` y transmite `sideBet-1`, es decir selector 1. Se reutiliza en clientes que demuestren esa misma cadena y no reconfiguren los selectores o la apuesta especial en el constructor. Una declaración de compra de otra familia queda pendiente; no se copia selector 1 a ciegas a todo el catálogo.

Una compra se valida después de completar sus repeticiones con bonus aceptado y cierre. Una tirada normal exitosa no oculta una compra rechazada o pendiente. Los OK históricos no se reescriben; hace falta repetir la prueba con la aplicación reiniciada.

## Clasificación y evidencia

Tres campos se clasifican como `SPIN/normal`; cuatro como variante. Sólo un selector identificado por el cliente permite marcar `bonus_buy` o `side_bet`. Los artefactos incluyen `spin_shape`; operación, aceptación y cierre son datos separados. La comprobación opcional de coste necesita un débito verificado: una diferencia de saldo puede incluir premios.

Se incluyó una fixture sanitizada con los frames relevantes, sin claves de sesión. La reproducción del recorrido manual comprueba que hay un único envío de compra y que las cinco apuestas normales posteriores no se consumen como bonus. La verificación de código se realiza offline; todavía no se afirma que todo el catálogo haya sido probado con compras ni se reemplazan los resultados locales por esa reproducción.

Verificación: 48 pruebas específicas aprobadas, incluida reproducción con auditoría activada, aislamiento entre modos y revisión independiente sin hallazgos pendientes.

La suite completa anterior al último guard de cierre registró 806 pruebas y 73 subtests aprobados; permanecen cuatro fallos preexistentes de BGaming. El guard posterior se comprobó en la suite específica.


## Verificación real y corrección del lanzador (2026-10-02)

Al revisar los 30 resultados más recientes de la aplicación no había intentos PURCHASE. Sus specs contenían `purchase_modes=[]`; varios sólo habían inspeccionado `games_000101.js`. El enlace corporativo usa `games.html?game=...`, cuyo JavaScript redirige a `<game>.html`. Resolver el WebSocket mediante navegador no incorporaba el cliente del juego a la detección estática. El ejecutor ahora reproduce ese redirect conocido del host oficial, conserva los parámetros y descarga los assets del juego específico antes de decidir sus modos.

Una prueba real de Ten Lucky Spins, iniciada desde el enlace genérico del catálogo con mensajes espaciados 0,7 segundos, completó SPIN y PURCHASE por separado: un envío de compra con selector 1 y quince continuaciones; ambos intentos terminaron OK y sus auditorías de regreso quedaron confirmadas. El modo PURCHASE quedó validado en ese resultado. La prueba se guardó en evidencia local separada, sin reemplazar el historial de la aplicación ni publicar claves de sesión.

También se comprobó estáticamente el discovery corregido en seis entradas recientes (Cash'n Fruits X, Cash'n Fruits Hold And Win, Cash&Spins 243, Cash Amplifier 243, Burning Spins 243 y Buffalo's Wealth Win Spins). Cada una recorrió cuatro scripts y no produjo compras declaradas bajo el contrato conocido. Esta muestra no es una validación de compras de todo el catálogo ni prueba que no existan otras familias de compras.

La aplicación ya abierta debe reiniciarse para cargar la corrección. Los OK antiguos no acreditan compras y no se reescriben. Verificación específica tras el fix: 49 pruebas aprobadas.
