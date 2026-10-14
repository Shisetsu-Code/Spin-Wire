# Yggdrasil Demo Executor Implementation Plan

> For agentic workers: use superpowers:executing-plans to implement each task inline.

Goal: sustituir PARCIAL incondicional por ejecución Demo verificable.
Architecture: runtime por contrato API 2.6.0, dominio Modes y monedas Denoms actuales; máquina de estados wager/bets; integración con verify_return_to_base y GameTestResult.
Tech Stack: Python, curl_cffi, pytest.
Spec: docs/superpowers/specs/2026-10-11-yggdrasil-demo-executor-design.md

## Global constraints
Solo servicio oficial Demo; ninguna credencial histórica; ningún ID o título como regla; jamás usar isFinished de animación como cierre; dos ciclos normales consecutivos para retorno; comandos desconocidos pendientes.

## Review focus
Precio/moneda inválidos; respuesta con modo o importe distinto; wagerid/pasos inconsistentes; comandos no soportados; captura histórica confundida con prueba actual. Todos se ejercitan en tests/test_yggdrasil_runtime.py.

## Task 1: Runtime y máquina de estados
Create tester_spin/providers/yggdrasil/runtime.py. Interfaces: configuration(data,gameid,currency)->config con modes/templates; wager_state(payload)->estado; DemoRuntime.round(template,directory)->resultado con terminal/base, comandos y trazas sanitizadas.
- [x] Crear fixtures sanitizados de los dos HAR y tests negativos/positivos; verificar rojo.
- [x] Implementar configuración, bootstrap Demo y ejecución C con wagerid actual y max(step)+1.
- [x] Verificar tests y validación de precios, identidad y progreso.

## Task 2: Integración y aceptación
Modify adapter.py test_game, SPEC y documentación. Usar configuración actual para giro y BB, repeticiones por modo, retorno común y evidencia por intento.
- [x] Test de adaptador con transporte simulado y fixtures reales, incluyendo dominios desconocidos y fallos inciertos.
- [x] Sustituir recorrido pasivo manteniendo fallback sin bootstrap ejecutable.
- [x] Probar ambos juegos Demo sin identidades anteriores; suite completa, revisión, construir e instalar EXE del escritorio.

## Execution ledger

Task 1: pruebas rojas de runtime inexistente, primitivas implementadas y verificadas. Task 2: integración antes devolvía PARCIAL (tests rojos); transporte simulado + capturas y Demo real verifican los recorridos.

Ruling: la configuración por modo contiene precios completos y permite reconstruir plantillas sin HAR por título para el contrato API demostrado; evita depender de capturas antiguas por cada juego. Si un dominio no aporta precios, permanece pendiente.
Ruling: numeric index launchers oficiales son otra vinculación válida de identidad; regla por URL y parámetros, nunca por lista de IDs.
Ruling: C puede devolver solo la apuesta final; exigir RESULTED en todas las apuestas previas antes de cobrar protege obligaciones pendientes.
Ruling: dos dialectos de respuesta (featuresUsed/actions) prueban modo base, siempre además de liquidación financiera de wager. Las selecciones naturales no demostradas no se automatizan.

Aceptación Demo actual: representantes 10511 y 10945 OK 5/5 y 6/6 respectivamente; los IDs aparecen únicamente como evidencia de pruebas, nunca como regla del ejecutor. Suite final: 1198 pruebas y 254 subtests aprobados. Escritorio construido, instalado y smoke-test OK (10 proveedores).

Final: detectado bloqueo HTTP429 en authenticate tras tandas repetidas; implementado ritmo de 1s compartido y respeto de Retry-After/60s, sin reintentos de pagos. Esperas superiores al timeout no envían peticiones ni cuelgan el siguiente juego. Los dos recorridos completos previos están preservados en los artefactos de aceptación, y los bloqueos posteriores se registran por separado como ERROR.
Ejecutable instalado: C:/Proyectos/Tester-Spin/Tester-Spin.exe, SHA256 55B2ED93F3DB0087377352B17A84DDD1574DA90253B35F1EAF7F03A52F2BB4F5. Acceso directo del escritorio verificado.


## Ampliación del catálogo — 2026-10-13, en curso

- [x] Pasada de los 151 registros inicialmente sin OK y análisis local de familias desconocidas.
- [x] Roles actuales Config.bettingModes, formatos clásicos y typed/numeric, elecciones del servidor sin gamble y artefactos completos de estructuras conocidas.
- [x] Regresiones de controles desconocidos, flags, importes, monedas, grupos, tipos malformados y coordinación del Retry-After entre procesos.
- [x] Suite offline: 1488 pruebas +254 subtests, tres advertencias HTML previas.
- [ ] Confirmar el grueso del catálogo en nuevas sesiones después de la pausa oficial.

