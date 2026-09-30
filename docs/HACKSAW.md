# Hacksaw Gaming en Tester Spin

Integración del 30/09/2026: proveedor registrado en el selector y la cola de reintentos, con **184 juegos y 184 miniaturas**. Se usan los identificadores numéricos oficiales para conservar juegos sin página individual y URLs con caracteres codificados.

Estado actualizado: **los 184 juegos fueron probados**, con 179 OK y contrato listo, 4 parciales por elecciones no modeladas y 1 error del proveedor. Los 16 antes bloqueados por el límite de demo pasaron al reanudar; no quedan juegos sin probar. Ver [resultados completos y casos pendientes](HACKSAW_CATALOG_VALIDATION.md).

El primer representante validado fue **Fist of Destruction Megamultiplier**, ID **2536**, cliente **1.12.3**, con las siguientes compras:

| Selector anunciado | Multiplicador |
| --- | ---: |
| mod_bonus | x3 |
| mod_expand | x50 |
| mod_expand_2 | x250 |
| fs | x110 |
| fs_2 | x275 |

Formato observado: autenticación POST JSON a `https://rgs-demo.hacksawgaming.com/api/play/authenticate`, y apuesta POST JSON a `/api/play/bet`. El giro base lleva `bets[].betAmount`; las opciones agregan `bets[].buyBonus` con el selector anunciado para ese juego. El adaptador consulta la versión del cliente y genera una sesión nueva en cada prueba. No reutiliza sesiones guardadas.

Algunas respuestas llegan en estado `wfwpc`. El cliente publicado y las capturas confirmaron el cierre mediante otra petición al mismo `/play/bet`, con `continueInstructions.action=win_presentation_complete` y referencia a la ronda actual. Sólo se aprueba cuando la confirmación corresponde a la misma ronda, `round.status=completed` y `possibleActions=[]`. Las elecciones `play` y `gamble` también están implementadas y probadas, con muestras separadas y límites de rondas adicionales; ver [compras con elección](HACKSAW_CHOICES.md). Otras acciones quedan pendientes; HTTP200 por sí solo no basta.

La prueba en el navegador remoto reportó incompatibilidad de dispositivo y su acceso directo a la API devolvió403. La conexión desde Tester Spin sí funcionó, por lo que pudo validarse el formato sin solucionar ese navegador. Los payloads completos quedan como evidencia local por intento; los contratos reutilizables excluyen los identificadores de sesión y ronda.

La integración conserva selectores previos si falla un reintento y respeta la duración mínima de ronda según las unidades del cliente. La actualización del catálogo no autoriza eliminar entradas a partir de una respuesta incompleta.

Verificación: 21 pruebas de Hacksaw aprobadas, incluida cobertura, muestras por intento, selectores, confirmación de la misma ronda y exportación sin sesiones. Revisión independiente sin problemas pendientes.

Suite completa: 759 pruebas y 73 subtests aprobados; cuatro fallos previos de BGaming:

- `test_big_bucks_bundle_uses_bet_only_and_buy_bonus_x120`
- `test_blazing_bundle_discovers_betting_actions_and_purchases`
- `test_contract_registry_derives_legacy_views_without_choice_hardcoding`
- `test_state_name_is_never_promoted_to_a_different_server_action`

Fuentes: [catálogo oficial](https://www.hacksawgaming.com/games/slots), [página del representante](https://www.hacksawgaming.com/games/fist-of-destruction-megamultiplier) y su cliente público. Evidencia local en `data/providers/hacksaw/2536/analysis/` y `tests/` dentro de Tester Spin.
