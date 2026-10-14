# Mecánica particular

La grilla incluye una columna común, ordenable y de ancho ajustable: **Mecánica particular**.

- **Sí — …**: elecciones declaradas por respuestas del servidor, dominios de selección observados o escaleras de decisiones comprobadas por el ejecutor.
- **Indicio — …**: progreso o símbolos bloqueados observados; un campo aislado no prueba un acumulador ni su persistencia entre rondas.
- **Sin datos**: no hay evidencia reconocida. No significa que el juego no tenga mecánicas especiales.

Las compras, antebets, giros normales y multiplicadores aislados no activan esta marca. Tampoco los selectores de apuesta de Belatra. No se consultan nombres ni IDs de juegos para clasificar.

La marca conserva evidencia histórica: puede describir una mecánica vista en una prueba anterior aunque la última corrida breve no la active. No modifica el estado OK/PARCIAL ni las cantidades de compras o antebets.

Al abrir la aplicación se revisan los metadatos históricos en segundo plano y hasta 80 archivos JSON de respuestas/resúmenes por corrida histórica, de hasta 512 KB cada uno. Los HAR completos y archivos mayores no se recorren automáticamente. El índice local evita volver a leer las corridas ya revisadas. Las pruebas nuevas guardan la clasificación en el resultado. No se envían capturas a servidores.

## Contrato para adaptadores actuales y futuros

`mechanics` usa `schema: tester-spin/mechanics/v1` e `items` con `id`, `label`, `status` (`confirmed` o `indication`) y `source` con evidencia. Un adaptador puede declarar un acumulador confirmado únicamente cuando haya contrastado su configuración y evolución, incluyendo persistencia o reinicio cuando corresponda. Las formas de protocolo desconocidas permanecen Sin datos hasta agregar una primitiva sustentada por evidencia.

La clasificación se realiza en `tester_spin/mechanics.py`, compartida por todos los proveedores. Las exploraciones locales están limitadas por tamaño, profundidad y cantidad de nodos. El historial no se reescribe ni se borra.