Estado real de la cola: 39 OK /159, 95 PARCIAL y25 ERROR. La pasada se detuvo
ante Retry-After=3590; no se repiten peticiones antes del plazo. Las capturas
anteriores seleccionan candidatos, pero cada trabajador vuelve a autenticar y
consulta configuración vigente. No se promueven juegos por replay offline.


## Resultado de la ampliación del 2026-10-13

98 OK /159, 48 PARCIAL y13 ERROR. Mayoría verificada en vivo; las familias
reconocidas no dejan candidatos por ejecutar. Los pendientes continúan como
trabajo de aprendizaje de contratos, no como cierre supuesto. Ver el corte y
primitivas vigentes en docs/YGGDRASIL.md. Verificación: 1572 pruebas,
254 subpruebas; ejecutable del escritorio instalado y smoke test OK.


## Continuación del 13 de octubre: ejecutable v11

Nuevo corte: 111 OK /159, 34 PARCIAL y 14 ERROR. Trece OK adicionales con
primitivas comunes de geometría, menús de rechazo de riesgo, cobro C con
marcador *, progreso de nivel, fragmentos vacíos y precios con descuento.
Pushy confirma 2 compras +1 antebet; se archivan obligaciones históricas de
precios preservando evidencias y cuota máxima. 1605 pruebas y254 subpruebas
aprobadas. Ejecutable de escritorio instalado y smoke-test con10 proveedores OK.
SHA256: 959409D67F9D9FB49455CA40195BBAD0D4A60FE42D922688FCA1654F193977D0.
No se amplió el backend Play for Fun ni se extendió el serializador escalar
a listas explícitas sin evidencia. Las familias no aprendidas siguen pendientes.


## Checkpoint v12, 13 de octubre

115 OK /159, 30 PARCIAL, 14 ERROR. API2.7 transport +geometría de alturas
variables estables, splitFields y paneles de jackpots inactivos verificados.
ActionGame_ de efectivo vincula normalización al importe pagado, controla
secuencia/moneda/totales y conserva el envelope para reconstrucción. Una
regresión en featuresOutputs fue detectada por la suite y corregida.
1623 pruebas y254 subpruebas aprobadas. Ejecutable instalado y smoke-test OK.
SHA256: F82F020F8AEAFAC7A533F531EA5BF819F51C5BE3688CD4E6B6EC06DC9E17BF96.

## Checkpoint v13, 13 de octubre

116 OK /159, 29 PARCIAL, 14 ERROR. Bonus parametrizado conserva el premio
con eco exacto; Calavera completo y PROMOTED. BBG reinicia las flags pero exige
freeSpinState y progreso unitario; las cascadas positivas de Florageddon
permanecen pendientes. No hay excepciones por título o ID.
1647 pruebas y 254 subpruebas correctas; escritorio instalado y smoke-test OK.
SHA256: D94C7C229F779E019A0D4AF39FB0DD8CD05EE2883C8A4B56C2D551B146EF5DE7.

## Checkpoint v14 — 2026-10-13

Florageddon PROMOTED en pasada 27: los cuatro modos completaron cierre y retorno.
117 OK /159, 28 PARCIAL y 14 ERROR. BBG usa Config.definition actual para validar
cascadas, roles wild, posiciones, ExtraLife y premios; reconoce grant directo
de FreeSpin, conserva disparador y distingue premio actual del acumulado.
1692 pruebas correctas. Ejecutable del escritorio instalado y smoke OK.
Launcher staticpff original consultado sin modificar parámetros: HTTP 403;
los rechazos authenticate siguen pendientes, sin cambio especulativo de backend.

## Checkpoint v15 — 2026-10-13

Primitiva supermeter: LS carga antes de C; acuses y cash-out contrastados.
Máscaras neutrales y precio BASIC prueban retorno. Dark Joker Rizes PROMOTED
en pasada 28. 118 OK /159, 27 PARCIAL, 14 ERROR; 1700 pruebas correctas.
Build v15 instalado, smoke Exit0. No excepciones por nombre o ID.

## Checkpoint v16 — 2026-10-13

