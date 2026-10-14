# Yggdrasil en Tester-Spin

Actualización: 2026-10-13. Resultado de la pasada autónoma: **137 OK de 159**,
8 PARCIAL y 14 ERROR. Se partió de 8 OK; las primitivas comunes recuperaron
129 juegos mediante sesiones Demo nuevas, precios actuales, rondas cerradas y
dos giros normales cerrados consecutivos. No hay excepciones por título o ID.

Los errores restantes son 13 rechazos authenticate (code=-1) y 1 rechazo play
(code=1). Los parciales conservan contratos o controles todavía no aprendidos.
La selección de familias reconocidas terminó sin candidatos adicionales.
Las capturas y diagnósticos se conservan en data/providers/yggdrasil para la
siguiente ampliación; un HAR histórico nunca promueve el juego por sí solo.
El Retry-After anterior se respetó antes de reanudar y la cola usa un trabajador.

## Autoridad de compras y antebets

`fn=game` de la sesión actual aporta `cfg.props.Modes`. Ese dominio fija las
opciones que deben ejecutarse; contar peticiones de un HAR no determina cuántas
compras existen. No hay listas de títulos ni excepciones por ID de juego.

Cuando `Config.bettingModes` existe, sus entradas relacionan comando, tipo y
coinsPerBet: BASIC es giro, BUY_BONUS es compra y GOLDEN_BET es antebet. Se
contrastan contra Modes. Duplicados, comandos ajenos, monedas inconsistentes,
tipos nuevos o discrepancias de coinsPerBet impiden ejecutar esa opción. GB
no es un alias global de antebet: necesita esta declaración tipada.

En contratos antiguos, Modes se interpreta mediante familias de comandos cuyo
serializador ya se aprendió: BB, BUY, BUY_BONUS, BUY_A_BONUS, BUYBONUS,
BUYMAXBONUS, BUY_RFS/BUY_SFS, BONUSBUY y variantes MAX/SUPER_BUY_BONUS.
GOLDENBET/GOLDEN_BET y GOLDEN_BET_WILD son familias de antebet conocidas.
Para ANTE_BET del dialecto Config.definition se exige bonusBetMultiplier>1 y
que su precio actual coincida con el precio BASIC multiplicado por ese valor.
Otros comandos siguen sin clasificar hasta aprender su contrato.

`orgSettings`/`extraOrgSettings` aportan Denoms por modo y moneda. El precio es
coin × coinsPerBet. No se reutilizan precios de otros juegos. Paylines determina
las líneas, si se anuncia. Una declaración completa y vacía acredita cero;
configuración ausente o ambigua deja la cantidad sin confirmar.

## Identidad y sesión

La página pública debe vincular su ID mediante un launcher oficial HTTPS de
staticdemo o staticpff. Se toleran espacios alrededor del gameid decimal.
Identificar una página staticpff no demuestra que su antiguo backend sea ejecutable:
no se cambia de servidor u organización para sortear rechazos del servicio Demo.

Cada prueba crea una sesión Demo aleatoria, obtiene token actual, consulta game
y exige restore vacío. Los HAR históricos no aportan credenciales ni identidades
para ejecutar. Se reconocen API 2.6.0 y 2.8.2; el dialecto clásico sin etiqueta de
versión requiere que CoinsPerBet o Paylines concuerden con BASIC.

## Bonus con parámetros y free spins

El SDK público puede ofrecer únicamente `Bonus` y distinguir la decisión mediante
`clientParams.playerChoice`. En la familia demostrada, `-1` conserva el premio y
`1` lo arriesga. No se infiere esta semántica de la palabra Bonus: se exige el DTO
actual aprendido y el eco exacto de `{bonusRound:false,playerChoice:-1}`.
Calavera conserva flags y cantidad; el dialecto BBG reinicia las flags de entrada
pero debe anunciar un `freeSpinState` explícito con el mismo premio y apuesta.
Reetiquetar el DTO de entrada como FreeSpin no constituye ese reconocimiento.

Calavera ejecuta `FreeSpin` con `{bonusRound:false}` y puede devolver todas las
jugadas en un lote. Los resultados generados completos se conservan en
`parameterized_bonus_results`, incluso cuando betdata es null. El menú guardado
expresa el premio actual y la salida segura, sin afirmar cobertura de todos los
resultados de gamble.

El cliente BBG envía FreeSpin sin clientParams y recibe una jugada cada vez.
El contador baja exactamente uno, currentPlay aumenta uno y se conserva el premio,
la apuesta y triggeringDetails. El servidor puede ofrecer Bonus para conservar
el premio o iniciar FreeSpin directamente desde la compra superior: la cantidad
se toma del estado actual, nunca de una constante por juego.

Config.definition aporta posiciones del tablero, roles isWild y premios por
símbolo y frecuencia. Cada cascada contrasta sus posiciones, símbolos, factores,
multiplicadores direccionales y dinero con esa definición. ExtraLife reemplaza
las posiciones no wild y conserva los wild según la caída de su columna.
El premio de la jugada se distingue del acumulado de la ronda; ambos se
contrastan con los acuses. El último FreeSpin puede anunciar Spin en el DTO
pero requerir C en el dominio del servidor: se cobra antes de probar el retorno.
Los esquemas o premios desconocidos permanecen PARCIAL y conservan su HAR.

Calavera y Florageddon completaron giro, antebet y ambas compras con cierre,
dos probes normales consecutivos y contrato PROMOTED. Las pruebas incluyen
roles wild y posiciones remapeados para impedir dependencias de símbolos fijos.

