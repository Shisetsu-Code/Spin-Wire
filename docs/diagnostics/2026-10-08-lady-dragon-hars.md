# 3 Oaks: Lady Fortune y 15 Dragon Pearls — HAR

Los dos HAR del usuario se analizaron exclusivamente como evidencia local. Ningún token, cookie, session_id, request_id, cuerpo de login ni HAR completo se incorpora al repositorio. La evidencia de cliente pública procede del artefacto histórico de Actions 37735796749; allí se almacenó el client.js de Lady Fortune y el hash del cliente de 15 Dragon Pearls.

## Lady Fortune
- HAR SHA-256: f21a346d6ae10b90759f1bbc5758b7a1b60854874f1eef847a121a8b92d5ea37
- 137 requests del servidor demo: 1 login, 1 start, 10 sync, 122 play y otras entradas auxiliares de red. Las respuestas play son HTTP 200, status.code=OK.
- El servidor anuncia available_buy_bonus=[1,2,3], prices={"1":100,"2":200,"3":300}, available_booster=[1] y ante_bet=[1.25].
- 3 compras observadas: los payloads llevan bet_per_line=5, lines=20, bet_factor=20, ante_bet=0 y buy_spin_scatters_count=4/5/6. **No hay selected_mode**.
- Se observaron 3 freespin_init, 70 freespin, 32 respin y 3 freespin_stop. El estado final después de cada freespin_stop vuelve a spins con round_finished=true y spin disponible.
- Además, se observaron giros con ante_bet=1.25. Son un modo distinto de apostar; el ejecutor actual NO los prueba como modalidad independiente.

Históricamente el test de catálogo estaba PARCIAL con 3 compras pendientes, pero una comprobación del código más reciente sobre el client.js real confirmó que las tres rutas de compra ahora se reconocen y se generan exactamente (CI diagnóstico 37749973412). No fue necesaria otra corrección del parser para estas compras. Se añadió una regresión permanente que verifica el conjunto de campos y rechaza una compra cuando el antebet permanece activo.

## 15 Dragon Pearls
- HAR SHA-256: 44c533f9c8cd81d5e3c506ed69574fe8645461974332ba957541c4559c4f025a
- 31 solicitudes al servidor demo, con 12 spin, 1 bonus_init, 7 respin y 1 bonus_spins_stop entre los comandos play.
- No hay available_buy_bonus ni antebet anunciado en start.
- El duodécimo spin normal activó bonus_init. Después llegaron siete respin y el comando final bonus_spins_stop, todos sin parámetros de acción.
- Después de bonus_spins_stop se observó current=spins, actions=['spin'] y round_finished=true. El HAR se detiene ahí: no acredita dos giros posteriores al bonus.
- En el informe anterior el juego figuraba OK con solo un giro normal; no había recorrido el bonus natural.

Se actualizó un contrato ya presente, ligado exclusivamente al SHA-256 f9492c4f6bf9b86c5a98c6fb45abe5f3412a924838c799b5a81ec93cf89a74d6 del JavaScript público verificado previamente. Los tres estados certificados para este cliente son:
- bonus_init: current=spins
- respin: current=bonus
- bonus_spins_stop: current=bonus, bonus.back_to=spins

El motor conserva el control de acciones anunciadas, retorno a base y límite de continuaciones. Este registro no cambia otros juegos de 3 Oaks por similitud de nombre.

## Pruebas
- CI diagnóstico sobre código actual con el cliente real archivado: https://github.com/Shisetsu-Code/Spin-Wire/actions/runs/37749973412
- CI de regresión sobre los cambios: https://github.com/Shisetsu-Code/Spin-Wire/actions/runs/37750369961
- Resultado observado: 7 regresiones nuevas aprobadas; 117 pruebas 3 Oaks y 120 subpruebas; 993 pruebas generales y 255 subpruebas.
- Son **pruebas offline**. No declarar completa la cobertura hasta observar la compra y el bonus natural nuevamente con el ejecutor corregido en una sesión demo y confirmar su retorno.

Nota: el nombre comercial "free spin" no demuestra que el servidor use freespin. En 15 Dragon Pearls utiliza bonus_init/respin/bonus_spins_stop; Lady Fortune sí utiliza freespin_init/freespin/freespin_stop.
