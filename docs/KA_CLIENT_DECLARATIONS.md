# KA Gaming: dominio declarado por el cliente

Actualización: 2026-10-11. Fuente: HAR de Jade Quest, Kick Cash Monkey 2 y Bonus Vending, cliente común 2071 y scripts específicos cargados desde el launcher demo oficial.

## Autoridad de opciones

La primitiva interpreta el descriptor registrado para el símbolo del juego y la herencia del cliente común. No utiliza títulos, listas de juegos ni el número de compras ejecutadas en un HAR.

También admite el descriptor con nombre que encabeza el script, se construye
inmediatamente sin argumentos y usa el constructor reconocido que registra el
símbolo cuando el argumento es `undefined`. Una declaración dentro de una función
o condición, una reasignación intermedia o un constructor desconocido no acredita
ausencia. Se mantienen las mismas comprobaciones de herencia y controladores.

En el contrato reconocido, `oda` controla la oferta del botón; el default heredado es false. Los dos clientes con compra usan una condición sobre promoción y `dbf` de startGame. `dbf` se interpreta solo cuando se demuestra su recorrido hacia la condición del cliente; un campo ausente o de otro tipo no se adivina.

La factory efectiva `Oia`, el controlador `Ya`, el precio `Xqa` y la ruta del botón deben tener formas reconocidas. La ruta común envía `Ab.kW(...,[1],...)`, que el serializador transforma en `pos:[1]`. Esto acredita una opción para ese contrato de cliente. No permite asignar una compra a todos los juegos del proveedor: un menú, controlador o selector distinto queda pendiente.

El descriptor de Bonus Vending no sustituye la bandera false de la base reconocida; su dominio de compras es completo y vacío. La ausencia de un override solo vale si se certifican la base y el descriptor correcto. Los métodos con cuerpos desconocidos siguen registrados como overrides; no se confunden con herencia.

## Ejecución y cobertura

Se descarga el script específico de la versión actual antes de crear la sesión; `startGame` aporta la configuración efectiva. Las opciones declaradas sustituyen el conteo de candidatos del catálogo y se guardan en `feature_domains`. Los fallos de descarga, cambios de sintaxis o de factory/controlador producen dominio incompleto y PARCIAL, incluso si el giro normal termina.

La compra se inicia una sola vez con `pos:[1]`. Las continuaciones omiten `pos`; se siguen las free games reconocidas hasta el retorno al estado normal. El inicio debe estar aceptado por el servidor con `pos:[1]`, `acb=1` y free games pendientes. No se acepta como cierre una ronda con decisiones o estados desconocidos.

Antebet: el contrato base reconocido declara `t$a=false`. Un descriptor sin override permite acreditar ausencia para esa familia; cualquier override todavía no interpretado conserva el dominio antebet incompleto. No se inventan selectores `atb`.

## Casos de referencia

| Juego | Compras declaradas | Multiplicador en cliente |
|---|---:|---:|
| Jade Quest | 1 | 80 |
| Kick Cash Monkey 2 | 1 | 80 |
| Bonus Vending | 0 | — |

Los nombres son ejemplos de prueba, no reglas del programa. Las capturas de compra muestran una petición inicial y las continuaciones hasta retorno al giro normal. Los resultados anteriores deben repetirse para obtener la nueva declaración.

## Pruebas

`tests/fixtures/ka_oct11_declarations.json` conserva descriptores públicos y estados necesarios de los tres HAR. Excluye usuarios, sesiones, firma del cliente, saldos y tokens. Los IDs auxiliares de pantallas se sustituyen por valores locales de prueba.

`tests/test_ka_client_declarations.py` comprueba declaración sin compras capturadas, ausencia por herencia, configuración desconocida, símbolo equivocado, desactivación del servidor, precio no reconocido, overrides anidados/no funcionales, factories distintas y separación de descriptores. También reproduce las rondas capturadas con el ejecutor y verifica que no se vuelve a comprar en las continuaciones. Son pruebas locales, no apuestas reales ni una certificación de todos los juegos KA.

Validación completa: 1139 pruebas y 221 subtests correctos. Tres advertencias preexistentes de BeautifulSoup en el catálogo Pragmatic.


## Transporte HTTP y retorno al giro normal

El User-Agent y el contexto firmado describen el mismo cliente Windows. La
versión Chrome se toma del perfil del transporte instalado o de un User-Agent
Windows explícito; no se fija a la versión de un HAR. Las credenciales y las
identidades se generan para cada sesión nueva.

La comparación controlada de arranques mostró 404 con el User-Agent anterior y
200 con el User-Agent Windows; cambiar solo los campos de dispositivo no resolvía
el 404. Se conservaron la firma, el protocolo y el juego de la prueba. Esto
separa un rechazo del transporte de un selector de juego desconocido.

Cada muestra exige, además del cierre de la ronda, dos giros base confirmados con
la apuesta normal original. Un bonus natural se recorre solamente mediante la
continuación demostrada y reinicia esa comprobación. Los estados desconocidos no
cuentan como regreso al base. La cuota configurada se aplica también a las compras.

El descriptor anónimo puede empezar con metadatos antes del constructor. Se leen los métodos del objeto exterior y se verifica el constructor registrado y la construcción inmediata; el orden de las propiedades no determina la disponibilidad. Cada respuesta de ejecución y continuación debe conservar `sel/cps/atb/dn` de la petición enviada. Un cambio inesperado mantiene el resultado pendiente, aunque después existan giros normales.
