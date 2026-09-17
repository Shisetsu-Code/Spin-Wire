# Compras y activaciones BGaming

Las compras no tienen que abrir un evento. Una respuesta cerrada también puede ser válida; se conserva el débito observado (saldo anterior menos saldo posterior más premio), la petición y la respuesta para comprobarlo.

- API v2 prueba valores escalares de compra anunciados por el servidor usando el contrato purchased_feature. No inventa nombres ni niveles.
- El cliente oficial confirma play_bonus_game sin parámetros. Solo se ejecuta cuando el servidor lo anuncia en un estado compatible.
- Si purchased_feature sigue activo, las tiradas no cuentan como confirmaciones del juego base. Se requieren dos tiradas normales exitosas, dentro del límite de diez comprobaciones; si no se logra, queda pendiente.
- Tras un rechazo HTTP 400/422 de una compra, se consulta init en la misma sesión. Solo se prueban tiradas normales si el servidor las permite; la compra rechazada sigue marcada como fallida.
- Las colecciones explícitas de resultados internos se registran por ruta y cantidad. Las pantallas de animación se cuentan por separado, sin sumarlas como apuestas adicionales. Una respuesta cerrada no basta para decidir si hubo un modificador o un bonus completo dentro de la respuesta.

## Validación breve con saldo ficticio

El 17 de septiembre de 2026: Adventures completó la tirada normal y tres compras (4/4), incluyendo play_bonus_game. Alien Fruits 3 completó tirada normal, bonus y chance (3/3). Cada intento confirmó dos tiradas normales al finalizar. Se utilizó una configuración de apuesta aceptada; no se probaron todas las combinaciones de líneas.

Los resultados y peticiones están en data/providers/bgaming/<juego>/tests. La prueba no demuestra que todos los juegos o combinaciones del proveedor estén cubiertos.