## Jugadas, elecciones y cierre

Cada petición exige HTTP 200 y code=0. El inicio debe reconocer paso 1, comando,
importe y moneda actuales. El wagerid debe ser nuevo. Las peticiones de pago
inciertas no se repiten.

Un cobro C requiere que el dominio pendiente sea exclusivamente C y que todos
los pasos anteriores estén RESULTED. Envía amount=0, el wagerid actual, betid
de la raíz y step=max(step)+1. El dialecto compacto reconoce coin/ncoins/importe/moneda sin exigir un eco de
líneas que no devuelve. Esto acredita la apuesta BASIC actual, no una selección
de líneas adicionales. Su cobro admite el eco nCoins del mismo servidor,
con cantidad y moneda conservadas; un número de monedas distinto se rechaza.

El servidor puede devolver solo el acuse final:
no necesita repetir los pasos anteriores. Debe conservar moneda e importe de
referencia, reconocer el comando y no cargar otra apuesta.

Las familias de elección aprendidas usan las opciones del paso actual, nunca
índices inventados. Se reconocen salidas NON_GAMBLE/NO_GAMBLE, RG frente a AG,
FREE_SPIN_*_PICKS frente a GAMBLE_*_LVL_*_POS_*, y NON_GAMBLE_*_SCATTERS
frente a GAMBLE_EGG_*. Los grupos de modo/recompensa se contrastan cuando el
serializador lo exige. La última familia conserva coin del wager actual.
PICK_BOX_* recorre una opción realmente anunciada. FREESPIN frente a GAMBLE
usa el paso bonus del cliente Leander. No se seleccionan opciones de gamble.

El menú makeChoice genérico exige exactamente possibleChoices y que coincida
con el dominio de comandos del servidor. Metadatos de tipo gamble, opciones
no aprendidas o parámetros adicionales no se adivinan. Una respuesta puede
entregar un nuevo menú después de cada elección. Los artefactos guardan
available/selected por paso, indicando que no se probaron todas las alternativas.
Elegir sin C no se informa falsamente como un cobro. La familia Gati anuncia
Finished/Checkpoint: Finished incluye clientParams.finishedByPlayer=true y
permite llegar al cobro C. Checkpoint requiere estado del cliente y no se inventa.
Este par es gestión de presentación/persistencia, no una elección de juego para
la grilla de mecánicas. Los paquetes BASIC validan pantallas, premios, cero
spins restantes/otorgados y ausencia de riesgo o colecciones activas.

El cierre real exige wager.status=Finished, apuestas no vacías, todas RESULTED
y ausencia de comandos pendientes. Fin de animación o beneficio mostrado no
prueba liquidación. Los límites de pasos/probes dejan pendientes las rondas
que no pudieron demostrarse.

## Dos regresos al giro normal

Cada muestra necesita dos ciclos ordinarios consecutivos cerrados. La
clasificación valida estructuras conocidas: acciones por nombre, acciones
tipadas BaseGame, resultados clásicos de carretes, metadatos de colecciones,
DTO de pantallas/multiplicadores y rondas numéricas de modo principal 0/Regular.
Las familias tienen validadores de campos, tipos, geometría, premios y banderas.
Campos nuevos, elecciones, free spins o respins activos quedan sin acreditar.

`featuresUsed=['noFeature']` no permite ignorar controles adicionales. Su forma
mínima o el resultado clásico completo deben corresponder a un contrato conocido.
El umbral de rage se obtiene de ExperienceToTriggerFreespins de la configuración
actual: no se fija un valor por título. Una colección no se convierte por sí sola
en compra, antebet o acumulador confirmado.

Las animaciones y los contadores no sustituyen el acuse del pago ni el cierre
financiero. Reconocer localmente un HAR solo habilita un candidato para la nueva
prueba; no cambia su estado a OK.

## Transporte y evidencia

La ejecución usa un trabajador por proveedor y separa los inicios HTTP al menos
cuatro segundos. El ritmo y Retry-After se conservan por carpeta de datos, con
bloqueo entre procesos y escritura atómica. Reiniciar el programa no borra una
pausa del servidor. Si la espera supera el timeout, no se envía la petición.
La cola consulta la pausa antes de iniciar preparación o HTTP: los juegos
que no llegaron a probarse conservan sus resultados anteriores.
Un 429 no acredita ni invalida una primitiva de juego.

Cada ejecución conserva un HAR local completo de la API, configuración segura,
peticiones/acuse por paso y return-to-base.json. Los DTO conocidos se retienen
para reconstrucción. Los comandos desconocidos permanecen en el HAR privado.
Tokens, sesiones, saldos y respuestas completas no se publican en Git.

Validación final: 1721 pruebas correctas, con tres
advertencias HTML preexistentes. El corte actual dejó 122 OK /159. El ejecutable del
escritorio está actualizado y su arranque se verificó con los diez proveedores;
la versión y su huella aparecen en la sección de validación final.

## Ajustes comunes de las tandas posteriores

El eco compacto ncoins puede incluir cmds=C cuando el giro gana. Se verifica
coin, ncoins, importe y divisa; esto no acredita una selección de líneas ausente
en el eco. C es cobro, no compra. Los vectores clásicos de premio admitidos
validan su máscara contra el tablero y los campos monetarios finitos.

