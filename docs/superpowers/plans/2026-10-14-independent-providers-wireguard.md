# Ejecución independiente por proveedor y lotes WireGuard

Objetivo: ejecutar cualquier proveedor desde Windows o GitHub Actions usando el
mismo catálogo, primitivas, cobertura y pruebas monetarias que Tester-Spin.

## Diseño

- Registro de proveedores con carga diferida: seleccionar uno no carga los otros.
- CLI independiente: listar proveedores, actualizar catálogo y ejecutar pruebas.
  Raíz de datos explícita, límite total, desplazamiento, estados y muestras.
- Cada juego corre en un proceso con plazo; conserva los finalizadores comunes.
- WireGuard opcional mediante archivos locales .conf. Cantidad por IP obligatoria
  si se usa VPN; perfiles con la misma salida comparten cuota dentro de la corrida.
- Un túnel administrado por vez por equipo, sin modificar túneles ajenos. Validar
  conexión/salida antes de ejecutar; no comenzar nuevas apuestas sin VPN solicitada.
  Cambiar perfil entre juegos. Los intentos fallidos también consumen cuota.
- Un 429 detiene la corrida; no se rota de IP en respuesta al bloqueo.
- Reporte público reducido; HAR, sesiones y configuraciones permanecen locales.
- Workflow manual de GitHub: proveedor, cantidad, desplazamiento, cuota por IP;
  configuraciones en Secret, limpieza al terminar, resumen descargable sin sesiones.
- La validación real de VPN depende de configuraciones suministradas por el usuario.

## Plan de implementación

1. Pruebas de carga independiente; registro diferido compatible con la GUI y
   PyInstaller. Sustituir construcción de todos los adaptadores en la cola antigua.
2. Pruebas de cuotas y vida del túnel; gestor WireGuard para Windows/Linux, mutex,
   verificación de salida, perfiles privados y limpieza de recursos propios.
3. Pruebas de cola/finalización/cancelación; CLI, procesos, límites y resumen.
4. Empaquetado Python, lanzador local y workflow manual; comprobar comandos,
   esquema y ausencia de secretos en artefactos publicados.
5. Pruebas del resto del repositorio, revisión de código, documentación y GitHub.

Ejecución nativa en esta conversación según la autorización previa de trabajo
autónomo. No se activará una VPN real hasta recibir sus perfiles.

## Registro de ejecución

- Registro diferido: pruebas rojas y verdes; ya no carga ni crea proveedores ajenos.
- VPN y cuotas: pruebas rojas y verdes, sin activar perfiles reales todavía.
- CLI y paquete: instalación verificada; prueba real de Airport Security terminada OK.
- Workflow: manual, dependencias por proveedor y reporte allowlisted.
- Ruling: usar Job Objects/cgroup v2, no solo terminar el padre Python; Playwright
  puede dejar descendientes separados. Un fallo de cierre es fatal y conserva VPN.
- Ruling: rechazar Table=off/tablas alternativas y hooks; una conexión con handshake
  no demuestra que el tráfico use rutas de VPN.
- Pendiente externo: carpeta de perfiles reales y cantidad por IP de la consulta al usuario.
