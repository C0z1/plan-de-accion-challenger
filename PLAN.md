# Plan de acción v2 (2026-11-07)

Basado en 282 partidas de Solo/Duo (abril a octubre 2026, Riot API), ahora con **timeline** (minuto a minuto) y `challenges`.
Detalle: [`datos/analisis-2026-11-07.md`](datos/analisis-2026-11-07.md) (general) y [`datos/analisis-timeline-2026-11-07.md`](datos/analisis-timeline-2026-11-07.md) (timeline). Los porcentajes entre paréntesis son intervalos de confianza del 95% (Wilson).

**Cambios respecto a la v1:** se quitan las metas de KP y visión (no separan victorias de derrotas: KP es 41% en ambas, visión 1.01 contra 0.93). La métrica central pasa a ser **el oro contra tu rival y las muertes antes del minuto 14**. Las reglas que salían de muestras chicas quedan como "pistas", no como reglas.

## Dónde estás y cuánto falta

| | LP |
|---|---|
| Tú | Master 15 |
| Corte Grandmaster LAN (hoy) | 1,154 |
| Corte Challenger LAN (hoy) | 1,732 |

En Master se ganan y pierden unos 18–20 LP por partida (estimado; depende de tu MMR). Partidas aproximadas para llegar a ~1,750 LP:

| Win rate | LP netos por partida | Partidas para llegar a Challenger |
|---|---|---|
| 54% (tu temporada) | ~1.5 | ~1,200 (no es viable) |
| 58% | ~3 | ~600 |
| 62% | ~4.5 | ~390 |
| 65% | ~5.5 | ~320 |

**Conclusión:** con 54% no llegas. Lo que te va a llevar a Challenger es subir el win rate, no jugar más partidas.

## Lo que decide tus partidas (timeline)

| Oro contra tu rival a los 14 min | Partidas | WR |
|---|---|---|
| ≤ −1000 | 73 | 41% (31–53%) |
| −1000 a 0 | 79 | 52% (41–63%) |
| 0 a +1000 | 81 | 57% (46–67%) |
| ≥ +1000 | 47 | **72%** (58–83%) |

- En promedio llegas al 14 con **−152 de oro** contra tu rival (victorias +104, derrotas −452). En las derrotas vas **−8 de CS y −335 de XP** al 14: pierdes la línea más por farm y experiencia que por muertes.
- Mueres **2.2 veces antes del minuto 14**, casi igual en victorias (2.12) que en derrotas (2.29). La excepción: en las 25 partidas sin morir antes del 14 ganaste el 76% (57–89%).
- **Las muertes que sí separan son las del mid game:** del minuto 14 al 25 mueres 2.29 veces en las victorias y 3.06 en las derrotas; del 25 en adelante, 1.34 contra 2.05. (Parte es consecuencia de ir perdiendo, pero ahí está la diferencia.)
- **El 52% de tus muertes antes del 14 incluyen al jungla rival.** Las zonas donde más mueres son tu mitad de la línea de mid (182 muertes tempranas) y el río (65% con el jungla rival presente).
- Jugando mid, 1 de cada 3 muertes tempranas (139/414) pasa **fuera de la línea**: río (62) y jungla rival (32).
- **Casi nunca compras control wards:** 0.16 por partida, y en el 93% de tus partidas no compraste ninguno.
- Lo que más separa victorias de derrotas en el early (challenges): ventaja máxima de nivel sobre tu rival (+0.75) y kills en solitario (+0.47). (Se quita `turretPlatesTaken`: da hasta 23 por jugador y una línea solo tiene 5 placas por torre exterior, así que no mide tus placas.) Los skillshots esquivados y la visión casi no influyen.

## Virtudes (con datos)
- **Yone:** 65 partidas, 58% (46–70%). Va −234 de oro al 14 en promedio (−151 incluso cuando gana): es de escalar, no necesita ganar la línea.
- **Mordekaiser top:** 22 partidas, 68% (47–84%), aunque pierde la línea (−428 al 14).
- **Ekko gana la línea:** +177 al 14 y llega arriba en el 56% de sus partidas (Yone y Sylas, 41–43%). **Y sí convierte:** con la línea ganada gana 60% (45–74%), igual que el resto (62%).
- **Kills en solitario:** 2.1 por partida (2.5 en victorias). Mecánicamente le ganas a tu rival.
- **No hay patrón de tilt:** después de una derrota tienes 55% WR.