Los menús cero coste se conservan con protocolo, dominio ofrecido y opción
seleccionada. El control de cobertura solo considera resuelto un menú cuando
hay un acuse validado en la misma ronda/paso, petición de coste cero, dominio
idéntico, modo ejecutado hasta cierre y dos retornos ordinarios confirmados.
Esto acredita completar el modo de pago; no acredita haber probado todas las
alternativas de riesgo del menú. Un menú desconocido o sin acuse bloquea OK.

PICK_POSITION se ejecuta con el comando realmente ofrecido, amount=0, próximo
paso y betid raíz según PickAndClickSaveRequest del SDK oficial. No se mezcla
con PICK_BOX ni se fabrican posiciones. Las cascadas create/chain y subsymbol
booleano se reconocen como presentación tipada, conservando sus DTO.

El display PROGRESS/GENERAL_MULTIPLIER se liga al coin BASIC actual y su
collectionsMap. Se exige progreso inferior al límite anunciado, ausencia de
freeSpinsEntered y de multiplierIncreasedTo5, y coincidencia de los contadores.
Un envoltorio inválido no vuelve al detector genérico de tablero. La captura
segura conserva el estado y la moneda que permiten repetir esta validación.

Los menús Gati con Gamble.Options usan el rol collect declarado por el servidor
junto con su dominio riskList. Ese contrato tiene prioridad sobre cualquier
perfil por nombres, incluido C; contradicciones y envoltorios malformados
impiden continuar. Se conserva Options para reconstrucción y se envía su
comando COLLECT exacto, coste cero, paso siguiente y clientParams vacío según
el SDK. Los puntos decimales de las probabilidades en comandos risk se admiten
al leer el dominio; esas opciones no se ejecutan.

La familia NO_GAMBLE_N con GAMBLE_N+1_LEFT/RIGHT ofrece rechazar el riesgo o
intentar el nivel siguiente. Se elige únicamente la opción NO_GAMBLE vigente
y se contrasta ese nivel siguiente; no se confunde con NON_GAMBLE_N/GAMBLE_N_M.

## Última validación del ejecutable y primitivas comunes

La verificación completa del 13 de octubre aprobó 1721 pruebas.
La prueba de arranque del ejecutable instalado pasó con los diez proveedores.
SHA256 del ejecutable que abre el acceso directo del escritorio:
`E02BF460504CF3D875D5139A0FCF5730DE6957B08D3861949875C2E171F5D9FC`.

El dominio de continuación se toma del último paso del wager: los menús de
pasos anteriores son historial, no comandos actuales. Todos los pasos nuevos,
incluidos los que el servidor genera automáticamente, deben tener importe cero
y mantener la moneda de la petición inicial. Se rechazan cargos adicionales.

Se reconocen secuencias tipadas de resultados BASE con geometría y premios
contrastados. Un disparador de free spins solo sirve para elegir candidatos y
conservar evidencia; nunca se considera prueba de retorno al juego normal.
En el dialecto enumerado, las elecciones se toman de los comandos actuales
`:N` y de un NextRound tipado y vinculado al mismo modo BASIC. Cada elección
requiere respuesta, avance de paso y confirmación de importe cero.

Los contadores pueden omitir setCounters cuando los mapas inicial y final son
idénticos y no se registró ninguna colección nueva. La ausencia de animación
no autoriza estados cambiados ni premios pendientes. CoinsPerBet admite tanto
una lista como un valor numérico positivo único, siempre coincidente con BASIC.
No se añaden excepciones por nombre de juego o ID.

La tanda de configuración clásica distingue rechazo remoto de contrato aún
no aprendido. Un rechazo técnico del giro no prueba ausencia de compras y
no permite promover el juego a OK.

## Contratos clásicos y metadatos neutrales comprobados

El cliente clásico por líneas envía coin, amount y lines. Su nCoins es por línea,
no la suma del giro. Se usa este serializador sin ApiVersion, con CoinsPerBet ausente o escalar
y con Paylines.length igual al precio BASIC en monedas. El giro
omite coins total; la respuesta debe reconocer una moneda por línea y satisfacer
coin × nCoins × líneas activas = betamount = amount solicitado. Un dominio
CoinsPerBet en lista conserva su serializador anterior. La captura de control
con el MCP confirmó 30 × 1 × 0,01 = 0,30 y estado Finished.

El cobro de colección valida CASH, sus valores y los COLLECT realmente presentes,
los premios antes y después del multiplicador, el total de premios dibujados y
coinWin × coin = cashWin. Los buckets guardados se contrastan con el dominio
actual de Modes; un bucket de compra anterior no es una obligación nueva.
Las acciones malformadas se rechazan antes de sumar sus premios.
Golden Fish Tank Party completó en vivo dos compras, un antebet y sus retornos.

El par grandTotal/multiplier solo se considera neutral con total y premio cero,
multiplicador uno y wtw vacío. Los contadores de heads exigen todos los valores
cero, fsBetAmount nulo y ReelSetConfig como permutación válida. El panel de
jackpots es informativo únicamente sin premio, con moneda y apuesta BASIC
actuales coincidentes. Contadores activos, premios, campos nuevos y controles
no demostrados siguen sin afirmar retorno ordinario.

Los menús LS,C se resuelven cargando el estado antes de cobrar, según la sección
Acumulador clásico. El alcance de cobertura sigue siendo el dominio de modos
pagados; no afirma explorar todas las alternativas de azar.


## Continuación del catálogo, 13 de octubre

