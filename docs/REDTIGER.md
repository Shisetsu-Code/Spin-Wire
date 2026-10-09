# Red Tiger: compras y giros base

Una configuración del servidor puede anunciar capacidad de compra sin que el cliente del juego exponga esa función. Tratar esa capacidad como compra real producía conteos falsos y obligaciones pendientes en juegos sin compras accesibles.

`runtime.py` recoge evidencia del cliente; `execution.py` habilita compras sólo cuando están confirmadas (`client_observed=True`). Las opciones exclusivamente anunciadas quedan como `DISCOVERED_ONLY` y `SERVER_ADVERTISED`, sin ejecución automática. La cobertura de ramas excluye esos padres sin confirmar. Una bandera `hasFeatureBuy` aislada no crea una compra validada.

`base_state.py` clasifica respuestas por estructura. `hasState` por sí solo no demuestra bonus ni cierre. Se comprueban el modo, las acciones pendientes, las features y los componentes del estado. Se aceptan formas reconocidas de giro normal cerrado, incluidos estados persistentes normales demostrados; elecciones pendientes, free spins, respins y estados desconocidos impiden el cierre base.

Esta clasificación no contiene excepciones por nombre o ID de juego. Los fixtures y pruebas cubren tanto giros normales aceptados como estados incompletos rechazados. Véanse [detección](FEATURE_DETECTION.md) y [validación](VALIDATION.md).