## Defectos (con datos)
1. **Pierdes la línea por farm y XP:** en las derrotas llegas al 14 con −452 de oro, −8 de CS y −335 de XP. Además, mueres 2.2 veces antes del 14 (la mitad por gank) y 3.06 veces del 14 al 25 en las derrotas.
2. **Sylas es tu campeón más jugado y el que peor rinde:** 92 partidas, 52% (42–62%), −264 de oro al 14 (−615 en derrotas).
3. **Mala racha actual:** 44% en las últimas 50 y 35% en las últimas 20. **No es la línea:** en las últimas 20 llegas al 14 con oro ≥ 0 en el 60% (antes 45%) y con +360 de oro, pero de esas 12 solo ganaste 5 (42%, contra 65% antes), mueres 2.95 veces del 14 al 25 (antes 2.62) y el 60% fueron con campeones fuera del pool (Sylas, Locke, Zeri, Rakan). Muestra chica (n=12 y 20): pista, pero apunta a las prioridades 2 y 3, no a la 1. Fuente: `datos/analisis-revision-2026-11-07.md`.
4. **Ekko no aguanta ir abajo:** con oro < 0 al 14 gana 42% (26–59%), como Sylas (43%); Yone, en cambio, 57% (41–71%). Su 52% no es por no convertir, es por cómo juega cuando pierde la línea. Fuente: [`datos/analisis-convertir-2026-11-07.md`](datos/analisis-convertir-2026-11-07.md), `scripts/convertir.py`.
   - **Lo que hunde a Ekko abajo es el farm, no las muertes:** con la línea perdida muere igual en V y en D (2.31 contra 2.17 antes del 14), pero en las victorias llega al 14 con CS −0.2 y XP +24, y en las derrotas con CS −17 y XP −715. Si pierde más de 10 de CS al 14, 4/17 = 24% (10–47%); si no, 9/14 = 64% (39–84%). Por XP la brecha es igual o mayor: > 500 abajo, 3/15 = 20% (7–45%); ≤ 500, 10/16 = 62% (39–82%). Fuente: [`datos/analisis-linea-2026-11-07.md`](datos/analisis-linea-2026-11-07.md), `scripts/linea.py`.

## Prioridades (máximo 3)

### 1. Llegar al minuto 14 con el oro igualado o a favor (la palanca más grande)
- Pasar de −1000 a +1000 de oro al 14 es pasar de 41% a 72% de WR. Lo que más pierdes es farm y XP, así que prioriza el CS sobre los tradeos dudosos.
- Pierdes menos farm si no te matan en ganks: a los 2:45–3:15 (primer gank posible) y cada vez que el jungla rival desaparece del mapa, no pases de la mitad de la línea sin visión del río.
- **Compra 1 control ward en cada regreso a base** y ponlo en el río o en el arbusto lateral de tu línea. Hoy lo haces en el 7% de las partidas. Por sí sola, la visión no separa victorias de derrotas: el objetivo es evitar los ganks, no subir el número.
- No sigas al rival a la jungla ni al río antes del 14 si no sabes dónde está su jungla (ahí pasan 1 de cada 3 de tus muertes tempranas en mid).
- **Si ya vas abajo, cuida el farm más que las muertes** (`scripts/linea.py`, 148 líneas perdidas): con la línea perdida mueres antes del 14 casi lo mismo en V que en D (2.62 contra 2.32), pero en las derrotas vas −16 de CS y −806 de XP contra −11 y −529 en las victorias. Perder > 10 de CS al 14: 44% (34–55%); ≤ 10: 53% (41–65%). Con Ekko la brecha es mayor (24% contra 64%). Abajo: farmea bajo torre y no roamees si eso te cuesta oleadas. (El CS es parte del oro, así que esto dice *qué parte* de la desventaja pesa, no que sea otra causa.)
  - **Lo que de verdad pesa es la XP, no el CS** (control de DeepSeek: a igual oro, 74 partidas entre −1500 y −500 al 14): partiendo por la mediana, el CS no separa (47% contra 44%), la XP sí: XP @14 ≥ −566 → 24/37 = 65% (49–78%); peor → 10/37 = 27% (15–43%). Los IC no se cruzan. En todas las líneas perdidas: perder ≤ 500 de XP → 59% (46–70%); > 500 → 40% (31–51%); Ekko 62% contra 20% (3/15). Abajo, **quédate en rango de XP de cada oleada** (aunque no puedas farmear bajo presión) Es pista fuerte, no hecho: la XP también baja si tu rival roamea con éxito.
  - **¿De dónde sale esa XP?** (`scripts/xp.py`, minuto a minuto del 2 al 14, foto por minuto): casi toda de **los minutos en que mueres** (−760 de XP contra tu rival, igual en V y en D). Regresos (−34/−9) y roams (−85/−99) casi no cuestan, y 2+ minutos fuera de la línea no baja el WR (54% contra 45%). Lo que separa remontar de no: **la XP de matar a tu rival** (+420 en V contra +226 en D, el 70% de la brecha) y algo de farm en línea (−76 contra −159). Abajo: **no te dejes matar otra vez y castiga a tu rival cuando se exponga**; no hace falta quedarte encerrado en la línea (10+ minutos en línea sin salir: 8/25 = 32% (17–52%), pista).
  - **Castigar a tu rival sí es tuyo** (`scripts/castigo.py`, 147 líneas perdidas): de la XP de "muere él", +325 en V y +193 en D son de minutos en que participaste en el kill (≈77%); solo +95/+31 son de kills sin ti. Con la línea perdida y 0 kills tuyos sobre tu rival antes del 14 ganas 23/58 = 40% (28–53%); con 1 o más, 48/89 = 54% (44–64%); con al menos uno en solitario, 59% (43–72%). Los kills en solitario son 92% en tu propia línea y te cuestan morir en los 20 s siguientes 1 de cada 4 veces. Con tu jungla no suben el WR (45%). Ekko: 57% con 1+ kill contra 31% con 0; Yone gana igual sin kills (62%). Es pista (los IC se cruzan): abajo, busca el kill en tu línea cuando el rival se pase, no el gank forzado. (Contar también el minuto siguiente a tu muerte como "muerto" casi no cambia: −786/−818 contra −759/−763.)
  - **El farm perdido no depende del matchup:** CS @14 por rival de línea (19 rivales con 5+): permutación p = 0.30. No elijas pick para "no perder farm"; es cómo juegas la línea.
