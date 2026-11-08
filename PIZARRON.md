# Pizarrón del equipo

> Contexto vivo del repo. **Léelo primero.** Cada agente edita **solo su sección** de "Ahora": la actualiza al empezar y al terminar cada turno. En "Hallazgos" y "Decisiones" solo se agregan renglones, no se borran.
> El detalle largo va en `datos/notas-equipo.md`. Aquí van solo líneas cortas.

## Meta
Llevar a `cozi#1134` (LAN) de **Master 15 LP a Challenger** (~1,750 LP). Para lograrlo hay que subir el WR de **54% a 60% o más** (ver `PLAN.md`).

## Ahora

### Opus · constructor
- **Estado:** turno 2, iteración 5 terminada. `scripts/test_draft.py` (draft con partidas sintéticas + humo de `revision.py 1`; 11 pruebas pasan). `descargar.py`: con 401/403 abre el portal de Riot y lee la key también de `HKCU\Environment`.
- **Siguiente:** fixture de EndOfGame en companion; leer la revisión de DeepSeek de 61631e7 (`rivales()` y errores de descargar).
- **Actualizado:** 2026-11-07 23:25 (turno 2, iteración 5, cierre)

### DeepSeek · revisor
- **Estado:** revisado 485ecba (`scripts/muertes6.py` corre y reproduce). Respuestas a las iteraciones 1, 2 y 3 de Opus en `notas-equipo.md`.
- **Siguiente:** nada mío pendiente. Opus: la meta de Sylas conviene que marque ✅/❌ solo con n ≥ 10 (n=4 es ruido).
- **Actualizado:** 2026-11-07 23:12

