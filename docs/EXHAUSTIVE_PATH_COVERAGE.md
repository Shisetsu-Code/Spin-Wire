# Exhaustive path coverage

Actualización de muestreo: consultar [Muestreo y aprendizaje](SAMPLING_AND_PROTOCOL_LEARNING.md).
Las ramas conocidas incluyen cuotas de muestras terminales; las elecciones se
identifican por su prefijo, no por el número de paso. En BGaming se excluyen
`purchased_feature` y `purchased_feature_level` de la matriz independiente porque
ya están acoplados y enumerados como contratos de compra.

## Invariante

`OK` significa que Tester-Spin completó todas las acciones ejecutables y todas las ramas finitas que el proveedor anunció o que fueron observadas durante la corrida.

Una respuesta HTTP/WS válida no basta. Una rama anunciada que no fue recorrida, un selector cuyo dominio no está resuelto, una continuación sin wire contract, o un estado nuevo que no se puede clasificar mantiene el juego en `PARCIAL`. Tester-Spin no inventa requests para convertir un resultado en `OK`.

El scheduler aplica `ProviderAdapter.finalize_test_result()` a todos los proveedores. El finalizador genera `path-coverage.json` y vuelve a comprobar las ramas declaradas por el adaptador y las ramas explícitas encontradas en los artefactos de la ejecución.

Los adaptadores pueden declarar una rama con:

```text
coverage_required = true
required_options  = [...]
covered_options   = [...]
```

Además, una acción de gameplay con `executable=false` o `observed=false` se considera cobertura pendiente aunque el adaptador no haya añadido explícitamente `coverage_required`. Las filas de metadata pura `DISCOVERED_ONLY` no se convierten automáticamente en acciones.

## Red Tiger

Fuente de verdad actual: settings/runtime de Evolution Games más respuestas `platform/game/spin` y `platform/game/choice`.

Las compras anunciadas por `featureBuy` se ejecutan por separado. Si una respuesta contiene `choices.available` y `selected=null`, cada opción es una rama real. Una elección consume el `roundId`, por lo que las ramas hermanas se prueban recreando una compra/ronda fresca. El expansor es recursivo: si `A` abre `[A1,A2]`, se recorren `A/A1` y `A/A2`; `Random` también cuenta como una rama de protocolo independiente.

Varios `spinMode` dentro de una misma respuesta no se convierten en compras ficticias: son fases observadas de una ejecución. Las ramas sólo se crean cuando el protocolo expone una elección efectiva.

Guardas: profundidad máxima 8 y 128 prefijos por modo. Alcanzar una guarda deja cobertura incompleta; nunca produce un falso `OK`.

## Pragmatic Play

Fuente de verdad: `doInit`, respuestas de juego y transiciones confirmadas por HAR.

Se ejecutan los modos base, ante-bet y purchases descubiertos por `bls`/`purInit`/`purInit_e`. Las continuaciones conocidas incluyen `doBonus`, `doCollectBonus`, `doCollect`, continuation `doSpin`, `doMysteryScatter` y `doFSOption(ind)`.

`fs_opt` se trata como un árbol, no como un conjunto global. Cada aparición de `na=fso` se identifica por su prefijo de selecciones anterior. Si una ruta `0` abre otro selector `[0,1]`, las ramas `0/0` y `0/1` son independientes. Cada rama faltante se reproduce en una sesión fresca con su secuencia `ind` forzada hasta ese punto y se siguen descubriendo ramas hijas.

El `path-coverage.json` también valida cada artefacto `fso-selection-*.json` por ocurrencia para impedir que una selección hecha en un prompt cubra accidentalmente otro prompt distinto.

Un `na` desconocido o una firma de protocolo sin handler queda `PARCIAL` con RAW preservado.

## BGaming

Fuente de verdad: init/runtime API-v2, cliente JS, HAR seleccionado por juego, HyperHive HAR/serializer y perfiles persistidos.

Las purchases y niveles ya se descubren dinámicamente y las continuaciones con wire conocido se siguen hasta estado terminal. Las acciones anunciadas por `flow.available_actions` que no tienen contrato ejecutable se registran como gameplay no cubierto y ya no pueden convivir con `OK`.

