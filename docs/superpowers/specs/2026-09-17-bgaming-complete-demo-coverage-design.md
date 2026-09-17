# BGaming Complete Demo Coverage Design

## Objetivo

Llevar el catálogo BGaming con demo resoluble a un estado en el que cada juego pueda clasificarse correctamente como `OK`, `PARCIAL`, `ERROR` o `SIN_DEMO`, y donde `OK` signifique que todas las rutas de interacción que el runtime de ese juego realmente expone quedaron demostradas hasta un estado terminal/base conocido.

La cobertura es **capability-driven**. No existe una lista universal de compras, ante bets, chances, gambles o elecciones que todos los juegos deban tener. La ausencia de una capacidad es válida cuando el runtime no aporta evidencia positiva de que esa capacidad exista para ese juego.

El objetivo final de esta fase es comprender la superficie de interacción de todos los juegos BGaming con demo para poder producir contratos estables que un crawler/farm futuro pueda ejecutar sin redescubrir la lógica del juego.

## Alcance

Esta fase trabaja únicamente sobre BGaming.

El catálogo actual ya tiene una mayoría de juegos en `OK`; por lo tanto, el trabajo principal es:

1. ejecutar un barrido completo para identificar los pocos `PARCIAL`/`ERROR` restantes;
2. separar falsos parciales causados por capacidades inexistentes de fallos reales de protocolo;
3. agrupar fallos reales por familia/firma estructural;
4. analizar uno o pocos representantes por grupo;
5. corregir reglas genéricas del protocolo;
6. volver a probar el grupo afectado;
7. repetir hasta que todos los juegos con demo queden `OK` o exista una excepción explícita y justificada;
8. ejecutar un barrido completo final de regresión.

## No objetivos

Spin-Wire no debe convertirse en un sistema de aprendizaje autónomo ni en un analizador heurístico general de juegos.

No se implementa:

- OCR;
- análisis de canvas/WebGL;
- click discovery visual general;
- navegación UI como mecanismo normal de clasificación;
- reglas por nombre de juego para resolver casos normales;
- un DSL universal de requests;
- lógica que suponga que todos los juegos tienen `PURCHASE`, `ANTE`, `CHANCE`, `GAMBLE` u otra capacidad opcional.

La interpretación de resultados, comparación de artifacts/HAR y diseño de nuevas reglas de protocolo se realiza externamente durante la depuración. Spin-Wire sólo recopila evidencia, ejecuta contratos que comprende y falla cerrado cuando no tiene evidencia suficiente.

## Definición de cobertura

"Todas las tiradas posibles" significa todas las rutas de interacción/wire distintas que el jugador puede provocar y que el runtime del juego demuestra como disponibles.

Ejemplos:

- spin base;
- ante bet;
- chance/feature chance;
- cada compra;
- cada nivel o variante de compra;
- respins;
- free spins;
- collect;
- gamble;
- picks;
- elecciones dentro de una compra;
- elecciones secuenciales o anidadas;
- continuaciones requeridas por el estado del servidor;
- cualquier rama que deba recorrerse antes de volver a terminal/base.

No significa enumerar todos los resultados RNG posibles de una misma ruta.

## Regla fundamental de `OK`

Un juego puede quedar `OK` cuando se cumplen simultáneamente estas condiciones:

1. existe una demo válida/resoluble;
2. el spin base fue ejecutado y validado contra el servidor;
3. todas las capacidades con evidencia positiva de disponibilidad para ese runtime fueron ejecutadas;
4. todas las ramas obligatorias observadas dentro de esas capacidades fueron cubiertas;
5. cada ejecución llega a terminal/base o a una transición comprendida que finalmente llega a terminal/base;
6. no quedan ramas requeridas sin cubrir;
7. no quedan errores de wire o estados desconocidos que formen parte de una ruta disponible;
8. el resultado no depende de inferir una capacidad ausente.

Un juego sin compras puede ser `OK`. Un juego sin ante bet puede ser `OK`. La inexistencia de una capacidad opcional nunca constituye por sí sola cobertura faltante.

## Evidencia de capacidades

Las capacidades se clasifican por fuerza de evidencia.

### Evidencia fuerte: capacidad requerida

Una capacidad pasa a `coverage_required=true` cuando existe evidencia positiva vinculada al runtime actual del juego, por ejemplo:

- metadata/bootstrap del juego que anuncia explícitamente esa capacidad;
- respuesta del servidor que publica una opción ejecutable;
- serializer del cliente cargado por ese runtime donde la capacidad forma parte del request real;
- HAR con request/response de esa operación;
- menú/configuración de runtime que se correlaciona inequívocamente con el wire ejecutable;
- estado del servidor que exige una continuación o elección concreta.

