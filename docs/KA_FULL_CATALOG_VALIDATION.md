# KA Gaming: barrido completo de 828 juegos

Corrida del 30/09/2026 solicitada sobre todos los juegos del catálogo local, incluidos los que no anuncian compras. Se usó el mismo adaptador RMP para los 828 juegos, con una sesión nueva por juego y cuatro juegos independientes en paralelo. El giro base previsto fue uno por juego; la compra pos=[1] estaba propuesta para los 60 juegos que la anuncian.

| Medida | Resultado |
|---|---:|
| Juegos con intento registrado | 828 |
| Con compras anunciadas | 60 |
| Sin compras anunciadas | 768 |
| HTTP404 en startGame | 828 |
| Giros base ejecutados correctamente | 0 |
| Compras ejecutadas correctamente | 0 |
| Juegos sin intentar en esta corrida | 0 |

El error ocurrió en POST https://rmpdemo.kaga88.com/kaga/rmp/startGame, antes de enviar apuestas. **Este barrido no permite decidir qué juegos son compatibles con el formato de giro o compra.** Los 828 errores son fallos de arranque; no demuestran 828 formatos incompatibles. La causa de los HTTP404 sigue sin determinarse.

El barrido anterior se había interrumpido tras tres HTTP404. Por pedido explícito posterior del usuario, esta corrida continuó hasta intentar todo el catálogo. Tester Spin conserva ambos historiales y las respuestas completas localmente.

Siguiente paso: comprobar y corregir o restablecer el arranque común con un representante conocido antes de repetir apuestas. Después volver a medir giro base, compras y continuaciones por juego. Las tres pruebas de protocolo anteriores que cerraron compras se conservan como evidencia histórica, sin convertir esta corrida en OK.

Los listados JSON y CSV contienen resultados resumidos sin sesiones ni firmas. Se verificaron 828 identificadores únicos y la coincidencia de conteos. El barrido no cambió el código del adaptador.
