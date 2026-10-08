# Ejecutar 3 Oaks localmente en Windows (sin GitHub Actions Runner)

Las pruebas de demos se ejecutan en la propia PC con Python y acceso a 3oaks.com.
No hace falta instalar WSL, Docker, WireGuard ni un runner self-hosted de GitHub.

## Descargar la rama con los contratos HAR corregidos

En PowerShell:

```powershell
cd C:\
git clone --single-branch --branch ci/three-oaks-complete-sweep https://github.com/Shisetsu-Code/Spin-Wire.git Spin-Wire-Local
cd C:\Spin-Wire-Local
```

No mezcles esta rama con una copia del programa ya compilada: el ejecutable instalado previamente no incorpora las nuevas correcciones.

## Fase 1: tres juegos de los HAR

```powershell
.\scripts\Run-3Oaks-Local.cmd smoke
```

Instala automáticamente dependencias en `.venv` (sin alterar el Python global).
Luego recorre **777 Fruity Coins**, **Lady Fortune** y **15 Dragon Pearls** una sola vez por sesión de demo. Cada juego recibe dos giros base y las compras serializadas que estén verificadas por el cliente; cuando un juego no tiene compras, la fase extra intenta 24 giros para capturar un bonus natural.

**Importante:** el programa usa el cliente HTTP de Tester-Spin, no la sesión ni las cookies del navegador HardFire. Aunque HardFire cargue el juego, una request Python podría obtener HTTP 403. Si eso ocurre, el programa detiene el recorrido y conserva la evidencia: no fuerza el acceso.

## Fase 2: catálogo completo

Cuando la fase de tres juegos funcione:

```powershell
.\scripts\Run-3Oaks-Local.cmd all
```

El ejecutor descarga un catálogo actualizado desde 3 Oaks, usa una sola sesión de demo por juego a la vez (sin abrir múltiples juegos simultáneos), prueba todos los giros base y compras demostradas y agrega muestreo de giros normales para juegos sin compras. Máximo: 90 minutos. Respetar posibles restricciones HTTP 403/429. Finalizar manualmente con Ctrl+C si hace falta.

**No es una enumeración de todos los resultados aleatorios** ni valida por sí mismo un antebet independiente que aún no se encuentre implementado en el adaptador.

## Resultados

- Resumen legible y sanitizado: `test-evidence\3oaks-local\summary.json`.
- Por juego: `test-evidence\3oaks-local\games\<slug>\base-and-purchases.json` y `*-wire.json`.
- Evidencia original de las requests/respuestas, **con tokens y sesiones**, solo local: `data\three-oaks-full-sweep\providers\3oaks\`.

La carpeta `data/` y `test-evidence/` están excluidas de Git. **No publiques los archivos originales de sesión**. Para investigar la salida de un juego, compartir solamente el JSON sanitizado del juego y las transiciones wire.

Los códigos de salida son:
- `0`: todos los juegos seleccionados terminados y sin cobertura obligatoria pendiente;
- `2`: recorrido incompleto, p.ej. HTTP 403/429 o límite de tiempo;
- `3`: recorrido terminado con alguna operación pendiente (PARCIAL/ERROR).

El runner no se instala como servicio y termina cuando se cierra el comando.
