# 3 Oaks: contratos de entrada y continuaciones

El catálogo público y el lanzador permiten localizar el cliente activo. El transporte de demo observado usa POST con JSON como `text/plain`, con comandos de login, start y play. Las sesiones y respuestas completas se guardan localmente.

## Primitivas del cliente

`source_inputs.py` y `code_primitives.py` analizan estáticamente el código publicado; no ejecutan JavaScript descargado. Separan la ruta del botón de giro de las rutas de compra. Soportan formas reconocidas de funciones, funciones flecha, eventos, middleware y puentes como `sendPlayAsync`; una forma desconocida no se completa por intuición.

Los parámetros salen de fuentes observadas: apuesta, líneas y factores anunciados. Un handler antiguo de tres campos no demuestra que el botón actual use ese formato. Se contrastan `init.js`, el protocolo activo y el controlador compartido `GR/gr.js`; una ruta directa de giro puede usar dos campos aunque exista middleware inactivo.

Las compras conservan el tipo del selector (texto o número) y el dominio demostrado. Una compra sin selector sólo es ejecutable cuando hay una única opción anunciada. Un mapa numérico finito puede probar opciones conocidas; no autoriza valores adicionales ofrecidos por el servidor.

## Rutas de compra mixtas

Un cliente puede contener un emisor con `selected_mode=t+1` protegido por un dominio finito y otro emisor con `selected_mode=t` sin dominio resuelto. Antes, esa segunda ruta anulaba también la primera y dejaba todas las compras pendientes. Ahora se conserva la ruta finita demostrada y se registran sus límites en `purchase_input_routes`.

Sólo se omiten alternativas desconocidas cuando las rutas conocidas son finitas. Tipos incompatibles, dominios abiertos y formatos sin prueba siguen pendientes. Las opciones fuera del dominio no se fabrican.

## Continuación y cierre

Se ejecutan únicamente transiciones demostradas y acciones anunciadas: inicialización de bonus, respins, giros gratis y sus cierres. La recuperación de una ronda pendiente usa las mismas primitivas. `back_to` y la vuelta a spins requieren prueba del getter o del dispatcher; no basta que exista una función con nombre parecido.

Una ronda termina cuando `round_finished=True`, el estado actual es `spins` y `spin` vuelve a estar disponible. Cada compra se ejecuta una vez por prueba, con un máximo defensivo de 80 pasos de continuación y plazos de ejecución. Después se comprueban dos giros base consecutivos. Alcanzar un límite deja el resultado pendiente.

## Registros y límites

`client_contracts.py` permite reutilizar contratos aceptados por huella del cliente o por huella exacta del handler y su llamador cuando la fuente no cambió ni se contradice. La caché de activos públicos distingue URL y revisión. No se reutiliza ciegamente una versión anterior.

La selección activa de solicitudes no depende del nombre del juego. `observed_game_rules.json` conserva perfiles históricos para aprendizaje y pruebas fuera de línea; no sustituye el análisis actual del cliente. Hay sintaxis todavía no reconocida y fallos de disponibilidad del proveedor que pueden producir PARCIAL.

[Validación y caso de regresión](VALIDATION.md). [Criterios de detección](FEATURE_DETECTION.md).
