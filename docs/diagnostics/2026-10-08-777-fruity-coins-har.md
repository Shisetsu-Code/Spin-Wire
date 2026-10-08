# 3 Oaks: diagnóstico HAR de 777 Fruity Coins

Fuente: HAR demo aportado por el usuario, deliberadamente no publicado en el repositorio porque contiene identificadores dinámicos de sesión. Se cotejó con el JavaScript público del cliente conservado en evidencia de Actions.

Se observaron 63 requests POST y 63 respuestas HTTP 200: 5 sync, 4 spin, 4 buy_spin, 4 bonus_init, 42 respin y 4 bonus_stop.

## Contrato de compra

El servidor anuncia available_buy_bonus=[1,2,3,4] y buy_bonus_prices={"1":65,"2":200,"3":150,"4":400}. El cliente consulta el precio en buy_bonus_prices.[buyFeatureType+1] pero envía el enum buyFeatureType directamente como selected_mode.

| Índice anunciado | Multiplicador | selected_mode enviado |
|---|---:|---:|
| 1 | 65 | 0 |
| 2 | 200 | 1 |
| 3 | 150 | 2 |
| 4 | 400 | 3 |

El cuerpo de cada compra contiene command=play, action.name=buy_spin y action.params con bet_per_line=10, lines=5 y selected_mode numérico 0..3. El resto de valores del transporte incluyen campos dinámicos de sesión/tiempos que NO se incorporan a fixtures.

La conversión se implementa solo si el cliente contiene un enum finito, una llamada certificada desde la UI a BUY_SPIN, el getter real de precios con desplazamiento +1 y los precios/índices coinciden con la respuesta de start. Valores ambiguos no se envían.

## Continuaciones

El servidor anuncia consecutivamente bonus_init, respin y bonus_stop. Cada uno se envía mediante command=play, con action.params={} para las continuaciones. Las cuatro compras finalizaron: context.current=spins, round_finished=true y spin nuevamente ofrecido. Al terminar la cuarta compra, el cliente ejecutó dos giros normales.

El cliente activo contiene una sobreescritura literal de FLOW_ACTIONS.BONUS_STOP que devuelve bonus_stop, además de una llamada real al dispatcher. El adaptador solo manejaba la variante derivada bonus_spins_stop. La corrección admite bonus_stop exclusivamente cuando el código certifica el flujo y cuando el servidor la anuncia como única acción pendiente.

## Validación

Rama: fix/three-oaks-har-777.

Actions: https://github.com/Shisetsu-Code/Spin-Wire/actions/runs/37747896970
- 6 pruebas nuevas y 4 subtests: aprobados
- 110 pruebas 3 Oaks y 104 subtests: aprobados
- 986 pruebas generales y 239 subtests: aprobados

Esta corrida valida código offline, no repite el demo ni certifica otros juegos todavía marcados PARCIAL. El HAR original no se sube a GitHub.
