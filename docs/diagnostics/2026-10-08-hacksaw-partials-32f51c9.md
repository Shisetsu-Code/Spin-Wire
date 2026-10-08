# Diagnóstico de parciales Hacksaw — 8 de octubre de 2026

## Alcance y versión

Código base: `32f51c951dfbf4705e7482abafa2561bb21eee15`.
Rama de diagnóstico: `diagnostics/partials-32f51c9`.

Se seleccionaron exclusivamente los dos registros `PARCIAL` publicados en `docs/hacksaw-catalogo-resultados.csv`: Stormborn (1875) y Strength of Hercules (1697). El catálogo es histórico; no representa todos los estados actuales del almacenamiento local del usuario. Beam Boys figura como ERROR, no PARCIAL, y no formó parte de esta prueba. No se repitieron los 184 juegos ni se probaron otros proveedores.

## Reproducción con el ejecutor original

[GitHub Actions: reproducción 37730897604](https://github.com/Shisetsu-Code/Spin-Wire/actions/runs/37730897604).
Commit de diagnóstico: `43403a058b9c60346cd5e7a4960990d564f6998a`.

Se ejecutaron las 23 pruebas existentes de `tests/test_hacksaw_provider.py`: 23 aprobadas, 0 fallos, 0 errores y 0 omitidas. No se ejecutó la suite completa del repositorio.

Se abrió una sesión demo nueva por cada pareja juego/compra y se realizó un giro base antes de probar la compra pendiente. No se reutilizaron credenciales de capturas. La selección de modos se limitó a SPIN y la compra objetivo; no se modificó la lógica de las transiciones.

| Juego | Cliente observado | Compra | Acciones anunciadas | Resultado original |
|---|---|---|---|---|
| Stormborn | 1.26.7 | bonus | ts, fs | PARCIAL |
| Stormborn | 1.26.7 | bonus_2 | ts, fs | PARCIAL |
| Strength of Hercules | 1.23.1 | bonus | fs, labyrinth | PARCIAL |
| Strength of Hercules | 1.23.1 | bonus_2 | fs, labyrinth | PARCIAL |

Los cuatro giros base cerraron. Las cuatro compras fueron aceptadas, pero dejaron `round.status=started` con las elecciones indicadas. Los 17 intercambios HTTP devolvieron 200; las respuestas de la API devolvieron `statusCode=0`. No fue un fallo de conectividad, de autenticación ni del payload de compra en estas muestras.

La causa se encuentra en `tester_spin/providers/hacksaw/adapter.py:201–206`: la lista admite solamente play/gamble, wild/warehouse y fs/lives. Las parejas anunciadas no encajan y el ejecutor sale del bucle sin enviar una elección. Después conserva correctamente el estado PARCIAL porque la ronda no terminó.

## Experimento controlado sobre las elecciones observadas

[GitHub Actions: experimento 37731194262](https://github.com/Shisetsu-Code/Spin-Wire/actions/runs/37731194262).
Commit del workflow experimental: `9184a4a3f798b6823173b0c910332994b9d8a3e2`.

Se extendió exclusivamente la lista de familias **en memoria**, agregando `("ts", "fs")` y `("fs", "labyrinth")`. No se modificaron archivos del adaptador, el payload de compra, las reglas de cierre ni la rama habitual del repositorio. El workflow verificó que `tester_spin/` y `tests/` permanecieran iguales al commit base. Esto es evidencia experimental, no una corrección integrada en producción.

| Juego | Compra | Rutas verificadas | Cierre |
|---|---|---|---|
| Stormborn | bonus | ts y fs | 2/2 |
| Stormborn | bonus_2 | ts y fs | 2/2 |
| Strength of Hercules | bonus | fs y labyrinth | 2/2 |
| Strength of Hercules | bonus_2 | fs y labyrinth | 2/2 |

Las ocho rutas fueron probadas una vez cada una. Las elecciones se enviaron mediante `continueInstructions.action`, conservando la sesión, secuencia y ronda correspondientes. En todas se observó:

`started → elección anunciada → wfwpc → win_presentation_complete → completed`

El identificador de ronda se mantuvo entre elección y confirmación, y el cierre informó `possibleActions=[]`. El experimento realizó 36 intercambios HTTP: 4 consultas de versión, 4 autenticaciones y 28 solicitudes play/bet. Los 36 devolvieron HTTP 200; las respuestas de la API devolvieron `statusCode=0`.

Un verificador offline contrastó cada elección con las acciones de la respuesta previa, el incremento de seq, la conservación de roundId y el cierre posterior. Confirmó ocho rutas distintas, no solamente el estado OK del resumen.

## Conclusión y límites

Para las muestras probadas, el bloqueo es la ausencia de dos familias de selección en el adaptador, no el descubrimiento ni la ejecución inicial de las compras. Incorporar esas familias permitió cerrar todas las rutas pendientes examinadas, sin excepciones por nombre de juego.

Queda integrar el cambio con regresiones específicas y ejecutar la comprobación de retorno mediante giros normales posteriores. Esta tarea no realizó esa comprobación adicional ni certifica todos los resultados aleatorios o posibles eventos futuros. Los registros originales no fueron promovidos a OK en el catálogo ni en el almacenamiento local.

## Evidencia y reproducibilidad

Los workflows están en `.github/workflows/hacksaw-partial-analysis.yml` y `.github/workflows/hacksaw-choice-probe.yml` dentro de la rama de diagnóstico. Ejecutan únicamente demos y publican intercambios sanitizados. Las credenciales y sesiones se ocultan; roundId se reemplaza por un hash que conserva las relaciones de igualdad.

- Artefacto de reproducción: `hacksaw-partials-37730897604`, ID `11529643067`, SHA-256 `fbd53d3ad15762d6cb39319362e8498833f287b309be27a8acfaf1505d649fc8`.
- Artefacto experimental: `hacksaw-choice-probe-37731194262`, ID `11530040529`, SHA-256 `574e38d440dd97bfe5ca86e65b5ddbeaf0d9a9290a8990549850f8ed58dc75f2`.

Los artefactos de Actions tienen retención de siete días. Se entregó también una copia descargable con ambos conjuntos de evidencia y un verificador offline.

El intento inicial 37730773942 falló antes de instalar dependencias o contactar demos porque el checkout superficial no contenía el commit base. Se corrigió el workflow mediante `fetch-depth: 0`; no fue un fallo de los juegos.
