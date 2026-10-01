# KA Gaming: compras observadas en cuatro HAR

> Evidencia histórica del 30/09. El estado vigente está en [KA_CURRENT_STATUS.md](KA_CURRENT_STATUS.md): 14 juegos con compra y cierre controlado de TheNaughtyTattooist validado el 01/10.

Capturas del 30/09/2026: JadeQuest, ChaosCombat, StellarFantasia y CarnivalBeauty. Incluyen 65 solicitudes de giro, cuatro de ellas con pos=[1]. No incluyen cuerpos de respuesta ni bootstrap de sesión; no se reutilizaron sus credenciales.

El formato común es POST https://rmpdemo.kaga88.com/kaga/command/spin con gn, sel, sid, cps, atb y dn. La compra agrega pos=[1]. El cliente público game.min.2070.js confirma su serialización; las pruebas nuevas de la demo confirmaron que inicia juegos gratis.

| Juego | Compra observada | Prueba remota inicial |
|---|---|---|
| JadeQuest | pos=[1] | Compra y cierre completos; 8 juegos gratis iniciales |
| ChaosCombat | pos=[1] | Compra y cierre completos; 10 juegos gratis iniciales |
| StellarFantasia | pos=[1] | Compra y cierre completos; 10 juegos gratis iniciales |
| CarnivalBeauty | pos=[1] | Compra aceptada; HTTP404 durante continuación, sin cierre confirmado |

La continuación usa el mismo endpoint y los parámetros actuales de la respuesta, omitiendo pos para no comprar otra vez. fsr=0 todavía puede corresponder a fs=true/acb=1: se necesita el paso final hasta fs=false, acb=0, rf=0, sin otros bonus ni juegos pendientes.

El adaptador incorpora compras sólo donde se importó evidencia del juego; no extiende pos=[1] a todas las compras anunciadas del catálogo. Antes de validar exige que la respuesta inicial muestre pos=[1], acb=1 y juegos gratis pendientes. Los estados desconocidos quedan parciales; hay límite de 64 pasos y cierre de sesión al terminar. El coste no se deduce del selector y permanece desconocido.

La prueba posterior desde el adaptador devolvió HTTP404 en startGame para los cuatro juegos. Por tanto sus últimas entradas de Tester Spin siguen ERROR; no se sustituyen por resultados OK a partir de una prueba anterior. Las tres ejecuciones iniciales completas demuestran el formato, pero falta repetirlas desde el adaptador cuando la demo responda nuevamente.

Los HAR y respuestas completas quedan en las carpetas locales de KA. La metadata importada excluye sesiones y firmas. Tests específicos de compras y RMP: 11 aprobados, incluida compra ignorada, aislamiento por juego y rechazo de estados desconocidos. Los cuatro fallos previos de BGaming siguen separados de este trabajo.

## Aplicación al catálogo

El usuario estableció ampliar los formatos aprendidos a todos los juegos aplicables y revisar las excepciones. En esa etapa pos=[1] se propuso a 60 candidatos del catálogo de 828 juegos. Ese criterio fue sustituido por la lista confirmada de 14 juegos con compra; el indicador público no bastaba. El barrido quedó interrumpido después de tres HTTP404 en startGame, sin apostar; no se confirmó compatibilidad adicional. Ver [estándar y resultado](PROVIDER_VALIDATION_STANDARD.md).
