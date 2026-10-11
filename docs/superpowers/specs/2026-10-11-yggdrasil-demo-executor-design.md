# Ejecutor Demo de Yggdrasil

## Objetivo y alcance

Hacer que Tester-Spin pruebe Yggdrasil de verdad, con primitivas por protocolo y sin excepciones por nombre o ID de juego. Reconocer compras, giros normales y continuaciones como categorías diferentes. Declarar OK solamente con evidencia de ejecución actual, cierre de ronda y retorno al giro normal. Los HAR enseñan formatos; su historial no acredita una prueba nueva.

El usuario aprobó este enfoque en el chat el 11 de octubre de 2026. Este documento describe el diseño para su revisión; el ejecutor todavía no está implementado.

## Evidencia y problema actual

El adaptador actual es pasivo: analiza capturas y devuelve PARCIAL siempre. No autentica una sesión ni ejecuta jugadas. Por eso corregir el parser por sí solo no convierte un juego en OK.

Las dos capturas aportadas muestran el mismo servicio Demo y configuración ApiVersion 2.6.0:

- 3 Piggies of Bank: cinco comandos BB distintos y cinco cobros C. No contiene un giro base capturado.
- 3 Gladiators vs Caesar: tres giros sin campo cmd, cuatro comandos BB distintos y cinco cobros C. La última ronda ordinaria permanece pendiente al terminar la captura.

El parser ya admite giros con cmd omitido y cobros sin coin. También diferencia el fin de la animación del cierre de la apuesta: clientData.isFinished no acredita una ronda cerrada. Un comando de continuación desconocido bloquea el cierre incluso cuando no puede normalizarse.

Una prueba exploratoria con sesión Demo recién creada confirmó authenticate, game y un giro ordinario del segundo juego. Todavía falta validar compras y cobros en sesiones nuevas. No se reutilizaron credenciales de los HAR.

## Enfoque elegido

Añadir un runtime específico de Yggdrasil e integrarlo en el adaptador existente. Mantener las estructuras GameTestResult, contratos de proveedor y verificación de retorno usadas por Tester-Spin. El descubrimiento pasivo permanece disponible para configuraciones o comandos que aún no tienen un ejecutor demostrado.

Analizar únicamente HAR conserva todos los PARCIAL. Reproducir literalmente sesiones históricas introduce credenciales vencidas y estados ajenos a la ejecución. La sesión Demo nueva permite verificar el comportamiento actual con evidencia independiente.

## Sesión y configuración

El runtime utiliza exclusivamente HTTPS y el host oficial demo.yggdrasilgaming.com, servicio /game.web/service, org=Demo. La identidad del juego procede de su página oficial y debe coincidir con las capturas asociadas. Un HAR aislado de otro juego no asigna automáticamente el ID.

Crear una identidad Demo nueva por prueba y obtener su token mediante authenticate. Consultar game con esa sesión y verificar el ID recibido. Token, identidad y wagerid se conservan solamente durante la ejecución; no se exportan en contratos, informes ni capturas compartibles. No hay autenticación de casinos ni uso de cuentas reales.

Extraer los modos, monedas y parámetros de apuesta de la configuración actual. Para una compra, exigir coincidencia entre el comando capturado y un modo del servidor. No convertir cualquier modo especial en compra: los BB capturados fundamentan la primitiva de compra; otros dominios requieren evidencia propia. Ausencia de antebet capturado no demuestra que el juego carezca de él.

## Parámetros de jugada

Normalizar plantillas con una lista explícita de campos permitidos: cmd, amount, coin y los parámetros de apuesta coins y lines cuando estén presentes y tengan formato válido. Descartar sesiones, tokens, clientinfo y datos auxiliares históricos.

No inventar multiplicadores a partir del nombre del modo ni trasladar precios entre juegos. Las capturas muestran que los formatos de apuesta pueden diferir: algunas compras tienen amount igual a coin; otras utilizan coinsPerBet. Cuando la configuración no basta para reconstruir el precio, conservar la plantilla capturada del mismo juego, contrastarla con los límites del servidor y validar el reconocimiento actual. Si no existe una plantilla compatible, ese modo queda pendiente.

