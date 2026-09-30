# Dos compras con elección incorporadas

Las capturas manuales corresponden a Donut Division (1608) y Le Pharaoh (1562). No contienen cuerpos de respuesta: se contrastaron los formatos con pruebas nuevas de la demo, sin reutilizar sesiones grabadas.

| Juego | Compras con elección | Acciones verificadas | Resultado |
|---|---|---|---|
| Donut Division | fs y fs_2 | wild / warehouse | OK y contrato listo |
| Le Pharaoh | bonus y bonus_2 | fs / lives | OK y contrato listo |

Las elecciones usan POST `https://rgs-demo.hacksawgaming.com/api/play/bet`, `continueInstructions.action` y la ronda actual. Cada ruta se conserva como una muestra independiente. La selección sólo admite familias demostradas por las capturas y anunciadas por el servidor; mantiene los límites de decisiones y repeticiones.

Se verificaron dos giros base, todas las compras anunciadas y ambas elecciones en cada compra relevante. Balance del catálogo: **181 OK, 2 parciales (Stormborn y Strength of Hercules), 1 error (Beam Boys)**.

Verificación: 23 tests de Hacksaw aprobados y revisión independiente sin hallazgos. Suite completa: 761 tests y 73 subtests aprobados, con los cuatro fallos previos de BGaming.