Los descuentos de BUY_A_BONUS son estados de precio de una compra de nivel
aleatorio; MAX_BUY_A_BONUS es la compra distinta de nivel máximo. El cliente
expone dos tarjetas, no once compras. Se exige la escala completa de descuentos
10–90%, los precios actuales de Modes y la misma moneda por variante. Antes de
comprar se consulta info/what=playerState de la sesión actual y se selecciona
el comando correspondiente a bonusProgress de coin con cinco decimales. No se
prueban precios que el acumulador no habilitó. Estado malformado, descuento no
anunciado o precio incoherente deja el modo pendiente. Se conservan los comandos
y precios originales en wire_modes/price_variants y current-purchase-price.json.
La migración histórica archiva las obligaciones antiguas de precio y transfiere
su cuota máxima al tipo de compra, sin eliminar otras compras pendientes.
La sesión de control confirmó dos compras y un antebet con sus cierres.

Los menús NG/G y FREE_SPINS/GAMBLE se interpretan desde las opciones del paso
actual y los datos tipados de ese mismo paso. La ejecución rechaza el riesgo
con la opción NG ofrecida o conserva las free spins ya otorgadas; cada paso
mantiene coste cero, moneda y ronda. Se guardan el menú original, la selección
y la respuesta. No se afirma haber probado todas las ramas de azar.

El marcador C,* significa que el cliente puede cobrar C; * no es una elección
para ejecutar. Esta primitiva requiere la forma clásica del giro y C primero
en el menú actual. No convierte menús desconocidos en un cobro genérico.

La geometría de splitz, reels sincronizados, bloques y reemplazos de símbolos
se contrasta con el tablero. Los índices de bloque y reemplazo se convierten
con columna=floor(index/filas), fila=index%filas, según el SDK. Las tiradas con
rpos nulo requieren tablero explícito completo; otros tipos malformados se
rechazan. Un premio en monedas sin wonCash solo se reconoce si coincide con
accC/accWa y coin de BASIC actual.

El progreso de nivel guarda spinsMade, coinsWon, gridSnapshot y un multiplicador
acumulado. lastBet selecciona la apuesta guardada. No son compras ni una entrada
a bonus por sí solos. El esquema aprendido exige incremento de spinsMade,
delta de coinsWon igual al premio del giro, máscara monotónica, nivel constante
y levelIncreased/superMode falsos. La máscara completa, los cambios de nivel y
campos nuevos siguen pendientes. Los fragmentos de jackpot se reconocen solo
con contadores cero, matrices sin fragmentos y valores informativos coherentes.

El serializador por líneas también admite CoinsPerBet escalar clásico cuando
coincide con BASIC y Paylines.length. La prueba con el cuerpo real del cliente
confirmó nCoins=1 y 20×0,01=0,20; no se extendió este cambio a dominios en lista
sin evidencia. Los artefactos step-001-request conservan ahora el cuerpo enviado,
no una cantidad total que fue omitida por el serializador.

Las páginas antiguas que lanzan staticpff pueden apuntar al servicio público
Play for Fun distinto del servidor Demo moderno. La captura de lanzamiento
mostró ese destino, pero la consulta pública respondió 403. No se cambió de
backend ni se acreditó OK sin aprender su autenticación y contrato actual.


## Geometría variable y acciones de efectivo

API 2.7.0 comparte el contrato actual Modes/Denoms y la validación del giro
pagado con 2.6.0 y 2.8.2. Su autorización de transporte no basta para afirmar
retorno: también se reconoce el resultado y se cierra la ronda.

Los tableros de alturas variables conservan altura inicial/final por columna,
casillas invisibles vacías y el tablero lleno que sirve al dibujo. Solo se
reconoce el caso sin cambio de alturas ni free spins otorgadas, con orden de
reels válido y todos los premios dentro de las celdas activas. Se conserva el
DTO original; la proyección interna de geometría no se transmite al servidor.

splitFields incluye posición, símbolo revelado y cantidad. Se verifican los
índices duplicados, el símbolo conocido y la casilla MYSTERY o el símbolo actual.
allBonusAmountsInMoney es una tabla informativa de premios, no un catálogo de
compras. Los paneles de jackpot con featuresData vacía y bonusWon cero se
reconocen únicamente con valores antes/después iguales. El formato previo de
featuresOutputs conserva su validador; no se redirige al nuevo esquema.

Los DTO ActionGame_ normalizan los premios por la apuesta pagada. Se exige
BASE_SPIN, modo base_game, fuentes Empty, contadores vacíos, tablero rectangular
completo y orden de inicio/evaluación/premios/final. amountNormalizedToBet×stake
igualará amount de la moneda actual. La suma de combinaciones coincide con los
premios intermedios, el total del modo y los totales monetarios del servidor.
La casilla empty no puede producir un premio. Fuentes, contadores, órdenes o
acciones nuevos mantienen el resultado pendiente. Se guarda el envelope de
ordinary_typed_action_outcomes, con importe y moneda suficientes para repetir
la validación; el saldo de la sesión se excluye.

## Acumulador clásico: carga y cobro

El dominio LS,C de un resultado clásico reconocido requiere cargar el estado
mediante LS antes de cobrar. PartnerConnect agrega el wager actual; la petición
LS envía step siguiente y betid raíz, sin amount. Se exige acuse de importe cero,
mismo wager, contador y saldo conservados, doubleResult=supermeter y dominio C,S.
Se elige C, importe cero, y se verifica cierre y premio igual al saldo cargado.
No se ejecuta S por inferencia. Máscaras activas y variantes no aprendidas siguen
PARCIAL. El retorno solo acepta estado neutral y precio BASIC actual.

