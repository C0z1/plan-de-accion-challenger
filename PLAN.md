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
- Lo que más separa victorias de derrotas en el early (challenges): ventaja máxima de nivel sobre tu rival (+0.75), placas de torre (+0.86) y kills en solitario (+0.47). Los skillshots esquivados y la visión casi no influyen.

## Virtudes (con datos)
- **Yone:** 65 partidas, 58% (46–70%). Va −234 de oro al 14 en promedio (−151 incluso cuando gana): es de escalar, no necesita ganar la línea.
- **Mordekaiser top:** 22 partidas, 68% (47–84%), aunque pierde la línea (−428 al 14).
- **Ekko gana la línea:** +177 al 14, +623 cuando gana. Pero solo tiene 52% de WR: no convierte la ventaja.
- **Kills en solitario:** 2.1 por partida (2.5 en victorias). Mecánicamente le ganas a tu rival.
- **No hay patrón de tilt:** después de una derrota tienes 55% WR.

## Defectos (con datos)
1. **Pierdes la línea por farm y XP:** en las derrotas llegas al 14 con −452 de oro, −8 de CS y −335 de XP. Además, mueres 2.2 veces antes del 14 (la mitad por gank) y 3.06 veces del 14 al 25 en las derrotas.
2. **Sylas es tu campeón más jugado y el que peor rinde:** 92 partidas, 52% (42–62%), −264 de oro al 14 (−615 en derrotas).
3. **Mala racha actual:** 44% en las últimas 50 y 35% en las últimas 20. **No es la línea:** en las últimas 20 llegas al 14 con oro ≥ 0 en el 60% (antes 45%) y con +360 de oro, pero de esas 12 solo ganaste 5 (42%, contra 65% antes), mueres 2.95 veces del 14 al 25 (antes 2.62) y el 60% fueron con campeones fuera del pool (Sylas, Locke, Zeri, Rakan). Muestra chica (n=12 y 20): pista, pero apunta a las prioridades 2 y 3, no a la 1. Fuente: `datos/analisis-revision-2026-11-07.md`.
4. **Ekko no convierte:** gana la línea pero tiene el mismo WR que Sylas.

## Prioridades (máximo 3)

### 1. Llegar al minuto 14 con el oro igualado o a favor (la palanca más grande)
- Pasar de −1000 a +1000 de oro al 14 es pasar de 41% a 72% de WR. Lo que más pierdes es farm y XP, así que prioriza el CS sobre los tradeos dudosos.
- Pierdes menos farm si no te matan en ganks: a los 2:45–3:15 (primer gank posible) y cada vez que el jungla rival desaparece del mapa, no pases de la mitad de la línea sin visión del río.
- **Compra 1 control ward en cada regreso a base** y ponlo en el río o en el arbusto lateral de tu línea. Hoy lo haces en el 7% de las partidas. Por sí sola, la visión no separa victorias de derrotas: el objetivo es evitar los ganks, no subir el número.
- No sigas al rival a la jungla ni al río antes del 14 si no sabes dónde está su jungla (ahí pasan 1 de cada 3 de tus muertes tempranas en mid).
- Métricas: **oro ≥ 0 contra tu rival al 14 en más del 55% de las partidas** (hoy 46%: 128 de 280) y CS al 14 sin desventaja en promedio (hoy −3).

### 2. Cerrar el champion pool
- **Mid:** Yone (principal) y Ekko (secundario).
- **Top / flexible:** Mordekaiser.
- **Sylas** solo cuando el matchup sea claramente bueno, no por costumbre.
- Métrica: más del 80% de tus partidas con esos 3 campeones.

### 3. Mid game: convertir la ventaja y no regalar muertes del 14 al 25
- Con ventaja (sobre todo con Ekko): empuja, toma placas y rota al objetivo con tu jungla, en vez de farmear en mid. Las placas son de lo que más separa victorias de derrotas (11.7 contra 6.8).
- El 43% de todas tus muertes son contra 3 o más enemigos. Antes de entrar a una zona sin visión, cuenta cuántos rivales se ven en el mapa.
- **Cuando ganas la línea y pierdes la partida** (48 de 128; fuente: [`datos/analisis-midgame-2026-11-07.md`](datos/analisis-midgame-2026-11-07.md), `scripts/midgame.py`):
  - Lo que más pesa es tu equipo: con tu línea ganada y el equipo con oro < 0 al 14 ganas 40% (25–58%), y con el equipo ≥ 0, 69% (60–78%). En las derrotas el equipo pasa de +502 al 14 a −438 al 20.
  - Lo que sí depende de ti es cuántas veces mueres: con 1–2 muertes del 14 al 25 ganas 74% (60–84%), y con 3 o más, 50% (38–62%).
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
- **Top contra mid:** top 58% (46–70%, 60 partidas) contra mid 54% (47–60%, 198 partidas). Los intervalos se cruzan: todavía no hay razón para cambiar de rol principal. Support/Pyke 67% (44–84%) en 18 partidas.

## Metas semanales
- Semana 1: cortar la racha. 55% o más de WR, oro ≥ 0 al 14 en más de la mitad de las partidas, al menos 1 control ward por partida, pool cerrado.
- Después: 58% o más sostenido, con oro ≥ 0 al 14 en más del 55% y ≤ 2 muertes del 14 al 25. Revisa los números cada domingo con `scripts/revision.py` (y, para el detalle, `scripts/analizar.py` y `scripts/timeline.py`) (antes corre `scripts/descargar.py` para bajar las partidas nuevas y sus timelines).