`additionalSpinOptions` era un hueco importante: el perfil descubría dominios finitos desde el cliente pero utilizaba sólo el primer valor. Ahora se construye el producto cartesiano de todos los valores demostrados en `spin_option_choices`; cada tupla se ejecuta en una sesión fresca y, dentro de esa tupla, vuelve a ejecutarse el conjunto normal de SPIN/purchases/continuaciones del proveedor.

No se prueban valores que el cliente no haya anunciado. Guarda: 128 combinaciones; excederla deja la matriz incompleta y por tanto `PARCIAL`.

HyperHive conserva su aislamiento y su descubrimiento por HAR/bundle. Una purchase o acción descubierta pero no ejecutable queda pendiente en lugar de degradarse a metadata opcional silenciosa.

## Belatra

Fuente de verdad: `enter`, contrato cifrado `/game`, y campos/start/finish demostrados por HAR.

El start conserva la configuración válida de líneas, apuesta y denominación. Para selectores de modo con dominio explícito se genera una matriz de sesiones frescas:

- `vipOn` se recorre como `0/1` cuando `vipMode.vipBetK > 1` demuestra que VIP es un modo real;
- cada `isMath*` escalar observado se recorre como `0/1`;
- `mathType` se recorre cuando `analInfo.mathType*` demuestra más de un valor explícito.

No se interpreta cada importe/denominación como un modo de juego: son parámetros de apuesta, no ramas del state machine.

`buyBonus.buyTotalBetK` anuncia compras, pero los HAR/documentación actuales del proyecto no contienen todavía un request de compra autoritativo. Esas opciones se registran como requeridas y no cubiertas: Tester-Spin queda `PARCIAL` en vez de inventar el wire.

En `toDoubleDialog`, `finish`/decline está demostrado. La rama gamble no tiene todavía contrato demostrado en el proyecto, por lo que un título que exponga ese diálogo queda `PARCIAL` hasta incorporar evidencia real de esa rama.

## RubyPlay

Fuente de verdad: launcher/init, gameserver, client bundle y action wrappers.

Las continuaciones demostradas son `respin`, `freespin`, `minispin`, `select` y `pick`. `select` y `pick` usan un campo `index`; el executor actual puede enviar esos índices y mantiene índices distintos en cadenas `pick`.

El proyecto todavía no demuestra un dominio finito completo para `select`/`pick` en todos los títulos. Por eso ya no se acepta que `index=0` signifique cobertura exhaustiva. Si una corrida entra en `select` o `pick`, se conservan los índices observados y se declara `DOMAIN_UNRESOLVED`; el juego queda `PARCIAL` hasta que un HAR o el cliente permita derivar de forma autoritativa todos los índices legales.

Las continuaciones sin wire contract siguen la misma regla: evidencia preservada, sin request inventado y sin `OK`.

## 1Spin4Win / D1

Fuente de verdad: WebSocket funcional `A/u2` y estados observados por HAR/cliente.

Los estados activos conocidos `st={5,6,11,12}` son continuaciones deterministas del mismo wire `type=1`, por lo que se siguen hasta `st=0` terminal. No hay en la evidencia actual del proyecto un selector de usuario equivalente a `choices.available`.

La auditoría ahora inspecciona los frames guardados. Un `type=3` con un `st` distinto de `{0,5,6,11,12}` se convierte en estado no resuelto y bloquea `OK`; no se lo trata accidentalmente como terminal.

## Política para nueva evidencia

Cuando aparezca un HAR nuevo, la prioridad es extraer el dominio y el wire exactos y convertir el gap en un executor provider-local. Hasta entonces el comportamiento correcto es `PARCIAL`, no elegir una opción arbitraria y no compartir heurísticas de wire entre proveedores.

El orden de autoridad es: request/response real del proveedor > código cliente que construye ese request > metadata runtime explícita > inferencia. Una inferencia nunca autoriza por sí sola a enviar una transición destructiva o de apuesta.

### Origen de elecciones durante la comprobación de base