## Mapa del repo
| Archivo | Qué es | Dueño |
|---|---|---|
| `PLAN.md` | Plan de acción vigente | Opus |
| `scripts/descargar.py` | Baja partidas y timelines de la Riot API a `datos/raw/` | Opus |
| `scripts/analizar.py` | Estadísticas agregadas → `datos/analisis-*.md` | Opus |
| `scripts/timeline.py` | Análisis de timeline (muertes, oro por minuto) | Opus |
| `scripts/draft.py` | Guía de matchups (sin args) o recomendación de pick: `draft.py <rival> [rol]` | Opus |
| `datos/analisis-matchups-*.md` | Guía de matchups y bans generada por `draft.py` | Opus |
| `scripts/revision.py` | Últimas N partidas contra las metas del plan (✅/❌) + tabla por partida: `revision.py [N]` | Opus |
| `datos/analisis-revision-*.md` | Salida de `revision.py 20` | Opus |
| `scripts/midgame.py` | Mid game en partidas con la línea ganada al 14: oro del equipo, muertes 14–25 (pick-off, objetivo perdido, zona) | Opus |
| `datos/analisis-midgame-*.md` | Salida de `midgame.py` | Opus |
| `scripts/rol.py` | Mid contra top (y demás roles): WR, línea, conversión, campeones, tendencia, permutación | Opus |
| `datos/analisis-rol-*.md` | Salida de `rol.py` | Opus |
| `scripts/convertir.py` | Línea ganada al 14 por campeón y V/D de uno: `convertir.py [Campeón]` (Ekko por defecto) | Opus |
| `datos/analisis-convertir-*.md` | Salida de `convertir.py` | Opus |
| `scripts/linea.py` | Línea perdida al 14: muertes por gank/1v1, CS, XP, por campeón y V/D: `linea.py [Campeón]` | Opus |
| `datos/analisis-linea-*.md` | Salida de `linea.py` | Opus |
| `scripts/xp.py` | XP vs rival 2–14 minuto a minuto según tu estado (muerto, matas al rival, base, fuera, línea) | Opus |
| `datos/analisis-xp-*.md` | Salida de `xp.py` | Opus |
| `scripts/castigo.py` | Línea perdida: cómo muere tu rival antes del 14 (tú solo, con jungla, sin ti), XP tuya contra ajena, WR | Opus |
| `datos/analisis-castigo-*.md` | Salida de `castigo.py` | Opus |
| `scripts/placas.py` | Placas reales del timeline en tu línea (tuyas, del equipo, perdidas) contra WR, a igual oro y por campeón | Opus |
| `datos/analisis-placas-*.md` | Salida de `placas.py` | Opus |
| `scripts/nivel6.py` | Diferencia de nivel con tu rival 0–14: muertes/kills por 10 min (con y sin jungla rival), zona de la muerte (arriba contra igual), carrera al 2 y al 6 | Opus |
| `datos/analisis-nivel-*.md` | Salida de `nivel6.py` | Opus |
| `scripts/early.py` | Qué separa V/D en el early por campeón (challenges + timeline @14, permutación y q de BH, control a igual oro) | Opus |
| `datos/analisis-early-*.md` | Salida de `early.py` | Opus |
| `scripts/partida.py` | Replay en datos de una partida (min 12–26, o 0–12 con `--early`) o de las últimas derrotas con la línea ganada: `partida.py [id [--early] | --ultimas N]` | Opus |
| `datos/analisis-decisiones-*.md` | Revisión de decisiones en derrotas con la línea ganada | Opus |
| `scripts/objetivos.py` | Presencia en objetivos, minuto de los ganks y muertes del late a igual oro | Opus |
| `datos/analisis-objetivos-*.md` | Salida de `objetivos.py` | Opus |
| `scripts/muertes6.py` | Muertes antes del 6: tipo (1v1/gank), nivel al 3 y al 6, WR y oro @14, por campeón y rival, últimas 10 | Opus |
| `datos/analisis-muertes6-*.md` | Salida de `muertes6.py` | Opus |
| `scripts/wards.py` | Control wards: tú y los 1,431 jugadores de línea ajenos (gank <14 y WR, a igual oro y por rol) | Opus |
| `datos/analisis-wards-*.md` | Salida de `wards.py` | Opus |
| `scripts/companion.py` | Lee el cliente de LoL (solo lectura): en champ select corre `draft.py` contra tu rival; al terminar, `descargar.py 5` + `revision.py 1`. `--fixture <carpeta>` para probar | Opus |
| `scripts/fixtures/` | JSON de ejemplo de la LCU (gameflow-phase, champ-select session) | Opus |
| `scripts/test_companion.py` | Pruebas sin red: `python -m unittest discover scripts` | Opus |
| `scripts/test_draft.py` | Pruebas de `draft.py` (funciones y recomendación con partidas sintéticas) y humo de `revision.py 1` | Opus |
| `datos/notas-equipo.md` | Detalle de cada turno y de cada revisión | Ambos (solo agregar) |
| `BITACORA.md` | Sesiones jugadas por el usuario | DeepSeek |
| `PIZARRON.md` | Este pizarrón | Ambos (cada quien su sección) |
| `RESUMEN-NOCHE.md` | Resumen del turno nocturno para el usuario | Opus |
| `TARJETA.md` | Reglas del PLAN en una página, para jugar | Opus |

## Hallazgos (con datos)
- 2026-11-07 · DeepSeek: KP es 41% en victorias y en derrotas, así que no las separa. Lo que sí separa es muertes (5.8 vs 7.4) y oro contra el rival (+1313 vs −1566).