- Métricas: **oro ≥ 0 contra tu rival al 14 en más del 55% de las partidas** (hoy 46%: 128 de 280) y CS al 14 sin desventaja en promedio (hoy −3).

### 2. Cerrar el champion pool
- **Mid:** Yone (principal) y Ekko (secundario). Si el matchup es malo y crees que vas a perder la línea, Yone (aguanta ir abajo: 57% contra 42% de Ekko).
- **Top / flexible:** Mordekaiser.
- **Sylas** solo cuando el matchup sea claramente bueno, no por costumbre.
- Métrica: más del 80% de tus partidas con esos 3 campeones.

### 3. Mid game: convertir la ventaja y no regalar muertes del 14 al 25
- Con ventaja: empuja, toma torres y rota al objetivo con tu jungla, en vez de farmear en mid. Con Ekko y la línea ganada, en las victorias haces 4.5 takedowns de torre contra 2.2 en las derrotas y pasas el 25% del 15 al 24 en tu línea contra el 34% (WR 69% si estás < 50% en línea, 25% en 8 partidas si no: pista).
- El 43% de todas tus muertes son contra 3 o más enemigos. Antes de entrar a una zona sin visión, cuenta cuántos rivales se ven en el mapa.
- **Cuando ganas la línea y pierdes la partida** (48 de 128; fuente: [`datos/analisis-midgame-2026-11-07.md`](datos/analisis-midgame-2026-11-07.md), `scripts/midgame.py`):
  - Lo que más pesa es tu equipo: con tu línea ganada y el equipo con oro < 0 al 14 ganas 40% (25–58%), y con el equipo ≥ 0, 69% (60–78%). En las derrotas el equipo pasa de +502 al 14 a −438 al 20.
  - Lo que sí depende de ti es cuántas veces mueres: con 1–2 muertes del 14 al 25 ganas 74% (60–84%), y con 3 o más, 50% (38–62%).
  - **No es solo consecuencia de que tu equipo vaya abajo:** con tu línea ganada *y* el equipo con oro ≥ 0 al 14, ganas 82% (69–90%, 49 partidas) con 0–2 muertes del 14 al 25 y 57% (43–70%, 49) con 3 o más. Si además el equipo sigue ≥ 0 al 20, 84% contra 61% (revisión de DeepSeek): el efecto se mantiene pero los intervalos ya se cruzan, así que es pista fuerte, no hecho.
  - En las derrotas, el 72% de esas muertes vienen seguidas de un objetivo perdido (dragón, heraldo, barón o torre) en los 90 s siguientes. Desde un instante cualquiera de esas partidas la cifra es 58%: morir regala objetivos.
  - Morir solo (pick-off) **no** separa victorias de derrotas: 37% de tus muertes en victorias contra 33% en derrotas. El problema es cuántas veces mueres y cuándo, no si estabas solo.
  - Regla: **antes de que salga un dragón, heraldo o barón, no pelees si no hace falta**. Y si tu equipo va abajo aunque tú ganes la línea, juega a no morir y que tu ventaja no se pierda: el rival necesita tu muerte para tomar el objetivo.
