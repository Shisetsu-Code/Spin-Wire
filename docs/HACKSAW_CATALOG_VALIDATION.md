# Hacksaw: resultado completo del catálogo

Estado al 30/09/2026. Se intentaron los **184 juegos** del catálogo local: **181 OK**, **2 PARCIAL**, **1 ERROR**. No quedan juegos sin probar ni bloqueados por el límite de demo en el resultado final.

La prueba ejecutó dos giros base y las compras anunciadas en cada autenticación. Cuando apareció una elección compatible, se probaron las rutas y el cierre de la misma ronda. `OK` y contrato listo corresponden a esas acciones observadas; no garantizan recorrer todos los eventos aleatorios o todas las repeticiones posibles de una elección.

## Casos pendientes

| Juego | ID | Resultado | Motivo observado |
|---|---|---|---|
| Stormborn | 1875 | PARCIAL | Compra en started, acciones ts / fs |
| Strength of Hercules | 1697 | PARCIAL | Compra en started, acciones fs / labyrinth |
| Beam Boys | 1426 | ERROR | Apuesta devuelve statusCode 1; sin cierre terminal |

Las compras de estos dos juegos requieren comprobar y modelar sus elecciones. No se adivinaron payloads ni se declararon listas. Beam Boys conserva el error observado en la primera pasada y no se volvió a probar durante la reanudación.

## Límite de demo y reanudación

La primera pasada dejó 134 OK, 2 parciales, 1 error, 16 bloqueados y 31 sin probar. El servidor devolvió `statusCode: 21`, `Demo mode limit reached!`, incluso después de esperar. Se pausó a pedido del usuario y se publicó el estado parcial.

El usuario luego indicó que había conectado una VPN y autorizó reanudar. Rise of Fortuna completó la comprobación inicial. Se recorrieron los 47 pendientes: los 16 antes bloqueados pasaron; entre los 31 restantes, 29 pasaron y dos quedaron parciales. No se cambió el protocolo ni se reutilizaron sesiones grabadas. Esto no determina cómo contabiliza el servidor su límite de demo.

El recorrido está terminado; no hay reintentos programados. Los tres casos de seguimiento quedan pendientes de trabajo posterior.

## Resultados y evidencia

- [Listado completo en JSON](hacksaw-catalogo-resultados.json).
- [Listado completo en CSV](hacksaw-catalogo-resultados.csv).
- [Integración y formato común](HACKSAW.md).
- [Capturas manuales](HACKSAW_MANUAL_VALIDATION.md).
- [Compras con play/gamble](HACKSAW_CHOICES.md).

Las solicitudes y respuestas completas están conservadas localmente en `data/providers/hacksaw/<ID>/`. No publicar HAR, sesiones o identificadores efímeros. Los listados compartidos contienen resultados resumidos sin credenciales. El historial de Tester Spin conserva también los intentos anteriores afectados por el límite; estos listados muestran el resultado seleccionado tras la reanudación.

Validación de código previa al barrido: 23 tests de Hacksaw y revisión independiente aprobados. Suite completa: 761 tests y 73 subtests aprobados, con cuatro fallos preexistentes de BGaming. El barrido y su reanudación no requirieron cambios de código del adaptador.


## Capturas manuales posteriores

Donut Division y Le Pharaoh dejaron de estar parciales tras incorporar sus elecciones demostradas por HAR: wild/warehouse y fs/lives. Se verificaron ambas rutas en las dos compras relevantes de cada juego, con sesiones nuevas y cierre terminal. [Detalle y validación](HACKSAW_ADDITIONAL_CHOICES.md). El total actualizado es 181 OK, 2 parciales y 1 error; los conteos históricos de la primera reanudación describen ese momento, antes de esta ampliación.