- 2026-11-07 · Opus: ningún ban tiene respaldo: 2 de 80 rivales quedan bajo el WR base y el azar da ~1.9.
- 2026-11-07 · Opus: Viktor mid 1-7 (Ekko 0-4); Diana mid 2-5 con −1322 de oro al 14.
- 2026-11-07 · Opus: la racha (35% en últimas 20) no es de línea: oro ≥ 0 al 14 en 60% (antes 45%), pero convierte 5 de 12 (42% vs 65%); 60% fuera del pool.
- 2026-11-07 · DeepSeek: el "convierte 5 de 12 (42%)" es pista, no hecho: n=12, IC 19–68% se cruza con el 65% (56–73%) de la temporada.
- 2026-11-07 · DeepSeek: `gameEndedInEarlySurrender` no existe en los 300 JSON; el filtro de remakes vive solo de `gameDuration < 300` (alcanza: las 18 remakes son <300s). Código muerto en timeline/draft/revision.
- 2026-11-07 · Opus: con la línea ganada al 14, si el equipo va < 0 de oro gana 40% (25–58), y si va ≥ 0, 69% (60–78). Con 3+ muertes del 14 al 25, 50%; con 1–2, 74%.
- 2026-11-07 · Opus: en las derrotas, el 72% de las muertes del 14 al 25 vienen seguidas de un objetivo perdido en 90 s (línea base 58%). Los pick-offs no separan (37% contra 33%).
- 2026-11-07 · Opus: la permutación a nivel de partida (sugerida por DeepSeek) confirma que no hay bans con respaldo: 2 reales contra ~1.7 del azar (p = 0.50).
- 2026-11-07 · DeepSeek: la base de "objetivo perdido en 90 s" tiene sesgo leve por partidas cortas (56% vs 58% en partidas ≥ 25 min): no cambia la conclusión.
- 2026-11-07 · DeepSeek: cortando por oro del equipo al 20 (con equipo ≥ 0), 0–2 muertes 14–25 → 84% (n=44) y 3+ → 61% (n=36, IC se cruzan): el efecto de las muertes se mantiene pero se debilita.
- 2026-11-07 · Opus: top 58% contra mid 54% es ruido (permutación p = 0.55). Top es bueno por Mordekaiser (68%); top sin Morde, 53%. Sylas top 4/11.
- 2026-11-07 · Opus: las muertes del 14 al 25 pesan aunque el equipo vaya bien: con línea y equipo ≥ 0 al 14, 0–2 muertes → 82% (69–90); 3+ → 57% (43–70).
- 2026-11-07 · Opus: Ekko sí convierte: con línea ganada 60% (45–74), igual que el resto (62%). Con línea perdida 42%, como Sylas (43%); Yone 57%.
- 2026-11-07 · Opus: `turretPlatesTaken` no mide tus placas (da hasta 23 por jugador; el máximo de un equipo es 15). Se quitó del PLAN.
- 2026-11-07 · Opus: con la línea perdida (148), las muertes <14 no separan (V 2.62, D 2.32); sí CS y XP @14 (−11/−529 contra −16/−806). Solo 5/148 líneas perdidas sin morir.
- 2026-11-07 · Opus: Ekko con línea perdida: V llega con CS −0.2 y XP +24, D con −17 y −715. > 10 CS abajo: 4/17 (24%); ≤ 10: 9/14 (64%).
- 2026-11-07 · Opus: a igual oro (−1500 a −500 al 14, n=74) el CS no separa (47% vs 44%) y la XP sí: ≥ mediana 65% (49–78), < mediana 27% (15–43).
- 2026-11-07 · Opus: el CS @14 por rival de línea no se aleja del azar (19 rivales, permutación p = 0.30): el farm perdido no es de matchup.
- 2026-11-07 · DeepSeek: dentro de Sylas solo el CS @14 por rival sigue variando (Yasuo −26, Qiyana −20, Viktor −28, contra Zed +4): el p=0.30 no es confusión con tu campeón, es que 3 rivales que niegan farm se diluyen entre ~19 neutros. Muestra chica (pista).
- 2026-11-07 · DeepSeek: el filtro "20+ min" (`len(fr) <= 20`) deja entrar 2 partidas que acaban en 19:21 y 19:36; su "@20" lee el frame final. Menor (2 de 275).
- 2026-11-07 · Opus: con la línea perdida, los minutos de muerte cuestan −760 de XP en V y en D; regresos y roams ~0. La brecha V/D (−529 vs −806) es 70% XP de matar al rival (+420 vs +226).
- 2026-11-07 · Opus: con la línea perdida, de la XP de "muere él" +325/+193 (V/D) es de kills contigo y +95/+31 sin ti. 0 kills tuyos sobre el rival antes del 14: 40% (28–53); 1+: 54% (44–64); 1+ en solitario: 59%.
- 2026-11-07 · Opus: contar el minuto siguiente a tu muerte como "muerto" casi no cambia xp.py (−786/−818 contra −759/−763).
- 2026-11-07 · Opus: corrige el renglón de `turretPlatesTaken`: en este parche hay hasta 15 placas por línea y equipo (3 torres) y caen después del 14. Igual no son tus placas (cuadra con los last hits del timeline en 159/600).
- 2026-11-07 · Opus: tus placas antes del 14 no separan V/D (ganada 2.17/2.02, perdida 1.28/1.13). Las perdidas sí, a igual oro: 0–1 contra 3+ → 58/36, 65/54, 76/50% en las 3 bandas (pista).
- 2026-11-07 · DeepSeek: a igual oro (−1500 a −500, n=73) el "1+ kill → 54%" baja a 39% vs 52% (IC 25–56 vs 37–67): parte es ir menos perdido (−844 vs −1201 de oro); el kill con jungla llega con el peor CS @14 (−16.1).
- 2026-11-07 · Opus: placas perdidas <14: estando fuera (base/roam) no separan (0 → 56%, 1+ → 52%); estando en tu línea sí (63% contra 48%); muerto 0.89/1.18 V/D. Es el rival con prioridad, no irte.
- 2026-11-07 · DeepSeek: ese "estando en tu línea separa" es artefacto de la foto gruesa: con placas a ≤15 s de un frame (316/645) pasa de 63 vs 48% a 54 vs 56%, y se invierte en 2 bandas. No concluyente.
- 2026-11-07 · Opus: el filtro `gameDuration ≥ 1200` en linea/convertir/xp saca 2 derrotas de 19:xx; nada cambia de conclusión (Ekko abajo 43%, XP en D −816).
- 2026-11-07 · Opus: yendo 1 nivel arriba de tu rival antes del 14 mueres ×1.31 (1.06–1.61) que a nivel igual; 65% con el jungla rival (49% igual). Abajo, ×1.04: no mueres más.
- 2026-11-07 · Opus: medir el nivel en el instante de la muerte da un "1 abajo" falso (×1.5) por el LEVEL_UP que tu kill le da al rival; se mide 3 s antes.
- 2026-11-07 · Opus: primero al 6: 62% contra 48%, pero a igual oro 52/44, 56/47, 69/62 (IC cruzados): casi todo es reflejo de ir arriba. Primero al 2: 59% contra 51%.
- 2026-11-07 · DeepSeek: placas perdidas "estando en tu línea" no separan con placas a ≤ 15 s de una foto (54% contra 56%): era artefacto de la foto por minuto.
- 2026-11-07 · Opus: yendo arriba de nivel, en tu lado de la línea mueres menos (×0.75, 0.52–1.08); pasado el río ×1.89 (1.35–2.64); jungla rival ×2.53 (1.23–5.21).
- 2026-11-07 · Opus: tu ward en los 90 s previos a morir no cambia la proporción de ganks (arriba 64% contra 67%); el timeline no trae la posición del ward.
- 2026-11-07 · Opus: bootstrap por partida: ×1.31 (1.07–1.58), pasado el río ×1.89 (1.28–2.62) aguantan; pero en mid 1 arriba ×1.12 (0.85–1.44) y pasado el río ×1.43 (0.82–2.25). Es efecto de top/bot (×2.43).
- 2026-11-07 · Opus: muertes <14 pasado el río por partida no separan V/D (1.10 contra 1.05; 0 → 51%, 1+ → 57%): el riesgo es cruzar con nivel arriba, no cruzar.
- 2026-11-07 · Opus: Sylas con > 68 minions de línea al 10: 74% (60–85); ≤ 68: 32% (20–46), q = 0.01. Aguanta en cada tercio de oro @14 y solo en mid. En el total no separa (67.2 contra 67.1).
- 2026-11-07 · Opus: Yone: ninguna de 18 métricas del early separa V/D (q ≥ 0.72). Ekko: XP/CS/oro @14 y kills <14 (q ≤ 0.03), casi todo reflejo del oro.
- 2026-11-07 noche · Opus: morir antes del 6 no baja el WR: 0 → 50% (42–58), 1+ → 59% (51–66); cuesta ~−430 de oro @14. Sin sangre (0 muertes y 0 kills <6): 45%. Las 1v1 <6 tampoco separan (54 contra 57%).
- 2026-11-07 noche · Opus: nivel al 3 no separa (55/54/56%); abajo al 6 → 44% (30–60), arriba 69% (51–82); 86% de las partidas abajo al 6 tuvieron muerte <6. Pista.
- 2026-11-07 noche · Opus: el % de partidas con muerte <6 sí varía por rival (permutación p = 0.04): Sylas 9/10, Fizz 5/6, Syndra 5/6, Ekko 4/5. n chica.
- 2026-11-07 noche · Opus: Sylas con 69+ minions al 10: 47% de las partidas antes de las últimas 20 (n=88) y 2 de 4 en las últimas 20. Ahora lo mide `revision.py`.
- 2026-11-07 noche · Opus: control ward antes del 14 no baja los ganks (0.85 contra 0.92 muertes por gank <14) ni sube el WR (49/49%) en 1,431 jugadores de línea ajenos; a igual oro tampoco. Tú: 8 de 261 partidas con alguno.
- 2026-11-07 · DeepSeek: "abajo al 6 → 44%" no es solo reflejo de morir: sin muerte <6 son 2/5 = 40% (n=5). Refuerza la pista "no salir del 6 con nivel abajo".
- 2026-11-07 · DeepSeek: el 74/32 de Sylas aguanta el filtro de `revision.py` (92 vs 90 Sylas: entran una partida de 12:49 y una jungle; >68 sigue 74%, ≤68 pasa 32→33%).
- 2026-11-07 noche · Opus: `companion.py` verificado en vivo y en solo lectura contra el cliente abierto (el lockfile existe; la fase era `InProgress`). El champ select solo se probó con fixtures.

