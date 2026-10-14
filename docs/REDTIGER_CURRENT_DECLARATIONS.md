# Red Tiger: declaración vigente de compras

La sesión oficial devuelve SETTINGS.result.game. hasFeatureBuy=false acredita cero compras, aunque existan plantillas en featureBuy o nombres de bonos en features. Con true, el detector exige featureBuy y mathModes no vacíos: nombres únicos, precios positivos finitos y el mismo mapa nombre/precio; cada mathMode debe tener type=featureBuy. Una declaración incompleta o contradictoria no certifica la cantidad.

Los HAR de Evolution del 11 de octubre contienen Red Tiger: la identificación corresponde al protocolo del juego, no al sitio que aloja el catálogo. El cliente bars-next observado habilita el menú con options.hasFeatureBuy y construye sus opciones con options.featureBuy. mathModes corrobora las opciones activas y sus costes. No se cuentan las solicitudes ejecutadas ni las variantes de bonos naturales.

Se usa la configuración de la sesión nueva en cada prueba, no la sesión o un listado de títulos del HAR. Las compras corroboradas se registran como SERVER_DECLARED, separadas de CLIENT_OBSERVED. Se envían por extras.features.featureBuy y featureBuyCost. El resultado operativo todavía exige las verificaciones de respuesta y cierre existentes; una cantidad conocida no convierte automáticamente un juego en OK.

## Casos de regresión

| Juego de la captura | Compras declaradas |
| --- | --- |
| 10001 Nights | 0 |
| Ali Baba’s Luck | 0 |
| Spooky Carnival | 0 |
| Big Cat Rescue Megaways | 0 |
| 777 Diamond Strike | FreeSpins: 100 veces la apuesta |
| Monopoly Money Magnate | FreeSpins: 50; HoldRespins: 20 veces la apuesta |

Estos nombres aparecen exclusivamente en ejemplos y fixtures de pruebas. No condicionan el código. FreeSpins identifica la compra de tiradas gratis; HoldRespins conserva el identificador de la compra Hold & Respin. Un tipo nuevo conserva su identificador de protocolo, sin inventar una traducción. La ausencia de antebet no se deduce de hasFeatureBuy ni de gameModes vacío.

Los fixtures almacenan únicamente declaraciones públicas, sin tokens o sesiones. Las pruebas verifican las seis capturas, contradicciones, datos ausentes, plantillas deshabilitadas y ejecución/cobertura/resumen de las dos compras con un nombre de juego distinto.

## Estado persistente y regreso al giro base

hasState=true no basta para identificar una ronda pendiente. Los HAR del 11 de octubre de Cash Ultimate y Case Closed muestran giros Normal, gameMode=0 y features=[] que conservan símbolos/acumuladores entre rondas pagadas independientes. El criterio genérico conserva todos los rechazos de elección, bonus y estado sin interpretar; adicionalmente admite un único resultado Normal con estado persistente si la solicitud es un giro base sin compra/bonus, la apuesta positiva coincide con el stake devuelto, el roundId entero aumenta, el saldo inicial enlaza con el saldo final anterior y el servidor acredita exactamente apuesta cobrada y premio total liquidado. Importes ausentes, no finitos, no concordantes o rondas repetidas permanecen sin confirmar.

El comprobador usa la respuesta anterior de la misma sesión y requiere dos rondas base consecutivas verificadas. No usa títulos, campos particulares como lockedTiles/progress/suspects, ni límites artificiales del acumulador. Esto verifica retorno a giros pagados normales; no certifica cobertura de todos los bonos naturales posibles.

La captura capture_20261011_141247.har únicamente contiene recursos del catálogo Evolution; no tiene settings/spin/choice del juego. No sirve como evidencia de una ronda del tercer juego.

12 de octubre: 10,001 Nights omite spinMode; se admite gameMode=0 con mandatoryFeature exactamente false y las mismas pruebas de cobro, liquidación y ronda independiente. mandatoryFeature=true siempre impide certificar regreso al base. Los dos HAR adjuntos capturan el mismo gameId; new-tab-page-home no contiene protocolo del juego.

## Cobertura de la compra y resultado NSP

Las compras confirmadas definen required_options con su selector de protocolo. Una ejecución validada acredita validated=true y covered_options para ese selector. Esto corrige DOMAIN_UNRESOLVED cuando la compra ya había sido ejecutada correctamente: declarar una opción no es ejecutarla, y un HTTP exitoso por sí solo no marca cobertura. Se conservan los controles de respuesta, elección y regreso al juego base.

El formato NSP con estado persistente se admite solo con el sobre exacto win/nsp/hasState, resultado normal nsp.reels y nsp.spinning y un único nodo de resultado, además de la evidencia financiera y de ronda independiente. El stake en win y nsp debe coincidir con el solicitado. Las variantes Ali Baba’s Luck Megaways y Power Reels de los HAR del 12 de octubre reproducen este contrato; no hay condiciones por título.

Los HAR de 777 Diamond Strike, 777 Super Strike y Arc of Zeus declaran una compra FreeSpins de 100 veces la apuesta y contienen su ejecución. El pendiente falso correspondía al registro de cobertura, no a la cantidad de compras. Los resultados anteriores no se alteran: se recalculan al volver a probar el juego.

Para acreditar la compra se exige también recibo: selector y coste solicitado coincidentes con la declaración, débito exacto de ese coste y bonus o elección devueltos. Una respuesta Normal que ignore extras no cubre la opción. Las tres compras de los HAR del 12 de octubre satisfacen este criterio.