- Métrica: **≤ 2 muertes del minuto 14 al 25** (tu promedio en victorias es 2.29; hoy 2.65). Como parte de esas muertes es consecuencia de ir perdiendo, sirve más para vigilar que como meta por sí sola.

## En champ select: `python scripts/draft.py <rival> [rol]`
- Te dice tu récord contra ese rival, tu WR cuando está en el equipo rival y qué campeón de tu pool pickear. El estimado mezcla tu récord contra el rival con tu WR del campeón (pesa como 10 partidas), así que con pocas partidas manda tu WR general.
- Guía completa (bans, rivales de línea, pool por rol): [`datos/analisis-matchups-2026-11-07.md`](datos/analisis-matchups-2026-11-07.md).
- **Ningún ban tiene respaldo estadístico todavía:** de 80 rivales con 8+ partidas, solo 2 (Lulu y Diana) quedan claramente bajo tu WR base, y barajando al azar tus victorias y derrotas salen ~1.7, con 2 o más en la mitad de las barajadas. Banea por comodidad, no por estos números.

## Después de cada sesión y los domingos: `python scripts/revision.py [N]`
- Compara tus últimas N partidas (20 por defecto) contra las anteriores en cada meta del plan (WR, oro y CS al 14, WR cuando vas arriba al 14, muertes por fase, control wards, pool) y marca ✅/❌. Abajo trae la tabla partida por partida. Antes corre `scripts/descargar.py` para bajar las nuevas.

## Pistas (muestra chica: vigílalas, no son reglas)
- Viktor en mid: 1-7 (2–47%), y **Ekko 0-4** contra él. Si sale Viktor, no pickees Ekko (`draft.py` recomienda Yone). Como ban sigue siendo pista.
- Diana en mid: 2-5 y llegas al 14 con **−1322 de oro**, el peor oro de todos tus rivales de línea frecuentes. Yone va 0-3 contra ella.
- La 3.ª partida de cada sesión: 43% (28–59%), contra 57% en la 1.ª. Para después de 2 derrotas seguidas, por si acaso.
- De 8 a 12 de la mañana: 36% (15–65%), en solo 11 partidas.
- Support/Pyke 67% (44–84%) en 18 partidas.

## Decisión: mid sigue siendo el rol principal (`python scripts/rol.py`)
- Top 58% (46–70%, 60 partidas) contra mid 54% (47–60%, 198). Con un test de permutación, p = 0.55: la diferencia es ruido, y para confirmarla harían falta ~1,700 partidas por rol.
- Lo que hace bueno a top es **Mordekaiser** (15-7, 68%), no el rol: top sin Mordekaiser va 53% (37–68%). Yone rinde igual en mid (59%) que en top (58%).
- En top llegas peor al 14 (−358 de oro contra −112 en mid) y en las últimas 20 de top vas 8-12 (40%).
- **Sylas top: 4-7 (36%, 15–65%).** Si te toca top, Mordekaiser o Yone, no Sylas.
- Fuente: [`datos/analisis-rol-2026-11-07.md`](datos/analisis-rol-2026-11-07.md).

## Metas semanales
- Semana 1: cortar la racha. 55% o más de WR, oro ≥ 0 al 14 en más de la mitad de las partidas, al menos 1 control ward por partida, pool cerrado.
- Después: 58% o más sostenido, con oro ≥ 0 al 14 en más del 55% y ≤ 2 muertes del 14 al 25. Revisa los números cada domingo con `scripts/revision.py` (y, para el detalle, `scripts/analizar.py` y `scripts/timeline.py`) (antes corre `scripts/descargar.py` para bajar las partidas nuevas y sus timelines).
