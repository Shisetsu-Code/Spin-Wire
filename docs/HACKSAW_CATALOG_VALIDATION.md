# Hacksaw: prueba del catálogo y pausa

Estado al 30/09/2026. El catálogo local contiene 184 juegos. Se probó en serie, con dos giros base y las compras anunciadas por cada autenticación; cuando apareció una elección compatible se probaron las rutas disponibles y el cierre de la misma ronda.

| Resultado | Juegos |
|---|---:|
| OK y contrato listo | 134 |
| Parcial: elección pendiente | 2 |
| Error del proveedor | 1 |
| Bloqueados por límite de demo | 16 |
| Sin probar | 31 |

**El recorrido está pausado por instrucción del usuario. Reanudar Hacksaw solamente cuando el usuario lo indique.** No hay reintentos programados. Tras una pausa se comprobó nuevamente el límite y la API siguió devolviendo `statusCode: 21`, `Demo mode limit reached!`.

## Casos que requieren seguimiento

- Donut Division (1608): compra devuelve `started` con acciones `wild` y `warehouse`. Falta comprobar y modelar esas elecciones.
- Le Pharaoh (1562): compra devuelve `started` con acciones `fs` y `lives`. Falta comprobar y modelar esas elecciones.
- Beam Boys (1426): apuesta devuelve `statusCode: 1`. No alcanzó cierre terminal.
- Desde Rise of Fortuna (2213), 16 juegos quedaron afectados por el límite de la demo. Esos resultados no demuestran incompatibilidad del juego ni del adaptador. Rise of Fortuna había iniciado la ejecución antes del bloqueo.

La aplicación puede mostrar ERROR/PARCIAL para los resultados del límite, porque el adaptador actual los registra como error remoto genérico. El listado adjunto los clasifica como `BLOQUEADO_DEMO` para evitar confundirlos con fallos de compatibilidad; esa clasificación es del informe, no un nuevo estado implementado en la aplicación.

## Cómo retomar

Cuando el usuario autorice continuar, comprobar primero un juego bloqueado con una sesión demo nueva. Si persiste el código 21, pausar de nuevo. Si se libera, repetir los 16 bloqueados y recorrer los 31 sin probar; conservar el historial anterior. Revisar después las elecciones de Donut Division y Le Pharaoh. No cambiar credenciales, identidades ni mecanismos de acceso para eludir el límite.

`OK` significa que las acciones ejecutadas en esta corrida terminaron correctamente. Dos giros y las compras no garantizan recorrer todos los eventos aleatorios o todas las posibles repeticiones de una elección.

## Resultados y evidencia

- [Listado completo y pendientes en JSON](hacksaw-catalogo-resultados.json).
- [Juegos intentados en CSV](hacksaw-catalogo-resultados.csv).
- [Integración y formato común](HACKSAW.md).
- [Capturas manuales](HACKSAW_MANUAL_VALIDATION.md).
- [Compras con play/gamble](HACKSAW_CHOICES.md).

Las solicitudes y respuestas completas se conservan localmente en `data/providers/hacksaw/<ID>/`. No publicar HAR, sesiones o identificadores efímeros. Los archivos compartidos aquí contienen resultados resumidos sin credenciales.

Validación de código previa al barrido: 21 tests de Hacksaw aprobados y revisión independiente sin hallazgos pendientes. Suite completa: 759 tests y 73 subtests aprobados; cuatro fallos preexistentes de BGaming. No se atribuyen al recorrido remoto del catálogo.
