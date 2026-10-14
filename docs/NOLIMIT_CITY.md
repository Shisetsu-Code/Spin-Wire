# Nolimit City: catálogo oficial

Proveedor integrado: `nolimit_city` / **Nolimit City**.

El catálogo oficial de afiliados contiene 140 demos del estudio en el corte del
2026-10-13. Fuente: https://nolimitcity.com/json/games.json. El enlace documentado
https://nolimitcity.com/json/affiliateGames.json redirige a ese feed.
Página pública: https://nolimitcity.com/games.

Cada fila usa name, code, studio y url. Solo se incorporan filas studio=Nolimit City;
no se atribuyen a este proveedor los juegos de otros estudios de Playin/Evolution.
code es la identidad de lanzamiento, symbol conserva su capitalización y slug
usa su forma normalizada. El enlace oficial es playin.com/embed/v1/demo/<code>.
Cambios de título no alteran esa identidad. Duplicados, colisiones de identidad,
enlaces de otro origen, nombres vacíos y catálogos vacíos se rechazan.

El snapshot incluido permite cargar el catálogo sin red. Una actualización en
línea agrega o actualiza registros sin borrar juegos existentes; este feed no
tiene autoridad de eliminación. No se inventan URLs de miniaturas: el feed no
las suministra. Los enlaces de demo permiten abrir el juego desde la grilla.

## Estado de ejecución

Los 140 juegos están cargados como PENDIENTE. Esta incorporación certifica el
catálogo y la identidad de sus demos, no sus rondas ni sus opciones. Al intentar
una prueba, el adaptador informa PARCIAL y genera un diagnóstico; no envía giros
por un protocolo supuesto y no produce contratos de farm ejecutables.

Compras, Action Spins, antebets y cantidades permanecen sin confirmar. Los flags
publicitarios no sustituyen el dominio de opciones de la sesión. El paso siguiente
es aprender primitivas a partir de HAR representativos y contrastarlas con el
servidor: autenticación, menú de opciones, precios, cargos, elecciones, cierre y
retorno. Las variantes de Playin no se presuponen iguales a las de otros accesos.

El proveedor aparece en el selector del escritorio y en el registro del ejecutor
por lotes. El catálogo se incluye en la compilación del ejecutable completo.