### Evidencia débil: diagnóstico solamente

No bloquean `OK` por sí solos:

- un string suelto en un bundle;
- enums compartidos por múltiples juegos;
- código genérico del engine sin correlación con el runtime actual;
- nombres conocidos de features encontrados fuera del serializer efectivo;
- ramas muertas/no alcanzables;
- vocabulario de una capacidad sin request demostrable.

Estos casos se representan como `DISCOVERED_ONLY`, `DISCOVERED_LITERAL_ONLY` o estado equivalente y deben llevar `coverage_required=false`.

### Evidencia desconocida

Si existe indicio de una capacidad pero no se puede decidir si está disponible para el juego, el sistema debe fallar cerrado de forma diagnóstica. No debe inventar un request ni marcar automáticamente una compra como obligatoria.

## Separación entre discovery y ejecución

Cada modo descubierto conserva como mínimo:

- `id`;
- `kind`;
- `source`;
- `discovery_state`;
- `executable`;
- `coverage_required`;
- request/options estables cuando exista evidencia suficiente;
- evidencia estructural sanitizada necesaria para diagnóstico.

`executable=true` significa que existe un contrato de wire suficiente para intentarlo.

`coverage_required=true` significa que el runtime actual demostró que esa ruta forma parte de la superficie del juego y debe validarse antes de permitir `OK`.

Estos conceptos no son equivalentes. Puede existir información útil para diagnóstico que no sea ejecutable ni obligatoria.

## Barrido completo BGaming

Se añadirá un modo de ejecución de catálogo completo reutilizando el adaptador BGaming real.

El barrido:

1. obtiene el catálogo autoritativo;
2. resuelve únicamente juegos con demo;
3. ejecuta juegos con concurrencia limitada;
4. usa un único runner y un único túnel Proton por corrida;
5. usa inicialmente concurrencia 3-4 para evitar conflictos de sesión/red y limitar carga;
6. conserva los resultados por juego;
7. genera un resumen global sanitizado;
8. no intenta corregir ni aprender reglas automáticamente.

La concurrencia ocurre dentro del runner. No se deben levantar múltiples peers simultáneos usando la misma configuración WireGuard.

## Resultado global del barrido

El reporte global debe permitir separar al menos:

- `OK`;
- `PARCIAL_CAPABILITY_FALSE_POSITIVE`: una capacidad débil fue interpretada como obligatoria;
- `PARCIAL_BRANCH`: existe una rama demostrada sin cubrir;
- `ERROR_PROTOCOL`: servidor rechazó el wire o apareció un contrato desconocido;
- `ERROR_DEMO`: demo/resolución/bootstrap no disponible;
- `ERROR_INFRA`: red, Proton, runner o dependencia;
- `SIN_DEMO`.

El programa no necesita realizar una clasificación inteligente compleja. Debe exportar datos suficientes para que el diagnóstico externo pueda agrupar resultados por causa.

## Cohortes de depuración

La depuración se hará por cohortes, no por títulos individuales.

Las dimensiones útiles son:

- familia de runtime (`api-v2`, `hyperhive-jsonrpc`, `legacy-lines`, `switchable-container`, etc.);
- firma estructural del request/serializer;
- modos/capacidades realmente anunciados;
- código/error de servidor;
- estado de cobertura;
- firma de transición/continuación.

El agrupamiento puede realizarse fuera de Spin-Wire a partir del resumen y artifacts. Spin-Wire no necesita implementar clustering ni heurísticas complejas.

Cuando varios juegos presentan la misma causa, se corrige una regla genérica y se vuelve a ejecutar el cohort completo.

## Política de HAR

Los HAR se usan como evidencia de diagnóstico, no como base obligatoria del core.

Orden de uso:

1. runtime/bootstrap/responses directamente observables;
2. scripts/serializer cargados por el runtime;
3. HAR automático si contiene operaciones útiles;
4. HAR descargado/manual para casos que sigan ambiguos.

Para un juego `PARCIAL` o `ERROR` que no pueda resolverse con artifacts sanitizados, se puede descargar su HAR y analizarlo fuera del flujo normal. La corrección resultante debe generalizarse a una familia/firma cuando sea razonable.

El HAR no debe incorporarse al repo si contiene tokens, cookies, session URLs u otros datos efímeros/sensibles.

## Excepciones por juego

Se permiten excepciones hardcodeadas sólo cuando:

1. el comportamiento es realmente excepcional;
2. no existe una generalización razonable que describa otros juegos;
3. el caso está demostrado con evidencia de runtime/HAR;
4. la excepción queda aislada del parser genérico;
5. incluye test de regresión;
6. documenta por qué existe.

Las excepciones deben vivir en una capa pequeña y explícita, preferentemente declarativa, separada de las reglas normales de BGaming.

Un ejemplo válido es un juego con una secuencia de elecciones interna única dentro de una compra cuando el servidor no expone un contrato general reutilizable.

Un ejemplo inválido es agregar `if game_name == ...` para corregir una estructura que en realidad pertenece a una familia de serializer compartida.

## Relación con `farm-contract.json`

Este diseño complementa `2026-09-14-discovery-contract-design.md`.

Cuando un juego BGaming queda realmente `OK`:

- sus modos requeridos están demostrados;
- sus elecciones obligatorias están cubiertas;
- no existen capacidades inventadas;
- `farm-contract.json` puede representar la superficie validada del juego;
- el crawler/farm futuro debe poder consumir ese contrato sin redescubrir la GUI.

Un juego `PARCIAL` puede producir candidate para diagnóstico pero no debe promover un contrato incompleto como listo.

## Flujo operativo de depuración

```text
barrido completo BGaming
        ↓
separar OK de no-OK
        ↓
identificar falsos parciales por capability
        ↓
corregir gate/discovery genérico
        ↓
reprobar cohort afectado
        ↓
agrupar PARCIAL/ERROR reales por firma
        ↓
tomar 1-2 representantes
        ↓
analizar artifacts/HAR si hace falta
        ↓
crear regla genérica + test
        ↓
reprobar cohort
        ↓
repetir hasta agotar no-OK
        ↓
barrido completo final
```

## Testing

Cada corrección de protocolo debe seguir test-first.

Los tests deben cubrir al menos:

- capacidad ausente no bloquea `OK`;
- literal genérico de purchase no crea cobertura obligatoria;
- metadata/runtime que anuncia una compra sí la vuelve obligatoria;
- varias compras anunciadas requieren todas;
- elecciones internas observadas requieren cada opción;
- elecciones inexistentes no se inventan;
- un juego sin compras puede cerrar cobertura sólo con SPIN;
- reglas HyperHive no rompen API-v2 ni legacy-lines;
- una excepción declarativa sólo afecta al juego/contrato explícito;
- el barrido global no pierde resultados cuando un juego falla.

Además, después de cambios relevantes se deben ejecutar juegos de control de familias ya validadas para detectar regresiones cruzadas.

## Casos de control ya demostrados

Los siguientes títulos se usan como referencias de regresión, no como reglas por nombre:

- `Alien Fruits 3`: API-v2 con spin y compras/chance conocidas;
- `Adventures`: API-v2 con múltiples niveles de compra y continuaciones;
- `Multi Rush`: HyperHive JSON-RPC con serializer alias y bet_type condicional;
- `Elvis Frog in Vegas`: legacy-lines con apuesta por línea;
- `Aztec's Claw Wild Dice`: referencia de literal de compra que no debe convertirse automáticamente en capacidad ejecutable.

Estos títulos sirven para verificar familias que ya fueron observadas. El código genérico no debe depender de sus nombres.

## Seguridad y datos

GitHub Actions publica sólo evidencia sanitizada.

No se publican:

- cookies;
- tokens;
- claves WireGuard;
- authorization;
- CSRF;
- session URLs completas;
- HAR crudos;
- requests/responses con secretos.

Los HAR crudos permanecen temporales salvo descarga deliberada para análisis.

## Criterio de aceptación final

La fase BGaming se considera terminada cuando:

1. se ejecuta un barrido completo del catálogo actual;
2. todos los juegos con demo resoluble terminan `OK`, salvo una excepción explícitamente documentada como no automatizable con la evidencia disponible;
3. ningún juego queda `PARCIAL` sólo porque no tenga purchase/ante/chance/gamble;
4. toda capacidad marcada `coverage_required=true` tiene evidencia positiva vinculada al runtime de ese juego;
5. todas las ramas requeridas están cubiertas;
6. no quedan errores de protocolo agrupables sin investigar;
7. las excepciones por juego, si existen, son mínimas, aisladas y testeadas;
8. se ejecuta un barrido completo final después de la última corrección;
9. los casos de control de API-v2, HyperHive y legacy-lines siguen pasando;
10. los juegos `OK` pueden promover un `farm-contract.json` consistente con la superficie validada que consumirá el crawler futuro.
