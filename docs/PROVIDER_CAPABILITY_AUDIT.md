# Declaraciones de compras y antebet

Actualización: 2026-10-13. La auditoría combina capturas completas, código del
cliente actual y ejecuciones nuevas. Un resultado histórico no valida una sesión
nueva ni certifica todas las opciones del juego.

## Regla común

La configuración efectiva determina las opciones esperadas. Los HAR enseñan el
serializador, los acuses y las transiciones; el número de peticiones capturadas no
es el número de compras disponibles. No se decide por nombre de juego.

Cada resultado conserva `feature_domains` por categoría, con `source`, `options`
y `complete`. Una declaración completa y vacía acredita cero. La ausencia de
configuración mantiene el total sin confirmar. Un giro normal no demuestra
que no existan compras o antebets.

El OK exige ejecutar los contratos conocidos, resolver decisiones anunciadas,
validar el cierre y comprobar el retorno al giro normal. No se fuerza OK ante
comandos desconocidos, muestras insuficientes o fallos del servidor.

## Autoridad por proveedor

| Proveedor | Fuente y límite |
|---|---|
| Pragmatic | `doInit.purInit/purInit_e` y `bls`. Tablas con claves JS sin comillas se leen sin ejecutar código; claves duplicadas, precios inválidos y máscaras inconsistentes quedan pendientes. La cobertura de compras exige `purtr=1`, `puri` correcto y cierre; antebet exige `bl` aceptado. Ambos necesitan las muestras y dos giros base. |
| Belatra | `enter.gs.buyBonus.buyTotalBetK` y `vipMode.vipBetK`. Índices/claves declaran compras; `vipOn` se contrasta con el estado efectivo. Campos ausentes no acreditan cero. |
| 3 Oaks | Configuración `start` y selector del cliente vigente. Se admite la asignación de versión con o sin paréntesis y la rama de módulo nuevo solamente cuando su predicado se demuestra con la configuración. No se envía la rama antigua por ensayo. |
| 1Spin4Win | Constructor y serializador específicos del cliente. Compra y antebet se descubren independientemente; no existe una regla general de ausencia basada en un giro. |
| BGaming API | Multiplicadores y restricciones de la configuración efectiva; CHANCE y compras tienen dominios separados. |
| BGaming HyperHive | Contrato de `params.req` del cliente. Se sigue una copia íntegra demostrada por el serializador; comentarios, funciones reasignadas, propiedades ajenas y parámetros que ocultan el nombre no son evidencia. La lista genérica `purchased_features` no equivale al menú de cada juego. |
| Red Tiger | `hasFeatureBuy`, `featureBuy` y `mathModes` compatibles. Plantillas deshabilitadas no cuentan. Elecciones recurrentes y resultados inline se interpretan por estado, cierre y contabilidad, nunca por título. |
| RubyPlay | Configuración efectiva y cliente específico. Las elecciones de índice sin dominio demostrado mantienen PARCIAL. |
| KA Gaming | Herencia y descriptor registrado del cliente común vigente. Se reconoce el descriptor inline o el descriptor inicial con nombre construido inmediatamente mediante el constructor demostrado. Declaraciones condicionales o no ejecutadas no acreditan cero. |
| Hacksaw | `authenticate.bonusGames` y tipo de `FeatureBuyItem`. Compras y FeatureSpins se separan; tipos o continuaciones desconocidos siguen pendientes. |
| Yggdrasil | `fn=game.cfg.props.Modes` del mismo gameid; si existe, `Config.bettingModes` determina tipo y coinsPerBet y se contrasta con Modes. GB no se clasifica globalmente. Config.definition valida ANTE_BET con multiplicador/precio actual. El ejecutor Demo liquida elecciones y rondas conocidas y exige dos ciclos base. Ritmo/Retry-After persistentes entre procesos; un 429 no certifica el juego. |

## Método de trabajo autónomo

1. Tester-Spin vuelve a ejecutar los casos pendientes con sesiones nuevas.
2. Se agrupan los fallos para elegir representantes y se compara su estructura.
3. El fuzzer MCP y el analizador de HAR se usan para formatos desconocidos; no
   para repetir individualmente todo el catálogo.
4. Se conserva la captura original local y se extraen fixtures sin credenciales.
5. Una primitiva se prueba contra casos positivos y negativos, se revisa y luego
   se vuelve a contrastar con ejecuciones de otros juegos del proveedor.

Los requisitos antiguos solo se archivan con evidencia: RAW previo coherente,
contrato normalizado equivalente, origen idéntico y máximo de muestras históricas
y actuales. No se borra historia ni se comparte automáticamente una elección de
compra con una elección natural.

## Verificación y límites

Las pruebas reproducen las declaraciones, los serializadores, los acuses,
selecciones recurrentes, contabilidad, ausencia de controles y casos ambiguos.
La suite completa debe ejecutarse antes de actualizar el ejecutable del escritorio.
Los HAR completos permanecen locales; no se publican sesiones ni firmas.

Los bloqueos de transporte se informan separados de los huecos de protocolo.
Ningún total parcial del catálogo demuestra que todos sus juegos estén correctos.
Los resultados nuevos y sus diagnósticos son la evidencia operativa de cada OK.


Corte Yggdrasil del 2026-10-13: 122 OK /159, 23 PARCIAL, 14 ERROR.
Primitivas actuales y evidencia: [YGGDRASIL.md](YGGDRASIL.md). Se recuperaron
114 OK desde 8 mediante sesiones nuevas, sin excepciones por título o ID.

Modes fija comandos y precios actuales; bettingModes o un constructor de menú
oficial aprendido fija el rol. El SDK dinámico separa las exclusiones golden
del dominio de compras y contrasta sus tarjetas. No se infieren compras por
precio elevado ni por contar jugadas históricas. Los descuentos de BUY_A_BONUS
son variantes de precio de una compra, con MAX como opción distinta.

Checkpoint v16: tres juegos recuperados con el perfil de modos/rondas común y
Dark Vortex con configuración y estado de portales contrastados. Acumuladores
LS/C, Bonus parametrizado y cascadas BBG conservan las validaciones anteriores.
1721 pruebas correctas, ejecutable instalado y arranque verificado.

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


## Hacksaw: catálogo y elecciones, 2026-10-13

186 juegos oficiales contrastados: 185 OK y un ERROR de servidor. Se eliminó la
lista cerrada de nombres de elección del ejecutor y del inventario de muestras.
Los selectores proceden de possibleActions de la ronda actual; no se confunden
con el dominio de compras. Evidencia y límites: [HACKSAW.md](HACKSAW.md).


Auditoría posterior de Hacksaw: los 185 OK guardados acreditan ejecución/cierre,
pero no una certificación actual completa. Falta retorno posterior en 178 juegos
con opciones; 181 resultados son históricos. Véase [HACKSAW.md](HACKSAW.md).


## Hacksaw: corte con dinero y retorno verificados

Pasada nueva de los 186 juegos: 183 OK, 3 PARCIAL y 0 ERROR.
Cada OK contrasta precio declarado, débito, eventos acumulados, liquidación y
dos rondas BASIC nuevas posteriores. Los contratos antiguos no satisfacen el
contrato v2. Auditoría independiente sin discrepancias; 2047 pruebas correctas.
Evidencia y pendientes: [HACKSAW.md](HACKSAW.md).
