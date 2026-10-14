# Red Tiger: elecciones y resultados internos observados

Evidencia inicial: cinco HAR aportados el 12 de octubre de 2026 (11:09:29, 11:11:22, 11:16:09, 11:20:07, 11:25:38 UTC), contrastados posteriormente con ejecuciones nuevas del proveedor. El ejecutor aplica las primitivas documentadas; un HAR anterior no convierte por sí solo un juego en OK.

El explorador busca una oportunidad de selector durante un máximo de doce giros
normales ya cerrados. No repite compras para buscar esa oportunidad ni avanza si
la respuesta contiene un estado desconocido. Guarda los giros sin selector y
acredita únicamente acciones ejecutadas. Las escalas recurrentes confirmadas por
el servidor se cierran usando otra opción anunciada y requieren dos giros base
posteriores antes de acreditar su muestra.

## Elección remota pendiente

Astronaut captura 12 solicitudes spin y 13 choice, sin extras.features.featureBuy. Estas elecciones aparecen en rondas iniciadas por giros ordinarios: no son compras adicionales y no se debe asumir que solo existen dentro de compras.

La respuesta del spin anuncia result.game.choices={selected:null, available:["continue","collect"]}, hasState=true y transactions.roundId. La siguiente solicitud POST platform/game/choice contiene choice y el mismo roundId, usando la misma sesión. La respuesta puede conservar selected=null y ambas opciones; entonces la ronda sigue esperando otra elección aunque el HTTP y success sean correctos. gameData.selected puede contener "continue" aun cuando choices.selected siga siendo null: es la acción ejecutada, no una prueba de cierre.

Ejemplo de la captura: spin abre una ronda; continue conserva el selector pendiente; otro continue vuelve a conservarlo; un tercer continue devuelve choices.selected="continue", available=null y hasState=false. Otra ronda permite continue seguido de collect, cuyo resultado devuelve selected="collect" y hasState=false. No son tres compras ni tres rondas independientes.

Para reconstruir: almacenar estados y transiciones por roundId, opciones disponibles en cada respuesta, acción solicitada, gameData devuelto y cierre anunciado. No deduplicar transiciones repetidas ni detenerse solo porque gameData.selected esté poblado. Una ronda cerrada todavía requiere la comprobación separada del retorno al giro base.

## Picker ya resuelto en la respuesta

BloodSuckersMegaWays declara cuatro compras: FeatureCoffin (10x), FreeSpins (150x), FreeSpinsFour (500x) y FreeSpinsFive (1000x). La captura ejecuta las cuatro. No hay solicitudes choice.

Las compras de tiradas gratis incluyen picker.options (10 entradas), picker.choices (secuencia de índices y nombres) y arrays adicionales additionalSpins/multiplier. Se verificó que cada choices[].option es un índice base cero válido y que options[index].name coincide con choices[].name en las tres respuestas. Los nombres se repiten: el índice y el valor deben conservarse, no basta deduplicar nombres.

| Compra | Selecciones resueltas capturadas |
| --- | --- |
| FreeSpins | 3: RandomWilds[1], FatTiles[3], Multiplier[7] |
| FreeSpinsFour | 5: RandomWilds[1], FatTiles[2], FatTiles[3], AdditionalSpins[6], Multiplier[8] |
| FreeSpinsFive | 5: RandomWilds[1], FatTiles[3], AdditionalSpins[6], Multiplier[8], Multiplier[9] |

Los índices 6/7/8/9 corresponden respectivamente a AdditionalSpins=3 y Multiplier=2/3/5. En FreeSpinsFour aparecen cinco entradas porque FatTiles ocupa dos índices. Por eso el sufijo del modo no es una regla fiable para contar cartas o resultados internos.

La respuesta ya incluye la secuencia y sus efectos, hasState=false y las tiradas gratis calculadas. En este HAR el picker es evidencia de resultados entregados, no un choices.available pendiente. No se debe inventar una llamada choice. La ausencia de solicitudes posteriores respalda una presentación local, pero reconstruir la relación exacta entre clic físico y revelación requiere revisar el código del cliente; este HAR no incluye ese código de juego.

## Compra seleccionada frente a elección interna

Los dos HAR BigRichTurkeys capturan FreeSpinsRed, FreeSpinsBlue, FreeSpinsWhite y FreeSpinsAll. El selector viaja en extras.features.featureBuy antes de ejecutar spin. El servidor devuelve turkeys (spins, multiplier, prizes), mystery, tokens y freeSpins ya calculados, con hasState=false y sin endpoint choice. freeSpins[].instantWin.options describe resultados del bonus y no basta para declarar botones remotos ni compras nuevas.

AsianFortune contiene cinco giros sin compra ni elección observada; no contiene settings para certificar la lista exhaustiva de capacidades. Tampoco la captura de Astronaut contiene settings: las acciones observadas no certifican ausencia de compras.

## Datos para reconstrucción

Conservar por separado: configuración vigente de compras; solicitud de entrada y coste; resultado completo del bonus; selector remoto pendiente y su roundId; secuencia de acciones/estados; picker resuelto con índices y valores; estado terminal y prueba de regreso al giro base. Nunca sumar opciones internas al contador de compras. Ante estructuras nuevas sin contrato demostrado, dejar interpretación pendiente.

