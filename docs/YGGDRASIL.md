# Yggdrasil en Tester Spin

Yggdrasil agregado al selector y a la cola de reintentos. Catálogo inicial importado de MultiPlay: 159 juegos. La actualización incorpora enlaces públicos sin eliminar juegos existentes, porque el snapshot y una página pública no prueban que se haya recorrido toda la paginación actual.

MultiPlay conserva dos compras observadas en una demo con `gameid=10964`:

| Comando | amount observado | coin observado |
| --- | ---: | ---: |
| BB_2 | 65 | 0.1 |
| BB_5 | 390 | 0.1 |

Transporte: POST a `https://demo.yggdrasilgaming.com/game.web/service?fn=play`, con `application/x-www-form-urlencoded`. También se observaron los campos channel, currency, lang, gameid, clientinfo y los identificadores efímeros gameHistorySessionId/gameHistoryTicketId. Los importes pertenecen a esas capturas: no son multiplicadores universales ni valores para copiar a todos los juegos.

El adaptador analiza capturas HAR locales por juego y conserva cada comando BB_* por separado. No deduce el identificador de un juego a partir de una captura ajena. Consulta la página oficial para vincular su lanzador de demo y detectar el anuncio Buy Bonus, sin inventar comandos.

La ejecución directa queda pendiente: la evidencia importada no demuestra bootstrap, giro base, continuaciones ni cierre de ronda. HTTP200 no basta para aprobar un juego. Las sesiones y clientinfo no se incluyen en los contratos reutilizables. Las compras de un representante no se propagan a todo el catálogo.

En el representante **3 Gladiators vs Caesar**, la página oficial anuncia Buy Bonus y vincula `gameid=10511`. Su demo se abrió, pero el navegador remoto reportó que no soporta WebGL. Se dejó pendiente conforme al alcance acordado, sin recorrer las 159 demos ni intentar solucionar ese bloqueo ahora.

Referencia: [página oficial del representante](https://yggdrasilgaming.com/games/3-gladiators-vs-caesar/), y `knowledge/providers/yggdrasil/STATUS.md` de MultiPlay (actualizado el 29/09/2026).

Verificación final: 9 pruebas de Yggdrasil aprobadas desde el repositorio final. Suite completa: 738 aprobadas, 73 subtests aprobados y cuatro fallos previos de BGaming:

- `test_big_bucks_bundle_uses_bet_only_and_buy_bonus_x120`
- `test_blazing_bundle_discovers_betting_actions_and_purchases`
- `test_contract_registry_derives_legacy_views_without_choice_hardcoding`
- `test_state_name_is_never_promoted_to_a_different_server_action`