Tanda por familias: SDK dinámico de modos con exclusiones golden y precios de
Modes; rondas numéricas en centavos y estado neutral de portales declarado.
Bloody Pesos, Red Dragon Sails y Your Own Island PROMOTED en pasadas 29–30;
Dark Vortex PROMOTED en pasada 31. Cuatro nuevos OK con reglas compartidas.
Regresión de interceptación de otros DTO enum corregida ligando el perfil al
constructor verificado. Suite completa: 1721 pruebas, tres warnings HTML.
Corte: 122 OK /159, 23 PARCIAL, 14 ERROR. Build v16 instalado y smoke Exit0.

Checkpoint v17: 124 OK /159, 21 PARCIAL, 14 ERROR. Acciones nombradas ampliadas con evidencia de HAR; resultados cerrados desconocidos detienen el probe sin repetir giros. Pasada 32: Enchanted Waters y Ragnaravens Wildenergy PROMOTED. Suite 1731 pruebas correctas; instalación y arranque verificados.

## Checkpoint v18: símbolos móviles

La primitiva compartida contrasta walkingBefore/After/New con desplazamiento de una columna, máscaras stickyA/B/N, geometría, posiciones, ciudad constante, premios de cada paso y acumulación monetaria. Exige cero cargo en continuaciones y cobro final; la validación de transporte mantiene identidad de ronda y comandos anunciados. Una secuencia completa reconocida puede reiniciar la búsqueda de retorno; no sustituye los dos giros ordinarios consecutivos. Estados o controles desconocidos siguen pendientes.

Pasada 34: Orient Express PROMOTED en sesión nueva, cobertura 1/1, cierre y retorno confirmados. Corte instalado: 125 OK /159, 20 PARCIAL, 14 ERROR. Suite completa: 1747 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v19: acumulador persistente declarado

CollectionsCapacity de la configuración actual determina la capacidad por columna; collectionMeter.amounts debe coincidir con la longitud de values. Los valores son cantidades finitas no negativas y cada colección permanece por debajo de su capacidad. Una colección incompleta guardada no exige continuación por sí sola. Sin capacidad válida, con colección completa, controles de premio, continuación o campos desconocidos, la respuesta conserva revisión pendiente. No se fijan capacidades por juego ni se descarta el estado original del HAR.

Pasada 35: Tuts Twister PROMOTED en sesión nueva, dominio 1/1 cerrado y dos giros ordinarios consecutivos comprobados. Corte instalado: 126 OK /159, 19 PARCIAL, 14 ERROR. Suite completa: 1764 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v20: estado neutral de símbolos persistentes

El contrato neutral exige modo desactivado, contadores emperorShift/previousEmperorShift/newWildCount enteros en cero, preStickyWilds y postStickyWilds vacíos y penguinAction ausente o false. Estados activos, acciones de reemplazo, posiciones persistentes y controles desconocidos conservan revisión pendiente. Son campos de protocolo compartidos, sin selección por título ni ID.

Pasada 36: Penguin City PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno ordinario confirmado. Corte instalado: 127 OK /159, 18 PARCIAL, 14 ERROR. Suite completa: 1774 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v21: estado ordinario de estación

El perfil de estación exige declaración actual completa de los cuatro conjuntos normales y sus variantes de función especial, con columnas y símbolos válidos. currentSeason debe concordar con su conjunto normal; numberOfSpins es un contador entero acotado. No se aceptan conjuntos Feature como retorno ordinario. El multiplicador de FALL ya está aplicado en wtw; su suma debe concordar con wonCoins, accC y accWa usando la moneda actual. No se aplica nuevamente el multiplicador. Campos y controles desconocidos permanecen pendientes.

Pasada 38: Seasons PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 128 OK /159, 17 PARCIAL, 14 ERROR. Suite completa: 1788 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v22: repeticiones premiadas devueltas por el servidor

El estado neutral exige contador cero, multiplicador uno, premios nulos e indicadores desactivados. La secuencia premiada contrasta geometría de símbolos grandes, conjuntos y posiciones, premios anteriores/posteriores al multiplicador, acumulación monetaria, apuesta inicial actual, continuaciones sin cargo y cobro final. El cliente usa finalBoard directamente; se conservan ambos tableros y se valida su geometría sin exigir igualdad. Una secuencia cerrada reconocida permite continuar la búsqueda de dos giros ordinarios consecutivos; no sustituye esa prueba.

Los premios directos de copa se contrastan con BaseSilverCupPrizes y BaseSilverCupDistribution. Solo se aprende el tipo de monedas y su conservación; Football Glory permanece pendiente por otra respuesta que aumenta el progreso. No se fija el umbral del cliente en el ejecutor.