Captura representativa propia: ygg-ls-live/http.har; secuencia normalizada en
tests/fixtures/yggdrasil_supermeter.json. Dark Joker Rizes completó la pasada 28
con contrato PROMOTED. La captura representativa prueba LS/C; la pasada aleatoria
prueba giro y retorno, sin garantizar que active el acumulador en cada ejecución.

## Constructor dinámico de modos del SDK

Cuando faltan roles, el ejecutor consulta el launcher oficial ligado al gameid
y sus bundles HTTPS de staticdemo/staticpff. El perfil aprendido construye
BASIC como giro y los demás modos como compras; GOLDEN_BET_IDS y su exclusión
explícita del menú separan antebets. Las tarjetas, cuando se declaran, deben
coincidir con ese dominio. Constructor ambiguo, fuente no reconocida, identidad
ajena o contradicción con bettingModes conservan el resultado pendiente.
Los comandos pueden tener cualquier nombre: sus roles proceden del constructor
verificado y sus precios del Modes actual. No se usan nombres o IDs de juegos.

Se conservan fuente, huella y manifiesto de assets en el diagnóstico privado.
La descarga ocurre solo si hay roles pendientes; la configuración de la sesión
se reconstruye con el perfil, sin reutilizar precios del HAR. Los bundles con
recursos embebidos tienen límites de tamaño y un máximo total de lectura.

El contrato Bet/Code/Completed/Round de ese perfil calcula dinero en centavos.
La moneda actual y la apuesta se contrastan con TotalBet; Money/MoneyTB, sus
posiciones y la suma de premios deben coincidir con TotalWin, SpinWin y cashWin.
coinWin se conserva como contador separado y debe concordar con accC.
Una ronda Regular no prueba retorno si contiene premios de free spins, bonus,
contadores activos o campos no aprendidos. Los estados persistidos por importe
no necesitan igualar el tablero recién generado. Las líneas son de base uno y
las posiciones de SymbolsInfo son índices planos. El perfil nuevo se aplica
solo cuando el constructor fue verificado, preservando otros contratos enum.

Pasadas 29–30: Bloody Pesos, Red Dragon Sails y Your Own Island PROMOTED, con
todos los modos declarados cerrados y dos probes ordinarios consecutivos.
Un error DNS de preparación se recuperó antes de jugar; no hubo reintento de
una petición de pago incierta. Las reglas y las pruebas son compartidas.

## Estado neutral de portales y líneas variables

La configuración actual aporta FreeSpinsBase, ExtraWilds, WindowHeight,
NonPortalReelHeight y CoinsPerBetNormal. extraFreeSpins/extraWilds describen
valores configurados; el estado activo lo determinan portalSpinsAwarded,
portalSpinsLeft, portalReels y stateChanges. El retorno exige estado neutral
en los estados anterior y posterior, apuesta actual, tableros y contadores
tipados y premios concordantes. Flags activas, elecciones y formatos nuevos
siguen pendientes. Dark Vortex completó su dominio anunciado en pasada 31.

Corte instalado v16: 122 OK /159, 21 PARCIAL, 14 ERROR. Suite completa: 1721
pruebas correctas; arranque del ejecutable del escritorio verificado.

## Checkpoint v17: acciones nombradas y parada ante formatos desconocidos

El mismo contrato admite tableros con celdas name, finishSpin con winCounters, posiciones con side LEFT/RIGHT y premios ways sin direction. freeSpinsWin debe ser cero para probar retorno ordinario. Campos o controles nuevos conservan revisión pendiente. Enchanted Waters y Ragnaravens Wildenergy completaron todos sus modos declarados en pasada 32.

Un resultado cerrado que no satisface una primitiva aprendida devuelve UNRECOGNIZED_CLOSED_OUTCOME y detiene el retorno en el primer probe desconocido. Se conserva el HAR para aprender su estructura; no se repiten ocho giros para intentar convertirlo en OK. Se mantienen dos probes ordinarios consecutivos para los retornos reconocidos.

Corte instalado v17: 124 OK /159, 21 PARCIAL, 14 ERROR. Suite: 1731 pruebas correctas, tres warnings. Arranque del escritorio verificado. SHA256: C636EED64E5120CC14A305D66BA34BD75C962F3A8142A2ED976F046FBE3B6C3B

## Checkpoint v18: símbolos móviles

La primitiva compartida contrasta walkingBefore/After/New con desplazamiento de una columna, máscaras stickyA/B/N, geometría, posiciones, ciudad constante, premios de cada paso y acumulación monetaria. Exige cero cargo en continuaciones y cobro final; la validación de transporte mantiene identidad de ronda y comandos anunciados. Una secuencia completa reconocida puede reiniciar la búsqueda de retorno; no sustituye los dos giros ordinarios consecutivos. Estados o controles desconocidos siguen pendientes.

Pasada 34: Orient Express PROMOTED en sesión nueva, cobertura 1/1, cierre y retorno confirmados. Corte instalado: 125 OK /159, 20 PARCIAL, 14 ERROR. Suite completa: 1747 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: FC79492F0335F5296D0AA66F7BFAE05CD057B89553660C9DD1B613769713E547

## Checkpoint v19: acumulador persistente declarado

CollectionsCapacity de la configuración actual determina la capacidad por columna; collectionMeter.amounts debe coincidir con la longitud de values. Los valores son cantidades finitas no negativas y cada colección permanece por debajo de su capacidad. Una colección incompleta guardada no exige continuación por sí sola. Sin capacidad válida, con colección completa, controles de premio, continuación o campos desconocidos, la respuesta conserva revisión pendiente. No se fijan capacidades por juego ni se descarta el estado original del HAR.

