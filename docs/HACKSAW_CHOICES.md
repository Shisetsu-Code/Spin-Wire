# Hacksaw: compras con elección

Se integró la continuación encontrada en la tercera captura manual: **Epic Bullets and Bounty**, ID 2185, cliente 1.2.3.

La captura contiene 33 solicitudes de apuesta y no incluye los cuerpos de las respuestas. Se contrastó con una sesión nueva de la demo para confirmar las opciones anunciadas y el cierre de las rondas.

| Selector | Multiplicador | Resultado remoto |
|---|---:|---|
| mod_bonus | x5 | Cierre confirmado |
| mod_duel | x100 | Cierre confirmado |
| mod_bounty | x100 | Cierre confirmado |
| bonus | x100 | play y gamble, ambos cerrados |
| bonus_2 | x200 | play y gamble, ambos cerrados |
| fs_epic | x1000 | Cierre confirmado |

Endpoint compartido: `https://rgs-demo.hacksawgaming.com/api/play/bet`.
Las compras usan `bets[0].buyBonus`; las elecciones usan `continueInstructions.action` con `play` o `gamble`, junto con la sesión, secuencia y ronda actuales. El cierre usa `win_presentation_complete` cuando el servidor lo solicita. Las credenciales de la captura manual no se reutilizan.

El adaptador prueba las opciones anunciadas y separa las muestras de cada ruta. Después de una prueba de gamble, termina mediante play si el servidor lo ofrece. Limita las decisiones a ocho por ronda y las rondas extra a dos por modalidad. Las elecciones nuevas o pendientes impiden declarar cobertura completa.

Validación: 2 giros base, 6 opciones de compra y las 2 rutas de cada compra con elección. Resultado remoto OK, cobertura 12/12 y contrato listo para este juego. Esto no significa que se hayan probado todos los juegos del catálogo ni todas las repeticiones posibles de gamble.

Pruebas locales: 21 tests de Hacksaw aprobados, incluida la protección contra opciones tardías y compras de prueba sin límite. La revisión independiente aprobó los ajustes.

El contrato exportado excluye valores de sesión y ronda. Evidencia de red completa conservada localmente en la carpeta de datos de Tester Spin.


## Otras familias de elección

Se agregaron wild/warehouse (Donut Division) y fs/lives (Le Pharaoh), con el mismo campo continueInstructions.action. Ambas rutas se verificaron en cada una de sus dos compras. [Detalle](HACKSAW_ADDITIONAL_CHOICES.md). Stormborn y Strength of Hercules conservan sus elecciones pendientes; no se habilitan acciones desconocidas por similitud de nombre.