Pasada 42: Hyperburst PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 129 OK /159, 16 PARCIAL, 14 ERROR. Suite completa: 1818 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v24: cascadas de giro base y tiradas gratis

Se valida la secuencia completa de tableros, posiciones ganadoras y desplazamientos, multiplicadores, premios anteriores/posteriores, acumulación de moneda y efectivo, cargos cero en continuaciones y cobro final. Las repeticiones mantienen el contador de tiradas gratis; los giros consumidos lo reducen. NO_REEL_SET identifica el relleno de una cascada después de una repetición anunciada. El saldo initialBalance se valida como dato numérico, conservando el HAR original.

Una cascada BASIC validada hasta el cobro, sin dominio de tiradas gratis, constituye el giro base completo. Una secuencia con freeSpinsAwarded conserva su clasificación de función separada. La prueba de retorno sigue exigiendo dos rondas ordinarias consecutivas. Campos desconocidos, contadores incoherentes y premios o geometría inconsistentes siguen pendientes.

Pasada 47: Vault Of Fortune PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 130 OK /159, 15 PARCIAL, 14 ERROR. Suite completa: 1844 pruebas correctas, tres warnings. Arranque del escritorio verificado. v23 fue una compilación intermedia; la actualización instalada es v24.

## Checkpoint v25: cantidades de funciones guardadas

Icons, WindowHeight y los carretes NReel de la configuración actual fijan el dominio de símbolos, mapas, orden y posiciones. La respuesta neutral exige featureBefore/After e initialPlayerState/playerState iguales, cantidades enteras no negativas, premios nulos y capsCount cero. El campo feature activa la función en el cliente; las cantidades guardadas no la activan por sí solas. Cambios de cantidades, indicadores de función, repeticiones o controles desconocidos conservan revisión pendiente.

Pasada 48: Spina Colada PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 131 OK /159, 14 PARCIAL, 14 ERROR. Suite completa: 1852 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v26: colecciones y repeticiones de giro base

SpinTypes, BaseReels/RespinReels y los límites de salud/progreso de la configuración actual delimitan la primitiva. La secuencia contrasta cada cambio de combate con beforeCollections/collections, preserva posiciones y máscaras de símbolos persistentes, comprueba premios y acumulación monetaria, cargos cero en continuaciones y cobro final. Una repetición anunciada puede ocurrir sin combate. Un combate de cambios cero y un contador de símbolos vistos no activan una función por sí solos. No se acepta ninguna recompensa de tiradas gratis dentro de esta primitiva base.

newUser es un indicador booleano de inicialización; puede comenzar verdadero y debe quedar falso al cerrar el estado. Los estados y controles desconocidos conservan revisión pendiente. Una secuencia base completamente validada cuenta como ronda ordinaria tras el cobro; el retorno sigue exigiendo dos rondas consecutivas.

La prueba concurrente encontró una carrera al inicializar el archivo de coordinación Windows antes de adquirir su bloqueo. La inicialización ahora ocurre dentro del bloqueo, conservando el Retry-After más largo entre procesos. La suite completa incluye esta comprobación real entre procesos.

Pasada 54: Wolf Hunters PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 132 OK /159, 13 PARCIAL, 14 ERROR. Suite completa: 1877 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v27: reemplazo de scatters y movimiento explícito

EdgeScattersReplacementIcon, EdgeScattersIsColumnBanned, Icons y BaseReelsSupplierConfig del servidor delimitan el reemplazo. La primitiva contrasta columnas, símbolo configurado, conjuntos normales de carretes, posiciones del caminante y tablero final. Los tableros explicados por esos dos efectos se reconocen como resultado ordinario; premios de tiradas gratis, efectos o cambios adicionales desconocidos siguen pendientes. Los valores y posiciones proceden de la configuración y respuesta, sin excepciones por juego.

Pasada 55: Aldos Journey PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 133 OK /159, 12 PARCIAL, 14 ERROR. Suite completa: 1885 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v29: tarjetas de compra y aceptación del premio

El perfil de tarjetas enlaza el menú, sus confirmaciones y comandos con el dominio actual de Modes. Las denominaciones completas, sus valores predeterminados y coinsPerBet deben coincidir con la relación de precios del cliente. El papel de compra no se infiere del coste ni del alias del comando. La aceptación de free spins se obtiene del control oficial y solo se ejecuta frente al premio y menú actuales; las continuaciones deben conservar la ronda y tener coste cero. Los premios de línea simultáneos se contrastan con la moneda BASIC actual, separadamente del precio de adquisición.