Pasada 35: Tuts Twister PROMOTED en sesión nueva, dominio 1/1 cerrado y dos giros ordinarios consecutivos comprobados. Corte instalado: 126 OK /159, 19 PARCIAL, 14 ERROR. Suite completa: 1764 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: BA95C148A9998B4EF531337ABAEE9D98872119E73DD8989849F784BC48EF5E8A

## Checkpoint v20: estado neutral de símbolos persistentes

El contrato neutral exige modo desactivado, contadores emperorShift/previousEmperorShift/newWildCount enteros en cero, preStickyWilds y postStickyWilds vacíos y penguinAction ausente o false. Estados activos, acciones de reemplazo, posiciones persistentes y controles desconocidos conservan revisión pendiente. Son campos de protocolo compartidos, sin selección por título ni ID.

Pasada 36: Penguin City PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno ordinario confirmado. Corte instalado: 127 OK /159, 18 PARCIAL, 14 ERROR. Suite completa: 1774 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: 5DBCCD79FB8A9BB8693256C6251733368369A2FAECBDD547224D630A4EC0EABC

## Checkpoint v21: estado ordinario de estación

El perfil de estación exige declaración actual completa de los cuatro conjuntos normales y sus variantes de función especial, con columnas y símbolos válidos. currentSeason debe concordar con su conjunto normal; numberOfSpins es un contador entero acotado. No se aceptan conjuntos Feature como retorno ordinario. El multiplicador de FALL ya está aplicado en wtw; su suma debe concordar con wonCoins, accC y accWa usando la moneda actual. No se aplica nuevamente el multiplicador. Campos y controles desconocidos permanecen pendientes.

Pasada 38: Seasons PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 128 OK /159, 17 PARCIAL, 14 ERROR. Suite completa: 1788 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: FC041B4B180C3B1622329692DF320A2D9EF4D39F942198E466B95A554A3720FC

## Checkpoint v22: repeticiones premiadas devueltas por el servidor

El estado neutral exige contador cero, multiplicador uno, premios nulos e indicadores desactivados. La secuencia premiada contrasta geometría de símbolos grandes, conjuntos y posiciones, premios anteriores/posteriores al multiplicador, acumulación monetaria, apuesta inicial actual, continuaciones sin cargo y cobro final. El cliente usa finalBoard directamente; se conservan ambos tableros y se valida su geometría sin exigir igualdad. Una secuencia cerrada reconocida permite continuar la búsqueda de dos giros ordinarios consecutivos; no sustituye esa prueba.

Los premios directos de copa se contrastan con BaseSilverCupPrizes y BaseSilverCupDistribution. Solo se aprende el tipo de monedas y su conservación; Football Glory permanece pendiente por otra respuesta que aumenta el progreso. No se fija el umbral del cliente en el ejecutor.

Pasada 42: Hyperburst PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 129 OK /159, 16 PARCIAL, 14 ERROR. Suite completa: 1818 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: 3126BE000DC766C7186A93D52E05C82AC37C9C9FA95EDE4BE91CC5138D61EDE8

## Checkpoint v24: cascadas de giro base y tiradas gratis

Se valida la secuencia completa de tableros, posiciones ganadoras y desplazamientos, multiplicadores, premios anteriores/posteriores, acumulación de moneda y efectivo, cargos cero en continuaciones y cobro final. Las repeticiones mantienen el contador de tiradas gratis; los giros consumidos lo reducen. NO_REEL_SET identifica el relleno de una cascada después de una repetición anunciada. El saldo initialBalance se valida como dato numérico, conservando el HAR original.

Una cascada BASIC validada hasta el cobro, sin dominio de tiradas gratis, constituye el giro base completo. Una secuencia con freeSpinsAwarded conserva su clasificación de función separada. La prueba de retorno sigue exigiendo dos rondas ordinarias consecutivas. Campos desconocidos, contadores incoherentes y premios o geometría inconsistentes siguen pendientes.

Pasada 47: Vault Of Fortune PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 130 OK /159, 15 PARCIAL, 14 ERROR. Suite completa: 1844 pruebas correctas, tres warnings. Arranque del escritorio verificado. v23 fue una compilación intermedia; la actualización instalada es v24.
SHA256: F38BEB466E37154576A9F199AB6AC6DB9BB2BB63E821C4C2910F6E9F4B2F0904

## Checkpoint v25: cantidades de funciones guardadas

Icons, WindowHeight y los carretes NReel de la configuración actual fijan el dominio de símbolos, mapas, orden y posiciones. La respuesta neutral exige featureBefore/After e initialPlayerState/playerState iguales, cantidades enteras no negativas, premios nulos y capsCount cero. El campo feature activa la función en el cliente; las cantidades guardadas no la activan por sí solas. Cambios de cantidades, indicadores de función, repeticiones o controles desconocidos conservan revisión pendiente.

Pasada 48: Spina Colada PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 131 OK /159, 14 PARCIAL, 14 ERROR. Suite completa: 1852 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: 6F044E2E6BD99AFE223828D6533A438A2567E7097B22DEBC5DE1F9D11EB83183

## Checkpoint v26: colecciones y repeticiones de giro base

