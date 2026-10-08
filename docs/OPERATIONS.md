# Operación y desarrollo

## Aplicación

Abrir `Abrir-Tester-Spin.cmd` desde el checkout para preparar y ejecutar el entorno de desarrollo. Con el entorno preparado, ejecutar `.\.venv\Scripts\python.exe run.py`. Seleccionar proveedor, cargar catálogo y probar juegos; usar el detalle y Árbol y diagnóstico para investigar resultados pendientes.

Compras, cantidad y antebets se resumen por juego y proveedor. `Sin datos` conserva incertidumbre; PARCIAL identifica cobertura o ejecución aún sin demostrar. [Interpretación](FEATURE_DETECTION.md).

Los datos persisten bajo `data/` o la ruta configurada. No borrar el historial para ocultar un pendiente: revisar su operación, parámetros, respuesta y razón. La evidencia local por ejecución permite contrastar resultados del programa con capturas manuales.

## Instalar y probar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest tests -q
```

## Compilar

```powershell
.\scripts\build-desktop.ps1
```

Genera la aplicación completa con los registros y recursos del proveedor incluidos. Recompilar después de cambiar el código o sus recursos; copiar el ejecutable resultante sólo después de comprobar el arranque.

Para un launcher con runtime actualizable, usar `scripts/build-launcher.ps1 -Clean`; revisar [configuración de actualización](AUTOUPDATE.md). La rama configurada determina qué código instala el launcher.

## Investigar un PARCIAL

1. Abrir [diagnósticos](RUN_DIAGNOSTICS.md) de la última prueba y localizar el primer pendiente.
2. Separar giro base, compra, antebet y continuación; verificar qué evidencia activa originó cada obligación.
3. Contrastar HAR y cliente de la misma versión, sin reutilizar credenciales ni rondas consumidas.
4. Extraer un fixture mínimo sin sesiones y una regresión para la primitiva, incluyendo un caso que debe quedar pendiente.
5. Repetir pruebas locales y, cuando corresponda, una demo nueva; registrar cierre y regreso al estado base.

La red caída o un cliente no descargado no prueban ausencia de compras. Un resultado OK de una muestra tampoco certifica el catálogo entero.

## Publicación

Publicar código, documentación y fixtures reducidos. Mantener fuera de Git `data/`, HAR completos, credenciales, ejecutables y copias locales. Los resultados de ejecución tienen un canal separado: [publicación de resultados](RUN_RESULTS_PUBLISHING.md).

## 3 Oaks: acceso de demo

El catálogo y el lanzador pueden responder correctamente mientras el login HTTP recibe un desafío de Cloudflare. El adaptador reconoce ese caso por su respuesta HTML y usa fetch desde Edge instalado o Chromium de Playwright, con una sesión nueva. No es un reintento de compras. Si no hay navegador disponible, instalar Chromium con el procedimiento de desarrollo anterior o disponer de Edge. Revisar `*.transport.json` y el HTML bloqueado del login en la evidencia local.
