# Hacksaw: cierre de formatos y compras

Se incorporaron las dos capturas manuales aportadas como evidencia local por juego. Los identificadores se comprobaron en los recursos del cliente iniciador: 2253 corresponde a Dr Zappo y 2408 a Epic Ze Zeus. Ambas capturas confirman la apuesta JSON a `/api/play/bet`, el selector `bets[].buyBonus` y el cierre `win_presentation_complete`.

Los HAR no contienen los cuerpos de respuesta ni la autenticación inicial. Por eso se usaron para contrastar el formato, y la ejecución se verificó con sesiones demo nuevas desde Tester Spin, sin reutilizar las sesiones grabadas.

| Juego | Opciones verificadas | Resultado |
| --- | --- | --- |
| Dr Zappo (2253) | mod_bonus x3; mod_laser x100; fs x50; fs_2 x200 | 2 giros base y las 4 opciones OK; cobertura 6/6; contrato listo |
| Epic Ze Zeus (2408) | mod_bonus x3; mod_activator x50; fs_consume x100; fs_progressive x250; fs_epic x2000 | 2 giros base y las 5 opciones OK; cobertura 7/7; contrato listo |
| Fist of Destruction Megamultiplier (2536), validación previa | mod_bonus x3; mod_expand x50; mod_expand_2 x250; fs x110; fs_2 x275 | giro y 5 opciones OK; cobertura 7/7; contrato listo |

Estos tres representantes muestran diez selectores distintos con el mismo formato de apuesta. No hizo falta introducir payloads especiales para Dr Zappo o Epic Ze Zeus: el adaptador obtiene la lista y los precios de cada autenticación. No interpreta el nombre `fs` como un precio universal; x50 y x110 son precios distintos para juegos distintos.

El cierre está probado mediante `round.status=completed`, sin acciones pendientes, y confirmación de la misma ronda cuando llega `wfwpc`. Las muestras y payloads completos se guardaron por intento en la carpeta local de cada juego. Los contratos compartidos excluyen las sesiones y los identificadores efímeros de ronda.

La tercera captura aportó Epic Bullets and Bounty (2185), con elecciones `play` y `gamble` dentro de las compras x100 y x200. Ambas rutas se implementaron y verificaron con sesiones demo nuevas; ver [detalle de elecciones](HACKSAW_CHOICES.md).

Después se inició el barrido del catálogo a pedido del usuario. El balance y las limitaciones actuales están en [prueba del catálogo](HACKSAW_CATALOG_VALIDATION.md). Ya no aplica la declaración anterior de que sólo se probaron tres representantes. El usuario autorizó después la reanudación y se completaron los 184 juegos: 179 OK, 4 parciales y 1 error. No quedan juegos bloqueados o sin probar.

Las 21 pruebas de Hacksaw pasan. La suite completa mantiene 759 pruebas aprobadas y cuatro fallos previos de BGaming.
