# Revisión autónoma de primitivas — 13 de octubre de 2026

Se usó Tester-Spin para repetir pendientes con sesiones demo nuevas y el fuzzer MCP solamente para estructuras desconocidas representativas. Los resultados parciales no se convierten en OK por catálogo, por captura histórica ni por una respuesta HTTP exitosa.

## Correcciones compartidas comprobadas

- 3 Oaks: selección dependiente de versión y rama activa del módulo de compras. Lucky Penny y Coin UP: Lightning cerraron giro y compras con OK.
- Red Tiger: resultados inline de respins liquidados, estado NSP con contenedores vacíos, adquisición acotada de selectores y muestreo de acciones recurrentes. Astronaut, Cannonball Cash y Book Of Desert Legends cerraron con OK; la tanda compartida produjo otros nueve OK.
- BGaming: seguimiento del argumento reenviado hasta el transporte JSON-RPC, sin contar todas las funciones genéricas del cliente como compras del juego. Blackbeard’s Bounty terminó giro, ante y dos compras con OK. Otros clientes HyperHive siguen sin contrato probado.
- Pragmatic: declaraciones de inicialización con claves JS sin comillas, activación de compra contrastada con purtr/puri, comprobación de apuesta bl, pruebas actuales y cuotas de muestras; migración de obligaciones históricas solo con origen y RAW correspondientes. Bloody Dawn terminó con OK. Los respins de tres ciclos admiten bloques de cobro estrictamente informativos; Chilli Heat Megaways terminó tres modos con OK.
- KA: User-Agent HTTP Windows coherente con contexto firmado y perfil instalado; descriptor registrado con metadatos antes del constructor; dos giros base obligatorios y conservación de la apuesta en cada continuación. ThreeMonkeys y FiveGodsOfWar terminaron con OK; la segunda tanda convirtió otros ocho pendientes en OK.

- Yggdrasil: compras BUY/BUY_BONUS y antebet GOLDEN_BET declarados por el servidor; animaciones por nombre con campos estrictos y artefactos reproducibles. E Force terminó giro y dos compras; Buffalo Freedom Doublemax terminó giro, tres compras y un antebet, ambos OK.

## Evidencia y límites

La suite final dio 1240 pruebas y 254 subtests correctos; quedan tres advertencias preexistentes del lector HTML. Las revisiones independientes verificaron los nuevos controles y sus casos negativos.

El fuzzer de Chilli detectó dos controles pero terminó PARTIAL por QUIET_TIMEOUT: sus clics no prueban ejecución. La ejecución actual de Tester-Spin y sus artefactos de retorno al base son la evidencia del OK. Se conservó una captura independiente completa de bootstrap y cliente (68 entradas), no una compra verificada por el fuzzer.

Los HAR completos del navegador están en Downloads/HardFire-HARs. KA y Yggdrasil también guardan los intercambios API íntegros, incluyendo errores y estados desconocidos, en analysis/http.har dentro de cada prueba local; estos no incluyen recursos de navegador ausentes del ejecutor HTTP. La captura de KA incluye bootstrap y giro; las capturas de BGaming incluyen compras y ante. Las capturas contienen sesiones y no se publican en el repositorio. Los fixtures de regresión contienen fragmentos sintéticos o sanitizados.

## Lo que sigue pendiente

- Yggdrasil: la autenticación devolvió HTTP 429 durante la primera tanda; una nueva prueba posterior de 3 Gladiators Vs Caesar terminó OK con nueve opciones ejecutadas y retorno confirmado. La tanda se detuvo después de identificar familias desconocidas; los casos nuevos conservan HAR de API para aprender sus primitivas. No se certificó todo el catálogo.
- Belatra: error TLS del host enlazado por el catálogo y HTTP 403 en la alternativa oficial observada. No se omite la verificación TLS.
- BGaming: otros clientes sin wire-shape de play certificado; no se adivina la petición.
- KA: la cola sin pruebas previas produjo treinta OK nuevos antes de recibir una serie de HTTP 404. El mismo rechazo apareció después en ThreeMonkeys, previamente OK, tanto con identidad Demo aleatoria como con la identidad pública actual del launcher. No se atribuye esa serie a primitivas de cada juego. Se detuvo la tanda; la señal del proveedor y el HTTP 429 se propagan ahora entre workers aislados, evitando iniciar más sesiones.
- Hacksaw/RubyPlay/KA: estados o dominios específicos aún desconocidos; se conservan los RAW y no se inventa una compra o elección.
- Pragmatic: obligaciones de elecciones naturales que no reaparecieron en la nueva sesión, cuotas históricas y algunas continuaciones sin contrato. Las compras no reemplazan la prueba de una elección natural.

El archivo local autonomous-provider-status.json contiene la distribución actual por proveedor. Las tandas y capturas locales no certifican todo el catálogo.

## Entrega instalada

El ejecutable del acceso directo del escritorio fue reemplazado por la compilación final y su prueba de arranque terminó OK con los diez proveedores. El estado final registra 69 OK adicionales respecto del inicio de la tanda: 45 en KA, 12 en Red Tiger, cinco en Yggdrasil, dos en 3 Oaks, dos en 1spin4win, dos en Pragmatic y uno en BGaming. No significa que los pendientes restantes estén certificados ni que todos los OK antiguos se hayan repetido en esta tanda.
