# Validación de las mejoras de detección

Actualización documental: 9 de octubre de 2026. La batería de regresión incluye los resúmenes, la migración de cobertura, protocolos Pragmatic, compras Red Tiger y primitivas 3 Oaks. Ejecutar `python -m pytest tests -q` para verificar el checkout; el resultado de una ejecución anterior no reemplaza esta comprobación.

## Evidencia obtenida durante la corrección

- La ejecución completa anterior al cierre documental aprobó 936 pruebas y 221 subpruebas.
- La captura 3 Oaks del 7 de octubre a las 21:50:41 se redujo a un fixture de 72 acciones play aceptadas; las tres compras terminan sus rondas.
- Una sesión nueva de 3 Super Coin Volcanoes completó un giro normal y tres compras con 66 solicitudes play. Las compras cerraron y se comprobó el retorno a giros normales. El caso verificó la composición de rutas finitas de compra frente a otra ruta sin dominio resuelto.
- La compilación de escritorio anterior al cierre documental incluyó `purchase_input_routes` y pasó la comprobación de arranque.

Son comprobaciones de esas versiones y muestras; otros juegos pueden seguir pendientes por sintaxis desconocida, acciones ambiguas o problemas de disponibilidad. La solución activa de 3 Oaks no elige solicitudes por nombre del juego.

## Regresiones que deben preservarse

| Área | Prueba de comportamiento |
| --- | --- |
| Resumen | Giros y continuaciones no cuentan como compras; evidencia insuficiente conserva Sin datos. |
| Red Tiger | Oferta del servidor sin confirmación del cliente no fuerza compra ni cobertura pendiente. |
| Estado base | Estados persistentes normales reconocidos cierran; bonus y elecciones pendientes no. |
| Pragmatic | Selecciones, recolección, cascadas y errores mantienen sus transiciones y evidencia. |
| Historial | Un modo actualmente opcional no vuelve a ser requerido por un pendiente antiguo. |
| 3 Oaks | Separar giro y compra; preservar tipos y dominios; rechazar rutas abiertas o incompatibles. |
| Rutas mixtas | Mantener opciones finitas conocidas sin extenderlas a valores fuera del dominio. |

Las fixtures publicadas excluyen sesiones reutilizables. HAR completos, informes de ejecución y capturas originales permanecen en el almacenamiento local. Los JSON/CSV antiguos de catálogo son históricos y no se usan como prueba de cobertura actual.

## Regresión de las tres capturas adicionales

Las pruebas `test_oaks_capture_primitives.py` y `test_oaks_capture_replay.py` contrastan 58 acciones de un cliente con middleware sobrescrito y selectores desplazados, 122 acciones de un cliente con compras por cantidad de scatters y antebet, y 21 acciones de bonus natural con llamadas literales de flow. También rechazan transportes no demostrados, transformaciones desconocidas y antebets sin reenvío confirmado.

Las verificaciones remotas adicionales se hicieron en sesiones nuevas y directorios aislados. El proveedor devolvió HTTP 429; se conserva el bloqueo como resultado pendiente/error, sin declarar compras validadas en vivo por haber aprobado la reproducción de las capturas.