## Decisiones
- 2026-11-07 · Configuración: Opus construye y hace los commits; DeepSeek-Pro revisa cada commit. Tope de DeepSeek: $5.
- 2026-11-07 · Opus: el pick se recomienda con un estimado encogido (M=10) hacia tu WR del campeón, no con el récord crudo contra el rival.
- 2026-11-07 · Opus: la meta del mid game baja a ≤ 2 muertes del 14 al 25 (también en revision.py) y queda como monitor. La regla nueva: no pelear si no hace falta antes de que salga un objetivo.
- 2026-11-07 · Opus: mid sigue siendo el rol principal; si toca top, Mordekaiser o Yone (no Sylas).
- 2026-11-07 · Opus: si esperas perder la línea, Yone antes que Ekko (aguanta ir abajo).
- 2026-11-07 · Opus: regla nueva en prioridad 1: si ya vas abajo, cuida el farm (bajo torre, no roamear a costa de oleadas) más que evitar muertes.
- 2026-11-07 · Opus: esa regla se precisa: abajo, lo que pesa es la XP; quedarse en rango de XP de cada oleada y no perder tiempo fuera de la línea.
- 2026-11-07 · Opus: se corrige la anterior con `xp.py`: el tiempo fuera de la línea no es donde se va la XP. Abajo: no morir otra vez y castigar al rival.
- 2026-11-07 · Opus: regla de placas en prioridad 1 (pista): antes del 14 no te vayas a base ni roamees con la oleada rival entrando a tu torre.
- 2026-11-07 · Opus: "castigar" se precisa con `castigo.py`: el kill en tu línea cuando el rival se pasa (pista), no el gank forzado con jungla.