Pasada 59: Shaker Club PROMOTED, 5/5 opciones recorridas, giro normal y ambas compras cerrados con retorno confirmado; cero ramas pendientes. Evidencia: tests/20261013-174015-2bb54b. No hay excepciones por juego en estas primitivas. Corte instalado: 134 OK /159, 11 PARCIAL, 14 ERROR. Suite completa: 1915 pruebas correctas y tres warnings. Arranque de escritorio verificado.

## Checkpoint v30: dominio clásico fijo y estado base vacío

Cuando CoinsPerBet no existe como dominio separado, una declaración MinCoins == MaxCoins == Modes.BASIC.coinsPerBet demuestra una cantidad fija de monedas. Esa cantidad se valida independientemente del número de líneas; no se copian valores del cliente ni se introducen excepciones por título. Ajustes de moneda nulos producen un modo explícitamente pendiente sin inventar precio.

El cliente distingue thisWilds, addedWilds y nextWilds de sus variantes fs. La terna base completa y vacía se reconoce junto con el tablero, importes y comandos normales del protocolo clásico. Campos incompletos, tipos distintos, estados activos y metadatos de free spins quedan pendientes.

Pasada 60 obtuvo las primeras jugadas de este dominio; pasada 61 confirmó Golden Monkey PROMOTED, dominio 1/1 cerrado y retorno normal confirmado. Evidencia: tests/20261013-174947-88ecd0. Corte instalado: 135 OK /159, 10 PARCIAL, 14 ERROR. Suite completa: 1935 pruebas correctas, tres warnings. Arranque del escritorio verificado.

## Checkpoint v31: cascadas ordinarias y ciclo de compras concedidas

La configuración actual delimita la geometría y los precios. La primitiva valida los tableros, desplazamientos con crecimiento o altura estable, combinaciones anunciadas y suma de payouts. Los multiplicadores pertenecen a cada tablero de respuesta; los payouts ya incluyen su efecto. Un multiplicador positivo por sí mismo no identifica compra ni antebet.

Una compra concedida puede reutilizar su comando en todas las tiradas del premio. Se exige el precio de adquisición actual, comando ofrecido y type=bonus, coste nuevo cero, identidad de ronda, paso siguiente, estados enlazados, contador decreciente y conservación del pago acumulado. El cobro final y dos giros BASIC cerrados prueban el retorno. Si el estado inicial conserva marcas, multiplicador o alturas de un bonus agotado, el giro BASIC actual puede limpiarlos; tiradas todavía pendientes y estados actualmente activos no se ignoran.

La revisión por lotes inicial reconoció 50 respuestas de nueve capturas. Pasada 69: Candyfinity PROMOTED, 7/7 opciones recorridas; BASIC, BUYBONUS, BUYMAXBONUS y GOLDENBET cerrados con retorno confirmado y cero ramas pendientes. Evidencia: tests/20261013-182559-d71a61. No se añadieron excepciones por título o ID. Corte instalado: 136 OK /159, 9 PARCIAL, 14 ERROR. Suite completa: 1974 pruebas correctas, tres warnings; arranque del escritorio verificado.

## Checkpoint v32: tarjeta única y pagos de ambos lados

El perfil sdk.confirmedSinglePurchaseCard/serverPriceDomains/v1 enlaza la tarjeta de compra, su confirmación y el constructor de la petición. Extrae comando, factor y cantidad de monedas del cliente y contrasta todos los precios y valores predeterminados con Modes y las denominaciones actuales. No asigna roles por título, ID ni alias del comando.

La cantidad de free spins se obtiene del premio actual freeSpin.added; la entrada requiere el comando del cliente también ofrecido por el servidor, precio correcto y coste nuevo cero. Las rondas BASIC validan premios de izquierda y derecha, coordenadas, transformaciones de tablero y total de la jugada. Los respins automáticos devueltos conservan la identidad del grupo, desplazan las posiciones retenidas al extremo inferior de cada columna y deben agotarlas antes del cobro. cashWin es el pago de una ronda; winSum acumula las rondas. No se confunden estos efectos ordinarios con compras o antebets.

Pasada 72: Defenders Of Mystica PROMOTED, dominio 3/3 recorrido, giro y compra cerrados con retorno confirmado y cero ramas pendientes. Evidencia: tests/20261013-190127-fb5a74. Corte instalado: 137 OK /159, 8 PARCIAL, 14 ERROR. Suite completa: 2016 pruebas correctas, tres warnings; arranque de escritorio verificado.