Las selecciones registradas en `return-to-base/probe-*` pertenecen a `SPIN`: esos probes ejecutan `doSpin` con `bl=0` y sin `pur`. No amplían las ramas de la compra o antebet que precedió a la comprobación. La fase `base_probe` conserva la validación de respuesta, el intento terminal y los dos ciclos base confirmados; sus muestras se deduplican por intento. Las observaciones de bootstrap conservan origen SPIN y no acreditan muestras por sí solas.

Revalidación del grupo Book of, excluyendo Book of Monsters en stand by: seis juegos OK; Book of the Fallen completó 36/36 operaciones, pero conserva alternativas de bonus ocasionales sin cubrir. Sus dos compras principales cubrieron las nueve opciones cada una. Completar operaciones no elimina las ramas observadas pendientes, y alcanzar el límite de exploración mantiene PARCIAL.


### Bonus progresivo plano de Pragmatic

El HAR `www.pragmaticplay.com-2026-10-09T10-39-55-686Z.har` demuestra dos recorridos naturales independientes de compras y antebet: `na=fso` ofrece tres opciones (`doFSOption(ind)`), y `na=b` ofrece una grilla plana de sobres (`doBonus(ind)`), seguida por `na=cb`, `end=1` y `doCollectBonus`. La inicialización no anuncia `purInit`, `purInit_e` ni `bls`; el catálogo contiene solamente SPIN.

Los campos `prg_m=cp,tp,r,acw` y `prg` describen progreso persistente. Su presencia no exige una compra ni implica un bonus activo. El selector de sobres requiere el menú abierto, progreso igual al objetivo positivo, una vida, nivel cero, premio acumulado coherente y vectores alineados completamente ocultos. El dominio se deriva de las posiciones del vector; no del nombre del juego ni de los premios. El cliente conecta `VsBonusGamePlayerChoice.Index` con `doBonus(ind)`. Estados distintos quedan pendientes.

La auditoría de regreso al juego base ahora resuelve `fso` usando el mismo parser y dominio del ejecutor habitual, guarda la elección y completa las tiradas gratis antes de exigir dos ciclos normales consecutivos. La elección natural no se convierte en compra. La grilla usa la política estructural de posiciones ocultas: comprueba el selector y cierre, sin afirmar que se probaron todos los premios. Para acreditar esa muestra, el servidor debe confirmar con estado positivo la posición elegida y terminar el bonus; además se exige ronda terminal y dos ciclos base del intento.

Pruebas de regresión: `test_pragmatic_progressive_bonus.py` y fixture sanitizado `pragmatic_progressive_choices.json`, que conserva únicamente campos de estas transiciones y elimina datos de sesión. Incluyen las tres opciones de free spins, los índices de sobre 7 y 4, rechazo de estructuras incompatibles y confirmación del índice por el servidor.


### Menús parametrizados play/sm/sp de Pragmatic

El HAR de Book of Monsters (`vs20fatbook`, `2026-10-09T00-15-45-564Z`) y el cliente oficial demuestran que el menú `gambling` de tipo 69 mantiene acciones play/sm/sp mientras cambian sus parámetros numéricos y su historial. Se valida el formato y relación de esos parámetros, `ask=level`, tabla e historial completos, una vida y menú activo. La normalización reconoce el contrato del protocolo, sin condicionar por nombre o ID del juego.

`ch_v` identifica clases de acción; `ind` sigue siendo la posición del botón. El cliente usa `GamblingBOM.UpdateItems -> maskIndices.indexOf(i)` y `GamblingItemBOM.ItemPicked -> button.index`. Por eso un menú reducido play/sp con `ch_v=0,2` envía `ind=1` para sp. Los contadores de exploración y cobertura usan la clase semántica, manteniendo el dominio de envío intacto. Se requieren muestras separadas de play, sm y sp cuando están disponibles, pero no de cada combinación numérica ni de cada profundidad del historial.

La respuesta debe añadir exactamente `ask~ind` al historial y avanzar el nivel, continuando un menú vivo o cerrándolo. Una muestra también exige intento terminal y dos ciclos base. Las capturas viejas se reinterpretan desde la respuesta precedente sin modificar sus archivos RAW. Los parámetros o estructuras que no coinciden conservan su cobertura separada. Esta política prueba las acciones del menú, no todas las secuencias aleatorias posibles.