SpinTypes, BaseReels/RespinReels y los límites de salud/progreso de la configuración actual delimitan la primitiva. La secuencia contrasta cada cambio de combate con beforeCollections/collections, preserva posiciones y máscaras de símbolos persistentes, comprueba premios y acumulación monetaria, cargos cero en continuaciones y cobro final. Una repetición anunciada puede ocurrir sin combate. Un combate de cambios cero y un contador de símbolos vistos no activan una función por sí solos. No se acepta ninguna recompensa de tiradas gratis dentro de esta primitiva base.

newUser es un indicador booleano de inicialización; puede comenzar verdadero y debe quedar falso al cerrar el estado. Los estados y controles desconocidos conservan revisión pendiente. Una secuencia base completamente validada cuenta como ronda ordinaria tras el cobro; el retorno sigue exigiendo dos rondas consecutivas.

La prueba concurrente encontró una carrera al inicializar el archivo de coordinación Windows antes de adquirir su bloqueo. La inicialización ahora ocurre dentro del bloqueo, conservando el Retry-After más largo entre procesos. La suite completa incluye esta comprobación real entre procesos.

Pasada 54: Wolf Hunters PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 132 OK /159, 13 PARCIAL, 14 ERROR. Suite completa: 1877 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: 4E51A46DE7EF5CA1204B0C755EC95ACE7C6E0794D3F851249D1340CEE69F4CF9

## Checkpoint v27: reemplazo de scatters y movimiento explícito

EdgeScattersReplacementIcon, EdgeScattersIsColumnBanned, Icons y BaseReelsSupplierConfig del servidor delimitan el reemplazo. La primitiva contrasta columnas, símbolo configurado, conjuntos normales de carretes, posiciones del caminante y tablero final. Los tableros explicados por esos dos efectos se reconocen como resultado ordinario; premios de tiradas gratis, efectos o cambios adicionales desconocidos siguen pendientes. Los valores y posiciones proceden de la configuración y respuesta, sin excepciones por juego.

Pasada 55: Aldos Journey PROMOTED en sesión nueva, dominio 1/1 cerrado y retorno confirmado. Corte instalado: 133 OK /159, 12 PARCIAL, 14 ERROR. Suite completa: 1885 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: 7CF8A5BF678B11A75D050AFDE32370A4894F5ED44C5EE70A43EE33FF66D5D138

## Primitiva de tarjetas de compra confirmadas (verificada)

El perfil `sdk.confirmedPurchaseCards/serverPriceDomains/v1` enlaza las tarjetas del menú con sus acciones de confirmación, el comando seleccionado y el inicio de la jugada. Los nombres de comandos, tarjetas y manejadores se extraen del cliente; no se asignan roles por nombre de juego ni por precio. Los modos del servidor deben coincidir exactamente con el dominio del menú. Todos los precios y el valor predeterminado se contrastan con las denominaciones actuales y coinsPerBet; no basta comparar coinsPerBet entre modos.

La aceptación del premio se extrae del control del cliente que inicia los free spins. Se exige el menú vigente, estado de premio, tablero y esquema conocidos, importe actual de la compra y conservación de los premios de línea. Las continuaciones llevan importe cero y se validan contra la misma ronda. Un premio de línea simultáneo usa la moneda BASIC demostrada en este perfil; la denominación de compra permanece vinculada a su precio de adquisición.

Pasada 59: el giro normal, BONUS1 y BONUS2 cerraron con retorno confirmado; la variante de línea simultánea quedó cubierta. Esta primitiva se incorporó en v29.

## Checkpoint v29: tarjetas de compra y aceptación del premio

El perfil de tarjetas enlaza el menú, sus confirmaciones y comandos con el dominio actual de Modes. Las denominaciones completas, sus valores predeterminados y coinsPerBet deben coincidir con la relación de precios del cliente. El papel de compra no se infiere del coste ni del alias del comando. La aceptación de free spins se obtiene del control oficial y solo se ejecuta frente al premio y menú actuales; las continuaciones deben conservar la ronda y tener coste cero. Los premios de línea simultáneos se contrastan con la moneda BASIC actual, separadamente del precio de adquisición.

Pasada 59: Shaker Club PROMOTED, 5/5 opciones recorridas, giro normal y ambas compras cerrados con retorno confirmado; cero ramas pendientes. Evidencia: tests/20261013-174015-2bb54b. No hay excepciones por juego en estas primitivas. Corte instalado: 134 OK /159, 11 PARCIAL, 14 ERROR. Suite completa: 1915 pruebas correctas y tres warnings. Arranque de escritorio verificado.
SHA256: 09FADAFB6CD7AF5CAC8C78F35A8AF5AC4CF3A1141012C0816D999D23D15F6AD5

## Checkpoint v30: dominio clásico fijo y estado base vacío

Cuando CoinsPerBet no existe como dominio separado, una declaración MinCoins == MaxCoins == Modes.BASIC.coinsPerBet demuestra una cantidad fija de monedas. Esa cantidad se valida independientemente del número de líneas; no se copian valores del cliente ni se introducen excepciones por título. Ajustes de moneda nulos producen un modo explícitamente pendiente sin inventar precio.

El cliente distingue thisWilds, addedWilds y nextWilds de sus variantes fs. La terna base completa y vacía se reconoce junto con el tablero, importes y comandos normales del protocolo clásico. Campos incompletos, tipos distintos, estados activos y metadatos de free spins quedan pendientes.

