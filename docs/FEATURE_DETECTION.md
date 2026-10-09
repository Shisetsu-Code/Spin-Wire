# Detección de funciones

## Tres preguntas independientes

1. ¿Existe una opción accesible de compra o antebet? Se requiere evidencia del contrato activo o del cliente, según el proveedor.
2. ¿Conocemos su solicitud? Deben estar demostrados acción, parámetros, tipos y dominio del selector.
3. ¿Se ejecutó y cerró? Una compra anunciada no es una compra validada.

`tester_spin/feature_summary.py` centraliza el resumen utilizado por la interfaz, los informes de revisión y la exportación. Cuenta opciones de entrada a compras; excluye spins normales, elecciones internas, cascadas, respins y continuaciones vinculadas a un modo de origen. Un `PURCHASE_BRANCH` aporta sus opciones requeridas distintas, no el número de respuestas recibidas.

## Evidencia por proveedor

| Proveedor | Tratamiento |
| --- | --- |
| Red Tiger | Sólo compras confirmadas por evidencia del cliente (`client_observed`). Una oferta exclusiva del servidor queda como descubrimiento, sin ejecución ni cobertura obligatoria automática. |
| 3 Oaks | Una compra observada en el cliente puede contarse aunque su formato todavía no sea ejecutable. La oferta del servidor sola no equivale a una compra visible. |
| Pragmatic | Se separan compras, antebets, selecciones de bonus y estados de continuación; los perfiles y las reglas estructurales se documentan por separado. |
| Belatra | El dominio activo de `vipOn` distingue antebet de compra; no depende del texto mostrado en la interfaz. |
| BGaming | `CHANCE` se trata como antebet cuando corresponde a esa modalidad, no como compra de bonus. |

`Sí` afirma presencia; `No` requiere evidencia suficiente de ausencia; `Sin datos` conserva la incertidumbre. Cuando hay compras confirmadas y otras sin confirmar, el resumen mantiene ambos hechos. No se deduce ausencia de funciones porque falló una descarga o una sesión.

## Cobertura e historial

`coverage_required` describe las obligaciones de la prueba actual. Un modo declarado opcional actualmente no vuelve a ser obligatorio por una ejecución histórica pendiente. El historial conserva la evidencia anterior sin imponerla al contrato nuevo.

Pragmatic agrupa posiciones de un selector oculto sólo cuando el contrato estructural demuestra equivalencia (`hidden-position-structural/v1`); guarda índice, firma y muestras de la selección. Esta equivalencia no se extiende a premios ni decisiones con efectos distintos.

## Añadir una primitiva

Documentar la acción y sus parámetros, la fuente activa que los produce, su dominio finito, las transiciones permitidas y el cierre de ronda. Añadir una regresión positiva y otra que rechace evidencia insuficiente. No usar el nombre del juego para habilitar rutas sin contrato. Si el formato cambia o aparecen alternativas incompatibles, conservar el pendiente y su causa.