- 2026-11-07 · Opus: se quita la regla "no te vayas a base con la oleada entrando" (placas perdidas fuera de línea no separan).
- 2026-11-07 · Opus: regla nueva en prioridad 1: al sacar ventaja de nivel, asume que viene el gank (mira el río, no empujes sin ver al jungla).
- 2026-11-07 · Opus: se precisa: con ventaja de nivel, tradea hasta la mitad de la línea y no persigas más allá sin ver al jungla rival.
- 2026-11-07 · Opus: en el PLAN, las placas perdidas en tu línea pasan a "sin causa clara" (revisión de DeepSeek).
- 2026-11-07 · Opus: la regla de "ventaja de nivel → gank" se acota a top/bot; en mid queda la general (no seguir al rival a su jungla).
- 2026-11-07 · Opus: `revision.py` ya no muestra `turretPlatesTaken` (no son tus placas) y suma "muertes <14 pasado el río" como monitor sin meta.
- 2026-11-07 · Opus: regla nueva para Sylas en el PLAN: no tradear ni roamear a costa de oleadas antes del 10 (meta 69+ minions al 10).
- 2026-11-07 · DeepSeek: el corte de Sylas (>68 min@10 → 74% vs 32%) es gradiente estable (64→61%, 72→77%), no umbral afortunado; top son 11/90 (ruido) y contra Qiyana farmea menos (56, n=5). El "en tu lado mueres menos" (×0.75) cruza 1 (bootstrap 0.49–1.06): es "no mueres más".
- 2026-11-07 noche · Opus: no se agrega regla "no tradear desde nivel 1" (los datos no la respaldan); entra al PLAN como pista: no salir del 6 con un nivel abajo.
- 2026-11-07 noche · Opus: la meta de Sylas (> 50% de sus partidas con 69+ minions al 10) entra a `revision.py`.
- 2026-11-07 noche · Opus: "control ward en cada regreso" deja de ser regla (sin respaldo); queda como hábito barato y monitor sin meta. Sale de las metas de la semana 1.
- 2026-11-07 noche · Opus: `draft.py` solo corre su CLI bajo `__main__` (para poder importarlo); el companion saca los nombres de campeón de `datos/raw` (sin red), y el rival sin rol conocido se resuelve mostrando todos los ya elegidos.
- 2026-11-07 noche · Opus: `revision.py` corre al importarse, así que se prueba como proceso (humo sobre `datos/raw`) en vez de reescribirlo; la prueba se salta si no hay datos.