Pasada 60 obtuvo las primeras jugadas de este dominio; pasada 61 confirmó Golden Monkey PROMOTED, dominio 1/1 cerrado y retorno normal confirmado. Evidencia: tests/20261013-174947-88ecd0. Corte instalado: 135 OK /159, 10 PARCIAL, 14 ERROR. Suite completa: 1935 pruebas correctas, tres warnings. Arranque del escritorio verificado.
SHA256: 2F0C34771F35848455B39D11BC181F4B4D67D9928132CCAF990FA9303A885884

## Cascadas numéricas y compras con comando repetido (verificadas)

La geometría inicial sale de Config.initialBoard. Cada tablero anuncia sus alturas y total_ways; el validador contrasta ese producto, coordenadas únicas, cantidad de combinaciones y suma de payouts. El SDK usa las posiciones de la fila ganadora directamente, incluidas las posiciones sustitutas. Las columnas ya existentes deben desplazarse íntegramente; la nueva columna puede crecer una posición o conservar la altura anunciada. No hay un límite de altura copiado del nombre del juego.

Solo el giro BASIC pagado, con bonusTriggered falso y estados sin tiradas gratis, compra ni antebet, cuenta como giro ordinario. Las cascadas de un premio comprado conservan su clasificación de bonus aunque reutilicen la validación de geometría y pagos.

El comando de una compra puede repetirse en la misma ronda para iniciar y ejecutar el premio. La continuación exige un modo de compra reconocido y su precio actual, premio vigente, comando ofrecido, importe nuevo cero, paso siguiente, estado enlazado y contador decreciente. El saldo acumulado debe aumentar únicamente por el pago validado de la respuesta. El cliente lo envía con type=bonus; ese comando repetido no representa una compra adicional.

Evidencia: 11 giros históricos validados; pasadas 62 y 63 confirmaron el giro normal y la aceptación sin nuevo cobro; pasada 64 recorrió varias tiradas y detectó el desplazamiento con altura estable. La suite actual tiene 1974 pruebas correctas y tres warnings. La pasada 69 confirmó todos los modos de esta familia; el código se distribuyó en v31. La revisión conjunta de nueve capturas recientes reconoce 30 giros BASIC, cinco concesiones de compra y 15 tiradas compradas; las 50 respuestas representativas pasan las primitivas compartidas. Los multiplicadores se toman de cada tablero; el payout recibido ya contiene su efecto y no se multiplica nuevamente. El retorno BASIC puede limpiar marcas históricas del bonus anterior con contador cero.

## Checkpoint v31: cascadas ordinarias y ciclo de compras concedidas

La configuración actual delimita la geometría y los precios. La primitiva valida los tableros, desplazamientos con crecimiento o altura estable, combinaciones anunciadas y suma de payouts. Los multiplicadores pertenecen a cada tablero de respuesta; los payouts ya incluyen su efecto. Un multiplicador positivo por sí mismo no identifica compra ni antebet.

Una compra concedida puede reutilizar su comando en todas las tiradas del premio. Se exige el precio de adquisición actual, comando ofrecido y type=bonus, coste nuevo cero, identidad de ronda, paso siguiente, estados enlazados, contador decreciente y conservación del pago acumulado. El cobro final y dos giros BASIC cerrados prueban el retorno. Si el estado inicial conserva marcas, multiplicador o alturas de un bonus agotado, el giro BASIC actual puede limpiarlos; tiradas todavía pendientes y estados actualmente activos no se ignoran.

La revisión por lotes inicial reconoció 50 respuestas de nueve capturas. Pasada 69: Candyfinity PROMOTED, 7/7 opciones recorridas; BASIC, BUYBONUS, BUYMAXBONUS y GOLDENBET cerrados con retorno confirmado y cero ramas pendientes. Evidencia: tests/20261013-182559-d71a61. No se añadieron excepciones por título o ID. Corte instalado: 136 OK /159, 9 PARCIAL, 14 ERROR. Suite completa: 1974 pruebas correctas, tres warnings; arranque del escritorio verificado.
SHA256: D30862F3D5BB065D063D419D51C979AEDAFDB9FBCDBF351887CE31CB4DC1D66E

## Checkpoint v32: tarjeta única y pagos de ambos lados

El perfil sdk.confirmedSinglePurchaseCard/serverPriceDomains/v1 enlaza la tarjeta de compra, su confirmación y el constructor de la petición. Extrae comando, factor y cantidad de monedas del cliente y contrasta todos los precios y valores predeterminados con Modes y las denominaciones actuales. No asigna roles por título, ID ni alias del comando.

La cantidad de free spins se obtiene del premio actual freeSpin.added; la entrada requiere el comando del cliente también ofrecido por el servidor, precio correcto y coste nuevo cero. Las rondas BASIC validan premios de izquierda y derecha, coordenadas, transformaciones de tablero y total de la jugada. Los respins automáticos devueltos conservan la identidad del grupo, desplazan las posiciones retenidas al extremo inferior de cada columna y deben agotarlas antes del cobro. cashWin es el pago de una ronda; winSum acumula las rondas. No se confunden estos efectos ordinarios con compras o antebets.

Pasada 72: Defenders Of Mystica PROMOTED, dominio 3/3 recorrido, giro y compra cerrados con retorno confirmado y cero ramas pendientes. Evidencia: tests/20261013-190127-fb5a74. Corte instalado: 137 OK /159, 8 PARCIAL, 14 ERROR. Suite completa: 2016 pruebas correctas, tres warnings; arranque de escritorio verificado.
SHA256: C157A68A221AF67E486C54D28462F8CC1AF3A97D5AA127473415278250A4A485
