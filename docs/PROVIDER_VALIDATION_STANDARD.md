# Estándar de integración y validación de proveedores

Estándar indicado por el usuario el 30/09/2026.

1. Identificar el formato común de giro, compra y continuación mediante capturas manuales y respuestas reales.
2. Implementar el formato por proveedor o familia y aplicarlo como candidato a todos los juegos aplicables del catálogo. No exigir un HAR individual cuando ya existe un formato común observado. La declaración de compra habilita la prueba; no constituye validación.
3. Ejecutar el catálogo priorizando los juegos con compras. Registrar giro base, cada compra, elecciones y cierre por separado. Validar sólo con efectos y estados terminales confirmados por el proveedor.
4. Conservar solicitudes y respuestas locales para los juegos que fallen. Clasificar errores de transporte, rechazos, formatos diferentes y continuaciones desconocidas. Revisar primero las excepciones que aportan nuevos formatos.
5. Extender lo aprendido de cada excepción al resto de su familia y volver a probar los pendientes. Evitar soluciones por nombre cuando el formato común basta.
6. Distinguir bloqueo común del servicio de incompatibilidad individual. Si varios juegos fallan antes de apostar y un representante conocido tampoco arranca, interrumpir el barrido y registrar qué quedó sin probar. Los resultados anteriores no se convierten en aprobación de la nueva ejecución.
7. Publicar conteos, pendientes y limitaciones sin sesiones, firmas ni HAR completos.

## Aplicación inicial a KA Gaming

Catálogo local: 828 juegos, 60 con compras anunciadas. El formato pos=[1], observado en cuatro HAR y completado en tres pruebas de protocolo, ahora se propone a los 60 juegos con compra, no solamente a los cuatro capturados. Las capturas específicas tienen prioridad sobre el candidato común.

El adaptador exige confirmar el inicio de compra y el cierre de sus juegos gratis. No declara todos los juegos aprobados por compartir formato ni asume que pos=[1] representa todas las opciones de precio de un juego.

Barrido intentado: BaWangBieJi, AliceInWonderland y Ares devolvieron HTTP404 en startGame. No se enviaron apuestas y no se pudo medir compatibilidad de compras. Quedaron 825 juegos sin recorrer en esa corrida. Las cuatro pruebas anteriores desde el adaptador también habían fallado en startGame; el representante de protocolo llegó a cerrar antes de aparecer los HTTP404.

El siguiente intento debe comprobar que el arranque responde y después retomar las compras y el catálogo. No hay reintento automático programado.