El giro ordinario omite cmd. Solo habilitarlo para el contrato de API comprobado y parámetros fundamentados en captura o configuración actual. Una configuración desconocida queda PARCIAL; no se envía un giro adivinado.

## Ejecución y cierre

Cada jugada exige HTTP 200, code=0 y una estructura wager/bets válida. Verificar que la respuesta corresponde a la apuesta enviada, incluido comando e importe cuando el servidor los declara. Una respuesta ambigua no acredita cobertura.

Una ronda está cerrada cuando wager.status es Finished, existe al menos una apuesta, todas están RESULTED y no se anuncian comandos pendientes. El estado de animación nunca reemplaza estas condiciones.

Cuando el servidor anuncia únicamente C, ejecutar el cobro con amount=0, sin coin, wagerid de la respuesta actual y paso siguiente al mayor paso recibido. Derivar betid de la apuesta raíz comprobada; no fijar pasos por juego. Esto contempla que una respuesta incluya varias apuestas ya generadas por el servidor.

Comprobar continuidad de wagerid y progresión de pasos. No reintentar automáticamente una petición de pago cuyo resultado sea incierto. Una continuación desconocida, contradicción, falta de avance, límite de recorrido o cancelación detiene la ronda sin convertirla en OK.

## Retorno y resultados

Después de cerrar cada camino probado, utilizar la verificación existente para exigir dos ciclos consecutivos de giro normal completados. Una ronda que activa una característica no cuenta como ciclo ordinario; primero debe cerrarse y comprobarse nuevamente el estado base. No deducir estado base solo de Finished.

Registrar por separado giro, cada opción de compra y continuaciones. C no es compra ni antebet y no aumenta el número de compras. Un modo se acredita únicamente con ejecución actual reconocida, cierre y retorno confirmado. Cumplir las repeticiones solicitadas por modo.

OK exige cobertura completa de los dominios conocidos. Una compra anunciada sin plantilla ejecutable o un comando desconocido producen PARCIAL con motivo concreto. Los fallos de transporte o rechazos reales se distinguen de un dominio todavía no implementado. Los contratos listos deben describir el bootstrap y las primitivas realmente verificadas, sin reutilizar el contrato pasivo como si fuera ejecutable.

## Artefactos y documentación

Guardar resúmenes sanitizados de peticiones y respuestas, pasos, comandos anunciados y causa de detención. No guardar headers Authorization, tokens, identidades Demo, saldos ni respuestas crudas. Para correlacionar rondas en informes, usar una referencia local opaca en vez del wagerid original.

Documentar campos aceptados, contrato terminal, límites y comandos desconocidos. Asociar las capturas aportadas a sus juegos mediante evidencia oficial y conservar su análisis sanitizado. Actualizar el ejecutable que abre el acceso directo del escritorio al terminar; una aplicación abierta necesitará reiniciarse.

## Validación y aceptación

1. Pruebas de parser: cmd omitido, C sin coin, monedas inválidas, juego ajeno, duplicados y campos privados.
2. Pruebas de máquina de estados: apuestas múltiples en una respuesta, cobro anunciado, identidad inconsistente, paso detenido, comando desconocido y cancelación.
3. Pruebas negativas: animación terminada con ronda pendiente, HTTP fallido y Finished con una continuación sin resolver nunca acreditan cierre.
4. Pruebas de resultados: captura histórica no valida una ejecución actual; C no suma compras; una compra sin retorno no acredita cobertura.
5. Pruebas Demo nuevas para los dos juegos: ejecutar giro base y opciones fundamentadas, conservar trazas sanitizadas y describir cualquier bloqueo sin forzar OK.
6. Ejecutar la suite de regresión, construir el escritorio y comprobar el ejecutable instalado.

La aceptación exige que los caminos verificados puedan completar su ejecución y que los restantes tengan un motivo reproducible. No exige esconder como OK juegos cuyo protocolo todavía no se entiende.

## Fuera de alcance

No modificar otros proveedores ni agregar excepciones por título. El fallo de carga de Belatra observado antes de cambiar a Yggdrasil continúa pendiente y es independiente de este diseño.
