# KA Gaming: estado actual (2026-10-01)

## Catálogo y alcance

El catálogo local contiene 828 juegos. La lista confirmada de juegos con compra es de 14: HotCoinBF, KickCashMonkey2, BuzzKillBonanza, TheNaughtyTattooist, ChaosCombat, CarnivalBeauty, SeasidePelican, TropicalHoliday, PlayfulKitten, InkPaintingMaster, FantasyOktoberfest, StellarFantasia, JadeQuest y ThiefDog. El indicador público `bp` daba 60 candidatos y no es suficiente para identificar compras. Los demás juegos también se prueban con tiradas normales y sus eventos gratuitos naturales.

El estándar es aplicar el contrato común al catálogo y revisar las excepciones con evidencia; no reconstruir cada juego desde cero ni dar por validado un juego sólo por compartir formato.

## Ejecución y sesiones

Cada prueba individual refresca el perfil de firma desde el launcher y el cliente público del juego, y crea una sesión nueva. Todas las tiradas, compras y continuaciones de esa prueba comparten sesión. La versión observada más reciente es `1.0.266 (2071)`; si no puede verificarse el perfil, se informa el error sin reutilizar silenciosamente una firma antigua.

KA comparte un límite máximo de 30 inicios de request por segundo dentro del mismo proceso. El campo **Delay entre operaciones KA (s)** agrega separación entre solicitudes; admite cero y su valor inicial es 0,2 segundos. El delay entre juegos lo controla el usuario: no existe el mínimo automático de un minuto. Estos límites no garantizan que la demo nunca restrinja el acceso.

Un HTTP 404 activa la detención del lote. Otros errores se registran y permiten continuar con los demás juegos; también se contiene un fallo al guardar un resultado. Una solicitud ya enviada puede terminar después de pedir la detención.

## Compras y juegos gratis

El contrato observado usa `POST https://rmpdemo.kaga88.com/kaga/command/spin`, con `gn`, `sel`, `sid`, `cps`, `atb` y `dn`. La compra agrega `pos=[1]` una sola vez. Sus continuaciones omiten `pos` y actualizan los parámetros a partir de la última respuesta.

La compra se acepta como tal sólo con evidencia de `pos=[1]`, `acb=1` y juegos gratis pendientes. `fsr=0` no basta para cerrar: si todavía hay `fs=true` o `acb=1`, falta la operación final. Las tiradas gratis naturales también se continúan, aunque el juego no tenga compra. La cadena tiene un límite de 64 pasos; estados o elecciones desconocidos siguen como parciales.

Los resultados adicionales `as` reconocen las variantes observadas de ThreeMonkeys, AgentAngels y Ares, comprobando estructura y números. No se convierten automáticamente en acciones pendientes ni generan nuevas apuestas si ya contienen el resultado completo. Las características informativas del catálogo no degradan por sí solas una tirada terminal a parcial.

**Limitación de muestreo:** la compra se ejecuta una vez por prueba individual. Si una cuota exige varias muestras de compra, puede seguir pendiente aunque el recorrido único haya terminado correctamente.

## Evidencia y resultados

El barrido histórico de 828 juegos terminó con **737 OK, 90 parciales y 1 error**, antes de los últimos ajustes. Sus causas incluían variantes de resultados adicionales, continuaciones gratuitas, cuotas de compras y un rechazo de posición de apuesta. No se reescribió ese historial ni se volvió a ejecutar todo el catálogo después de los cambios.

La prueba controlada más reciente de **TheNaughtyTattooist** terminó **OK**: una tirada base, una compra con 12 juegos gratis iniciales, continuación y cierre final, seguidos del cierre de sesión. Hubo 18 solicitudes POST, todas HTTP 200 y `ec=0`; el cierre quedó en `fs=false`, `acb=0`, `rf=0` y `fsr=0`. Fue una prueba directa del adaptador y no se guardó como una corrida nueva en la base de datos de la aplicación.

Se hizo con IP renovada, 5 segundos entre operaciones y 105 segundos antes del cierre final. Esos tiempos fueron exclusivos del diagnóstico y **no se añadieron como valores obligatorios**. La prueba no separa el efecto de cambiar la IP del efecto de espaciar solicitudes ni demuestra que 105 segundos sean necesarios.

Antes hubo HTTP 404 tanto durante un cierre como en `startGame`. Un 404 por sí solo no prueba un bloqueo, un endpoint inexistente o una compra mal formada. En este entorno, cerrar la aplicación antes de renovar la VPN permitió volver a operar; no se confirmó el mecanismo de red responsable.

## Verificación del código

La suite completa terminó con **793 pruebas aprobadas, 73 subtests aprobados y 4 fallos preexistentes de BGaming**. Los fallos están en dos pruebas de HyperHive y dos de selección de bonus; no se presentan como resueltos por este trabajo de KA.

Los HAR, firmas, sesiones y respuestas completas permanecen locales. Las fixtures publicadas contienen estados sanitizados para comprobar compras y eventos naturales, sin credenciales reutilizables.
