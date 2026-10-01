# 3 Oaks Gaming en Tester Spin

Integración del 30 de septiembre de 2026: proveedor disponible en el selector y la cola de reintentos, con catálogo completo de 110 juegos y 110 miniaturas guardadas.

Se consultó MultiPlay como referencia. Sus capturas históricas no demuestran el protocolo actual: `/api/v1/games/<slug>/play` entrega el lanzador HTML. El transporte actual observado utiliza POST con JSON como `text/plain` al servidor de demo y parámetro `gsc=login`, `start` o `play`. El adaptador guarda solicitudes y respuestas locales por intento, conserva los selectores de compra al exportar y sólo valida rondas con cierre explícito.

| Familia de cliente | Juegos |
| --- | ---: |
| goreel | 65 |
| kendoo | 20 |
| ratpack | 13 |
| hraymo | 10 |
| enjoy | 2 |

Esta clasificación viene de los clientes publicados; no implica cinco formatos de compra validados. Se tomó un representante por familia, sin abrir todas las demos.

En **3 SuperPower Diamonds** el arranque real anuncia `spin`, `buy_spin` y dos compras: `selected_mode=1` a x100 y `selected_mode=2` a x300. El cliente publicado serializa la compra dentro de `action.params.selected_mode`. Se registraron como candidatos, sin marcarlas como compras verificadas ni extenderlas automáticamente a otros juegos.

Login y arranque HTTP funcionaron. El giro HTTP devolvió `SERVER_ERROR`; los intentos posteriores recibieron HTTP403. Un giro normal sí completó visualmente en el navegador. Se deja la ejecución remota pendiente, conforme al alcance de aproximación gruesa acordado. El adaptador no adivina continuaciones de bonus.

Las credenciales de demo y sesiones quedan únicamente en evidencia local, fuera del inventario reutilizable. Fuentes: [catálogo oficial](https://3oaks.com/games) y su API pública. El inventario adjunto contiene los juegos, sus familias y los candidatos observados.