Se generó un registro JSON local saneado con índice de entrada HAR, solicitudes relevantes, declaraciones presentes, roundId, estados, gameData/picker y correspondencia de índices. Se verificaron todos los enlaces roundId de choice y los índices/nombres de picker sin discrepancias. No se incluyen tokens, cookies ni identificadores de sesión.

## Ejecutador actualizado

El ejecutor y el explorador de ramas guardan ahora choice_state y la transición antes/después, gameData y pickers resueltos. Leen de nuevo las opciones después de cada respuesta, conservando repeticiones en la misma ronda. Un esquema remoto sin selected/available explícitos o inválido genera advertencia y no se considera cierre confirmado. Las respuestas choice deben conservar el roundId y, si resuelven, confirmar la acción enviada; una advertencia detiene las siguientes selecciones de esa ejecución.

El recorrido principal conserva un límite de 64 elecciones por intento. Al alcanzar el límite con una elección pendiente sigue siendo PARCIAL; no se inventa cierre. La selección de una ruta de prueba no acredita automáticamente todas las ramas: se mantienen los controles existentes de cobertura y regreso al juego base. Un picker resuelto queda como evidencia de presentación y no genera solicitudes choice ni aumenta el contador de compras.

Cobra Queen (HAR 11:26:57) confirma otro resultado normal NSP con estado persistente. nsp.spinning es opcional y ya no se exige para validar el giro; el sobre reconocido win/nsp/hasState y las pruebas exactas de cobro, liquidación, stakes y avance de ronda se conservan. La captura no contiene settings, compras o elecciones, por lo que no prueba el catálogo exhaustivo de opciones del juego.

## Giro normal con escalera de decisiones

El HAR de Astronaut de las 12:29 muestra una única apuesta de entrada. Las solicitudes choice mantienen roundId y no descuentan otra apuesta: continue modifica progress.level y nextWin (premio potencial), y collect acredita el premio en cash.atEnd. Una continuación también puede terminar con premio cero. No interpretar progress.nextWin como dinero ya cobrado.

La comprobación de regreso al juego base ahora cierra elecciones anunciadas por cada giro de prueba, prefiriendo collect si aparece entre las opciones, y registra todas las respuestas. Certifica dos rondas pagadas normales y cerradas, no necesariamente dos respuestas sin selector. Exige débito inicial exacto, ausencia de débitos adicionales en las elecciones, continuidad de saldo, crédito exacto de cada premio, identidad de ronda, cierre remoto y componentes normales durante todo el recorrido. Bonus activos o resultados anidados de otro modo impiden certificar base. Las secuencias inline respin solo se aceptan como resultados ya entregados cuando contienen resultados completos con isLast=false en los intermedios e isLast=true en el último; no se confunden con los importes win.respin o winsMultipliers.respin.

Una recurrencia de la escalera se reconoce por dominio/roundId constantes, acuse de la acción y progress.level numérico avanzado. Se conserva el prefijo de entrada de esa escalera, por lo que una elección externa no se fusiona con ella. La cobertura exige ejecutar las acciones disponibles de la escalera; no multiplica la misma obligación por cada repetición ni afirma haber probado todos los niveles, importes o secuencias aleatorias. Los cambios de dominio o regresiones del contador mantienen rutas separadas. La traza completa de niveles y premios sigue disponible para reconstrucción.

Arcade Bomb omite spinMode y mandatoryFeature: gameMode=0 y las pruebas de ronda independiente pagada/liquidada permiten reconocer el giro base. Asian Fortune tiene un resultado NSP cerrado sin state=[]: las mismas pruebas financieras lo reconocen. Son reglas del formato de protocolo y no condiciones por título.

## Compatibilidad con pendientes históricos

Los marcadores de recurrencia son DIAGNOSTIC y coverage_required=false: explican la estructura y no representan una acción sin ejecutar. repeat_actions identifica únicamente acciones observadas que mantienen el selector abierto mientras avanza el nivel.

Con evidencia actual de acciones completas en la misma escalera, los pendientes históricos de profundidades repetidas se trasladan a policy_migrations bajo redtiger-depth-to-recurring-actions/v1. Se conserva el registro íntegro anterior y la evidencia de reemplazo. Solo se reemplazan prefijos estrictamente más profundos que la entrada, formados por acciones de repetición verificadas, con opciones pertenecientes al dominio actual y suficientes muestras. Prefijos de otra elección, acciones de cierre, opciones desconocidas y déficits de muestras permanecen pendientes. No se borra el historial de ejecuciones y no hay excepciones por título.

Las muestras se contabilizan por repetición: una acción cubierta en una repetición previa no sustituye otra muestra solicitada. Los requisitos históricos superiores se conservan. En el historial de Astronaut revisado había un requisito de tres muestras de collect, independiente de las falsas obligaciones por profundidad; se puede completar con tres repeticiones por modo.


## Rondas NSP con estado vacío anidado

Un resultado NSP pagado puede conservar `state` como un objeto cuyos contenedores
están vacíos. Se reconoce solamente la forma de resultado demostrada y una ronda
independiente con stake debitado, premio liquidado y saldo enlazado a la ronda
anterior. Índices presentes, flags activos, elecciones pendientes y otros campos
no reconocidos siguen impidiendo certificar el regreso al base.
