Plan Opus turno 7 iter 2 (app web local, http.server + index.html con polling cada 2 s):
- En partida: franja compacta con 3 tarjetas desde companion.meta_fase(): nivel tuyo vs rival (iconos Data Dragon), CS vs meta minions10 (hasta el min 10), muertes desde el 14 vs meta <=2 (14-25). Aviso en vivo arriba.
- Al terminar: la linea de resumen_fin() como tarjetas con check/cruz; luego la revision (score) cuando llegue.
- --demo recorre fases solas: ChampSelect -> InProgress (meta de ejemplo) -> EndOfGame (fin de ejemplo).
- Arreglo: minions10() devuelve None si faltan campeon/minimo.
Pruebas: unittest de evento()/estado JSON con fixtures, sin navegador.
Pide: riesgos y una alternativa, breve.