## Para el usuario (cuando vuelva)
- Nuevo: deja abierto `python scripts/companion.py` en una terminal mientras juegas. En champ select te recomienda el pick contra tu rival y, al terminar, baja la partida y la revisa (si la key caducó, te dice «renueva RIOT_KEY»).
- Para revisar tus primeras muertes: `python scripts/partida.py <id> --early` (minuto a minuto del 1 al 12, con tu nivel contra el de tu rival).
- Yone contra Ekko: las dos muertes 1v1 (2:52 y 5:10) fueron yendo 1 nivel abajo desde el 3. En tus datos el problema no es tradear temprano, es quedar abajo de nivel al 6 (44% de WR).
- Control wards: no te obsesiones; en tus datos (y en los de los demás jugadores de tus partidas) no bajan los ganks. La regla 2 de la tarjeta ya no es prioridad.
- En champ select: `python scripts/draft.py <rival> [rol]` (p. ej. `draft.py Viktor mid`).
- Al terminar cada sesión: `python scripts/descargar.py` y luego `python scripts/revision.py` (o `revision.py 10`).
- Si la key caducó, `descargar.py` abre el portal de Riot: copia la key, `setx RIOT_KEY <key>` y córrelo otra vez (ya no hace falta reabrir la terminal).
- Opus no puede llamar a `ask-deepseek.ps1` (el permiso bloquea PowerShell anidado). Si quieres que lo use, permite ese comando.
