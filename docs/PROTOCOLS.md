# Protocolos y cobertura

Cada adaptador descubre entradas, ejecuta acciones demostradas y conserva respuestas originales. La interfaz y la base de datos no inventan solicitudes específicas del proveedor. `ProviderAdapter.finalize_test_result()` aplica el control común de cobertura y genera `path-coverage.json`.

## Entrada frente a continuación

Una compra es una entrada pagada distinta; un antebet modifica el giro base. Free spins, respins, cascadas y elecciones internas continúan una ronda y no incrementan el número de compras. Opciones aleatorias y elecciones explícitas pueden requerir cobertura, pero no son nuevas compras.

Cada modo registra evidencia, posibilidad de ejecución, opciones requeridas y cubiertas, origen y muestras. Las banderas generales de servidor no se convierten automáticamente en obligaciones actuales. La cobertura histórica conserva trazabilidad y respeta los modos actualmente opcionales.

## Cierre

Una respuesta HTTP correcta no prueba cierre de ronda. El adaptador debe comprobar el estado terminal del protocolo y realizar las comprobaciones de retorno requeridas. No se inventan acciones ante estados desconocidos. Límites de tiempo, pasos o expansión dejan cobertura pendiente.

Las decisiones consumibles requieren rondas nuevas para recorrer alternativas. La equivalencia estructural sólo reduce posiciones cuando el contrato demuestra que representan la misma operación; conserva la selección observada y no equipara premios diferentes.

## Referencias activas

- [Detección compartida](FEATURE_DETECTION.md)
- [Pragmatic](PRAGMATIC_GAME_RULES.md): perfiles observados, bonus, selección y recolección.
- [3 Oaks](THREE_OAKS.md): primitivas estáticas, dominios de compra y cierre explícito.
- [Red Tiger](REDTIGER.md): confirmación del cliente y clasificación del estado base.
- [BGaming](BGAMING_EMULATION_CONTRACT.md), [capturas](BGAMING_HAR_CAPTURE.md).
- [Hacksaw](HACKSAW.md), [elecciones](VALIDATION.md).
- [KA Gaming](KA_CURRENT_STATUS.md), [Spin4Win](ONE_SPIN4WIN_PURCHASES.md).
- [RubyPlay](RUBYPLAY.md), [Yggdrasil](YGGDRASIL.md).
- [Cobertura de caminos](EXHAUSTIVE_PATH_COVERAGE.md), [aprendizaje de protocolo](SAMPLING_AND_PROTOCOL_LEARNING.md).

Los resultados de catálogo conservados en JSON/CSV son muestras históricas. No prueban cobertura de versiones posteriores de los clientes.
