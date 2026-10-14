# Nolimit City: catálogo oficial

Proveedor integrado: `nolimit_city` / **Nolimit City**.

El catálogo oficial de afiliados contiene 140 demos del estudio en el corte del
2026-10-13. Fuente: https://nolimitcity.com/json/games.json. El enlace documentado
https://nolimitcity.com/json/affiliateGames.json redirige a ese feed.
Página pública: https://nolimitcity.com/games.

Cada fila usa name, code, studio y url. Solo se incorporan filas studio=Nolimit City;
no se atribuyen a este proveedor los juegos de otros estudios de Playin/Evolution.
code es la identidad de lanzamiento, symbol conserva su capitalización y slug
usa su forma normalizada. El enlace oficial es playin.com/embed/v1/demo/<code>.
Cambios de título no alteran esa identidad. Duplicados, colisiones de identidad,
enlaces de otro origen, nombres vacíos y catálogos vacíos se rechazan.

El snapshot incluido permite cargar el catálogo sin red. Una actualización en
línea agrega o actualiza registros sin borrar juegos existentes; este feed no
tiene autoridad de eliminación. No se inventan URLs de miniaturas: el feed no
las suministra. Los enlaces de demo permiten abrir el juego desde la grilla.

## Estado de ejecución

Los 140 juegos están cargados como PENDIENTE. Esta incorporación certifica el
catálogo y la identidad de sus demos, no sus rondas ni sus opciones. Al intentar
una prueba, el adaptador informa PARCIAL y genera un diagnóstico; no envía giros
por un protocolo supuesto y no produce contratos de farm ejecutables.

Compras, Action Spins, antebets y cantidades permanecen sin confirmar. Los flags
publicitarios no sustituyen el dominio de opciones de la sesión. El paso siguiente
es aprender primitivas a partir de HAR representativos y contrastarlas con el
servidor: autenticación, menú de opciones, precios, cargos, elecciones, cierre y
retorno. Las variantes de Playin no se presuponen iguales a las de otros accesos.

El proveedor aparece en el selector del escritorio y en el registro del ejecutor
por lotes. El catálogo se incluye en la compilación del ejecutable completo.


## Primer protocolo observado: Airport Security

La captura suministrada incluye las jugadas en log._warpWebSockets, fuera de
log.entries. POST https://demo.nolimitcity.com/EjsFrontWeb/fs devuelve la URL
HTTPS /EjsGameWeb/gs y una clave de sesión. El cliente adjunta ?data=<clave>,
cambia https por wss y /gs por /ws/game. La clave no se fija en el programa.

Las peticiones son JSON cifrado con RC4 y expresado en hexadecimal. Las respuestas
son JSON con compresión LZW indicada por lzw:. Se contrastó la transformación
con GameCommunication y SocketAdapter del cliente incluido en el mismo HAR.
El lector valida la conexión correspondiente, los códigos LZW y sus límites de
expansión; no interpreta recursos gráficos ni peticiones de analítica como apuestas.

El sobre lleva type=normal, protocol, id y data. El comando está en content:

- normalBet: apuesta normal en bet.
- featureBet: bet es la apuesta base; featureName y playerInteraction.featureName
  seleccionan la opción. El débito real usa el multiplicador declarado.
- zeroBet: continuación de la ronda con bet=0.00; no es una compra nueva.

La inicialización declara game.featureBuyTimesBetValue (name, type, price),
allowedFeatureBets y featureBetLevels. En esta muestra hay cuatro compras de tipo
FREESPIN (80x, 240x, 500x y LUCKY_DRAW 212x) y tres opciones de tipo BOOSTED_BET
(1.4x, 12x y 4500x). LUCKY_DRAW es una sola opción aunque otorgue distintos premios.
Los boosted bets no se cuentan como compras ni se reclasifican automáticamente
como antebets o Action Spins. Su tipo y sus precios proceden del servidor.

La respuesta confirma wasFeatureBuy/wasBoostedBet, playedBetValue, win,
accumulatedRoundWin, nextMode, freespinsLeft, features.available y balance.
El id enlaza cada petición con su respuesta; no es por sí solo un identificador
de ronda. Los saldos intermedios pueden omitirse durante las tiradas gratuitas.
El cierre observado exige nextMode=NORMAL, freespinsLeft=0 y ausencia de elecciones.

Se decodificaron 102 mensajes: 51 intercambios, incluida la inicialización.
Las 14 rondas pagadas y 36 continuaciones están cerradas y contabilizadas:
10000.00 de saldo inicial - 10273.80 de coste + 2756.05 de premios = 2482.25.
Todos los siete selectores anunciados aparecen en la muestra. Solo existe un giro
normal al final: esta captura no prueba dos rondas posteriores ni certifica OK
en una sesión nueva. El ejecutor en vivo sigue pendiente.

## Analizador offline

```powershell
.\.venv\Scripts\python.exe tools/analyze_nolimit_har.py "ruta\captura.har" --output "ruta\informe.json"
```

El informe conserva precios, cargos, pagos, selecciones y cierres; no exporta
claves de sesión ni reproduce tráfico. El HAR original y las claves permanecen
locales bajo data/. Las pruebas incluyen mensajes reducidos sin credenciales y
casos negativos de precio, identidad y compresión. No hay ramas por título o ID.
