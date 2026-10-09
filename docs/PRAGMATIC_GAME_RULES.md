# Reglas por juego y aprendizaje por familias

El ciclo de depuración es: agrupar pendientes por estructura, observar una demo
representativa con el cliente oficial, corregir el handler común o asignar un
perfil, y repetir automáticamente la familia en Tester Spin. No se necesita una
investigación manual de cada título que comparte el mismo contrato.

`tester_spin/providers/pragmatic_game_rules.json` separa los datos de cada juego
del motor. `games` asigna el símbolo exacto del proveedor a un perfil de
`profiles`. Varios símbolos pueden reutilizar el mismo perfil. Un título que no
está registrado conserva la detección y los contratos existentes.

## Perfiles comprobados

| Perfil | Juegos asignados | Regla |
|---|---|---|
| `zeus_olympus` | `vs15godsofwar` | Petición de giro `l=15, ind=1`; la escala de apuesta de `doInit` sigue siendo 10. |
| `legacy_three_lines` | `cs3w`, `cs3irishcharms` | Tres líneas, escala 3, sin `bl/sInfo`; `gs=0` permite reconocer el cierre sin `na`. |
| `legacy_five_lines` | `cs5triple8gold` | Cinco líneas, escala 5, sin `bl/sInfo`; cierre legacy `gs=0`. |
| `scratchcard_ticket` | `scdiamond`, `scgoldrush`, `scqog`, `scwolfgold` | Comprar una tarjeta y continuar `play → end → collect → buy` con las acciones del cliente. |
| `extra_juicy_collect` | `vswaysxjuicy` | Continuación `doBonus(ind=1)` solo en los dos estados iniciales `bgt=35` observados. |

Cada perfil incluye `evidence`, que identifica la captura o los eventos reales
del cliente. Los HAR originales permanecen locales: pueden contener credenciales
temporales y no se incorporan al repositorio.

`fields` controla los parámetros de entrada; `omit_fields` elimina los que el
cliente de esa familia no envía; `stake_scale` describe el coste; `terminal`
reconoce el cierre; `continuations` relaciona estados con acciones. El informe
usa el mismo perfil que la ejecución, pasando el símbolo explícitamente. Los
errores del servidor tienen prioridad sobre cualquier perfil.

## Tarjetas y rondas gratuitas

La secuencia es `doBuy(tickets=1) → doPlay → doEnd → doCollect`. No basta con
observar `na=end`: todavía falta cerrar y cobrar. `doEnd` también puede devolver
`play` si se ganó otra tarjeta. Un `fs_left` positivo marca un evento gratuito y
reinicia la confirmación de rondas base consecutivas. Solo después de volver a
`buy` pueden iniciarse nuevas compras de prueba.

## Handlers estructurales compartidos

Las elecciones de `bgt=69`, las ruedas automáticas, las cuadrículas de picks y
las cascadas observadas reutilizan handlers estructurales. Se comprueba la
forma y el dominio publicados antes de elegir. Las ruedas automáticas no
reciben `ind`; una celda con estado positivo no puede volverse a elegir. El
bonus enhancer `be` preseleccionado por el servidor no cuenta como elección del
jugador.

La continuación mínima `bgid=0,bgt=69,end=0,rw=0.00`, con `rw_c=0`
opcional, usa el selector observado `ind=0`. La captura de Fury of Anubis
(`vs20wraanu`, HAR 2026-10-03T03-46-33-123Z) lo relaciona con el botón
COLLECT y con `na=s,fs=1,fsmax=10` posterior. Es evidencia del camino Collect;
no acredita Gamble. Los nombres de grupo `bg_0`, `bg`, `pc`, `pl` y `flat`
identifican namespaces de la misma firma candidata; la corrida de cada título
debe validar respuesta, cierre y regreso a base antes de aprobarlo. Campos como
`ask`, `ch_k`, `level` o `lifes` impiden usar esta continuación mínima.

Los menús segmentados relacionan `ask` con su tabla activa y envían solo
`ind`, la posición dentro de esa tabla. Kraken 2 aportó la muestra inicial.
Los valores de premio no se usan como índices y los menús etiquetados mantienen
su cobertura ordinal; no se combinan contratos distintos para eliminar pendientes.

La identidad de cobertura de una cuadrícula usa familia, tamaño y nivel, sin
crear una rama distinta por cada permutación del historial. Se conserva el
estado original en los artefactos para auditar cada acción.

La política `hidden-position-structural/v1` acredita la clase de selección de
posición oculta, no cada índice o premio posible. La fuente oficial usa el mismo
criterio `status<=0` y el mismo `doBonus(ind)` para esas posiciones. Cada muestra
requiere una posición disponible, respuesta válida, cierre y dos ciclos base.
El dominio real y el índice enviado permanecen en los artefactos. Familia,
tamaño, nivel y fuente siguen separados; el handler puede acreditarse desde
otro modo que llegue al mismo contrato. Cada modo de apuesta conserva su propia
prueba de ejecución y cierre. Las opciones etiquetadas siguen usando
`ordinal-options/v1`; un estado desconocido bloquea la aprobación.

En los informes estructurales, la opción `0` identifica la clase
`hidden_position`, no una instrucción de enviar `ind=0`. El contrato exportado
incluye la política, las etiquetas y el dominio real para conservar ese contexto.
Los artefactos ordinales históricos conservan su política original.

## Incorporar otro juego

1. Reutilizar un perfil cuando se comprueben los mismos parámetros, escala y
   estados. Registrar su símbolo exacto en `games`.
2. Si hay diferencias de datos, añadir un perfil acotado y su evidencia. No
   añadir una clase o un adaptador por título.
3. Añadir código compartido únicamente si aparece una transición nueva que los
   perfiles existentes no pueden expresar.
4. Repetir el grupo con sesiones demo independientes y concurrencia limitada.
   Revisar errores y cobertura; no aprobar un título solo por clasificarlo.

`OK` exige respuesta válida, cierre del modo, dos ciclos base consecutivos y la
cobertura requerida de las elecciones observadas. Una estructura desconocida
sigue en `PARCIAL`; una petición rechazada sigue siendo un fallo. Las pruebas
unitarias cubren perfiles, preservación de errores, alcance por símbolo y ciclos
de tarjetas. El empaquetado de escritorio incluye el JSON de reglas.
