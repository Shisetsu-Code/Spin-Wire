# KA Gaming: resultados adicionales incluidos en una tirada

En la prueba manual de 3x Monos (ThreeMonkeys), la tirada 16 devolvió un bloque as con un resultado adicional completo. La respuesta mantuvo e=false, ec=0, fs=false, fsr=0, acb=0, rf=0 y mb=false. El cliente específico publicado presenta la secuencia ya incluida en esa respuesta; no necesita otra petición para obtener esos resultados.

El adaptador anterior consideraba todo as no vacío una continuación desconocida y detenía la prueba. Ahora reconoce únicamente el formato completo observado: asi, st, swi, snm, ssm, swm, sw, swu, fsw, sm y tw, con estructura y valores numéricos comprobados. Bloques incompletos, elecciones u otros formatos permanecen parciales. La validación de terminal también sigue exigiendo ausencia de juegos gratis y bonus activos.

Se verificó directamente la respuesta guardada: el nuevo adaptador la clasifica como terminal. No se enviaron nuevas apuestas para comprobar este caso. El historial original permanece intacto. La app ya abierta necesita reiniciarse para cargar el código actualizado.

La prueba de Abeja reina (BumbleBee) completó 32 giros y luego recibió HTTP404: ese resultado es un fallo de acceso, separado del bloque as de 3x Monos.

Pruebas específicas de ejecución y compras: 14 aprobadas. Revisión independiente sin hallazgos pendientes. La evidencia completa permanece en los datos locales de Tester Spin y no se publica con sesiones o identificadores efímeros.


## Actualización 2026-10-01

También se reconocen los formatos observados de AgentAngels (`asi, st, swm, sw, swu, fsw, tw`) y Ares (los anteriores más `sm`), con validación estructural y numérica. Las tiradas gratis naturales se continúan aunque el juego no tenga compras. Para resultados y limitaciones vigentes, consultar [KA_CURRENT_STATUS.md](KA_CURRENT_STATUS.md); el conteo de pruebas anterior corresponde al cambio original.