### HAR de Pragmatic del 9 de octubre, 18:57–19:10 UTC

Los siete HAR incluyen Big Bass Mission Fishin’, Bloody Dawn, Bubble Up!, Cash Elevator, Chase for Glory, Dragon Kingdom y Floating Dragon Megaways. El fixture `pragmatic_oct09_seven.json` conserva solo estados y elecciones de bonus, sin datos de sesión.

- El menú repetido `bg/y,n` conserva dos controles aunque cambien `ask`, historial y valores de recompensa. Se valida el historial completo y la confirmación `ch_h` del índice antes de acreditar una muestra. Los historiales no generan rutas independientes; las dos opciones sí requieren muestras distintas.
- El selector `b/pck` demuestra un rango inclusivo y posiciones ocultas disponibles. Usa cobertura estructural por nivel/tamaño, manteniendo el dominio real y sin afirmar todos los índices o premios. La respuesta debe confirmar posición, historial y avance de nivel. Las capturas anteriores se reinterpretan desde el estado previo sin modificar RAW.
- La continuación `bg`, tipo 69, con campos exactos y `level+lifes=3` usa `doBonus(ind=0)`. La evidencia muestra disminución de vidas, reinicio del contador al recibir premios y cierre seguido de `doCollectBonus`. No se generan compras adicionales por vidas ni premios.
- Chase for Glory contiene ejecuciones de las cinco opciones del menú a/b/c/d/r. Big Bass contiene la elección fs_1, pero no demuestra por sí solo las demás elecciones. Los HAR de Cash Elevator y Dragon Kingdom solo contienen tiradas, por lo que no prueban sus menús pendientes ni ausencia de compras o antebet cuando falta doInit.

Estas primitivas se reconocen por estructura del protocolo; no comparan nombres de juegos ni IDs del catálogo.


### Belatra: recorrido compartido y retorno a base

El mismo controlador completa tiradas normales, variantes de antebet, compras y
pruebas de retorno. Se basa en el estado del servidor y los controles del cliente,
no en nombres ni identificadores de juegos.

- `toNextFG` con `freeInfo.remain > 0`: `askNextFG` con `remainFG` del servidor.
  El cliente actual ya no envía `totalWasFG`.
- `respinInfo.nIt > 0`, en `toRespin` o `toNextFG`: `askRespin` tiene prioridad.
  Los respins internos no crean otra compra ni otra opción de antebet.
- `toBonusN`: entrada genérica del cliente con `askBonusN` y `wasAttempt=0`.
  Se exige que la respuesta confirme la categoría y el primer intento.
- Bonus activo de respins con `other.autochoice=start`, contador `attempt`,
  `respinRemain`, `startRespin` y `stopBox`: `askBonusNstart` con el intento recibido.
  Se valida el avance del contador y `userChoice=start`; el cierre puede conservar
  el contador y debe confirmar `BonusN_finished/toPaid` y respins agotados.
  Otros controles u opciones permanecen pendientes.
- `toPaid` o `toDoubleDialog`: liquidación con `finish` y el `historyId` recibido.
  Solamente `finished/toIdle` confirma el cierre.

Las pruebas de retorno guardan también las continuaciones intermedias. Una ronda
con bonus o tiradas gratis se completa como evento conocido, pero no cuenta como
una de las dos tiradas normales consecutivas necesarias para confirmar el retorno.

Evidencia: HAR completos del 9 de octubre de 2026, Rise of Zeus (23:14:27),
Jackpot Pagoda (23:04:56) y Long Neck Fortune (23:19:15), y cliente oficial
`all_content.d4faa069acdbf8987afe.js`. Los HAR anteriores solo incluían mensajes
cifrados; el HTML de inicialización de los nuevos permitió descifrarlos localmente.
`tests/fixtures/belatra_oct09_rounds.json` conserva 24 rondas completas saneadas,
sin claves ni sesiones. `tests/test_belatra_har_rounds.py` reproduce cada petición
contra la respuesta previa y prueba controles desconocidos, falta de confirmación
y la evidencia del retorno. Esto demuestra las rutas capturadas; no sustituye una
prueba nueva de cada juego contra su servidor.
