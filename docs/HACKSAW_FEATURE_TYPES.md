# Hacksaw: compras de bonus y FeatureSpins

ActualizaciÃ³n: 2026-10-11. Evidencia: cinco HAR completos aportados por el usuario. Dos son capturas del mismo juego Max Win Machine. Las fixtures de tests conservan solo configuraciÃ³n de funciones, tipos del cliente y estados de ronda; excluyen sesiones, usuarios y saldos.

## Fuente y clasificaciÃ³n

`authenticate.bonusGames` declara IDs y multiplicadores. No todos los IDs son compras de bonus: `FeatureBuyItem.get_featureBuyItemType()` en el cliente separa `FeatureSpinItem`, `BonusBuyItem` y `BestOfBonusItem`.

La primitiva lee el constructor `FeatureBuyItem` para localizar el argumento de tipo, sin depender del nombre minificado ni del nÃºmero fijo de argumentos. DespuÃ©s lee `getFeatureBuyItems` del `main.js` de la versiÃ³n actual. Un tipo explÃ­cito prevalece sobre el ID. Solo aplica el default `mod_`/`bob_` cuando el getter del cliente demuestra ese contrato. No usa precios, tÃ­tulos ni listas de IDs de juego como criterio.

Los FeatureSpins se guardan como `FEATURE_SPIN` y se muestran por separado en el resumen. No se clasifican automÃ¡ticamente como antebet. Las compras de bonus conservan `PURCHASE`. Ambos usan el selector demostrado `bets[].buyBonus`, con `betAmount` base y multiplicador declarado por el servidor. El cobro `win_presentation_complete` se conserva como continuaciÃ³n, nunca como compra.

El ejecutor respeta `disableFeatureSpins` y `disableBonusBuys` por categorÃ­a, cuando estÃ¡n explÃ­citamente activados. Los IDs no resueltos, los tipos desconocidos y los fallos de lectura del cliente quedan pendientes; no se ejecutan ni prueban ausencia. Una declaraciÃ³n completa exige que todos los tipos anunciados estÃ©n resueltos. La cobertura conserva tanto compras como FeatureSpins hasta verificar su cierre.

## Casos contrastados

| Juego | Compras de bonus | FeatureSpins |
|---|---:|---:|
| Le Sortudo | 0 | 2 |
| Max Win Machine (dos HAR) | 0 | 4 |
| Supreme Zeus | 2 | 2 |
| Marlin Masters OG | 2 | 2 |

Los IDs y los nombres de esta tabla son casos de prueba, no reglas de detecciÃ³n. Las cinco capturas enseÃ±an la misma clasificaciÃ³n del cliente y el cierre de ronda por `completed` o por confirmaciÃ³n desde `wfwpc`. La ausencia de una categorÃ­a de antebet separada sigue sin confirmar: el resumen indica Â«Sin datosÂ».

## ValidaciÃ³n

`tests/test_hacksaw_feature_types.py` prueba los cinco HAR sanitizados, las variantes de constructor, overrides, flags independientes, tipos no escalares, extracciÃ³n fallida/parcial y cobertura de FeatureSpins. `tests/test_hacksaw_provider.py` verifica el envÃ­o del selector, confirmaciÃ³n de la misma ronda y elecciones soportadas. Las pruebas son locales; no equivalen a un recorrido manual de todos los clientes del proveedor.

Suite completa de la actualización: 1123 pruebas y 221 subtests correctos, con tres advertencias preexistentes del catálogo Pragmatic.
