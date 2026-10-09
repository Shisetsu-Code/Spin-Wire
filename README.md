# Tester-Spin

Aplicación de escritorio para cargar catálogos, probar demos y guardar evidencia de cada proveedor. El resumen informa compras, cantidad y antebets por juego y proveedor. Los giros normales y las continuaciones de bonus no se cuentan como compras.

## Ejecutar

En Windows, abrir `Abrir-Tester-Spin.cmd` desde el checkout. Prepara el entorno de desarrollo y abre la aplicación. Para un entorno ya instalado:

```powershell
.\.venv\Scripts\python.exe run.py
```

El ejecutable generado por `scripts/build-desktop.ps1` contiene una versión completa de la aplicación. Para incorporar cambios debe reconstruirse. El launcher generado por `scripts/build-launcher.ps1` usa un runtime actualizable: véase [autoactualización](docs/AUTOUPDATE.md).

## Interpretar resultados

- **OK**: las operaciones requeridas y su cobertura comprobada terminaron correctamente.
- **PARCIAL**: queda una operación, transición o cobertura requerida sin demostrar; revisar el diagnóstico.
- **ERROR**: la ejecución registró un fallo; se conserva su evidencia.
- **Compras/Antebets: Sin datos**: la evidencia disponible no permite afirmar presencia o ausencia.

Una bandera del servidor no basta para contar una compra ni convertirla automáticamente en una obligación pendiente. Existencia, capacidad de ejecución y validación son estados separados. [Reglas y ejemplos](docs/FEATURE_DETECTION.md).

## Documentación vigente

- [Operación, instalación, pruebas y compilación](docs/OPERATIONS.md)
- [Detección de compras y antebets](docs/FEATURE_DETECTION.md)
- [Contratos y cobertura de protocolos](docs/PROTOCOLS.md)
- [3 Oaks: primitivas y límites](docs/THREE_OAKS.md)
- [Red Tiger: evidencia y estado base](docs/REDTIGER.md)
- [Pragmatic: reglas y evidencia](docs/PRAGMATIC_GAME_RULES.md)
- [Validación y regresiones](docs/VALIDATION.md)
- [Diagnósticos por ejecución](docs/RUN_DIAGNOSTICS.md)
- [Arquitectura](docs/structural-map.md) y [adaptadores](tester_spin/providers/README.md)

Los documentos técnicos específicos de BGaming, Hacksaw, KA Gaming, RubyPlay, Spin4Win y Yggdrasil permanecen en `docs/`. Los archivos de resultados de catálogo son evidencia histórica, no certificación del catálogo actual. Los planes e informes de implementación sustituidos se retiraron; su historial sigue en Git.

## Desarrollo

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Las pruebas usan fixtures reducidos. Las capturas HAR completas, sesiones, datos locales y ejecutables generados no se publican en Git.
