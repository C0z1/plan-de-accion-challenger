# Pizarrón del equipo

> Contexto vivo del repo. **Léelo primero.** Cada agente edita **solo su sección** de "Ahora": la actualiza al empezar y al terminar cada turno. En "Hallazgos" y "Decisiones" solo se agregan renglones, no se borran.
> El detalle largo va en `datos/notas-equipo.md`. Aquí van solo líneas cortas.

## Meta
Llevar a `cozi#1134` (LAN) de **Master 15 LP a Challenger** (~1,750 LP). Para lograrlo hay que subir el WR de **54% a 60% o más** (ver `PLAN.md`).

## Ahora

### Opus · constructor
- **Estado:** iteración 10 terminada. `castigo.py`: con la línea perdida, ~77% de la XP de "muere él" es de kills con tu participación; 0 kills sobre tu rival → 40%, 1+ → 54%.
- **Siguiente:** lo que pida DeepSeek; si no, placas reales desde `TURRET_PLATE_DESTROYED` (sugerencia de DeepSeek) contra WR.
- **Actualizado:** 2026-11-07 10:20 (iteración 10, cierre)

### DeepSeek · revisor
- **Estado:** revisé bab24d7 (midgame.py) y b55f665 (rol.py). Correctos. n=1,678 verificado; causalidad de muertes 14–25 se mantiene aunque se debilita al cortar por oro al 20.
- **Siguiente:** revisar `scripts/convertir.py` (Ekko) cuando Opus lo commitee.
- **Actualizado:** 2026-11-07 06:15

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
| `datos/notas-equipo.md` | Detalle de cada turno y de cada revisión | Ambos (solo agregar) |
| `BITACORA.md` | Sesiones jugadas por el usuario | DeepSeek |
| `PIZARRON.md` | Este pizarrón | Ambos (cada quien su sección) |

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
- 2026-11-07 · Opus: con la línea perdida, los minutos de muerte cuestan −760 de XP en V y en D; regresos y roams ~0. La brecha V/D (−529 vs −806) es 70% XP de matar al rival (+420 vs +226).
- 2026-11-07 · Opus: con la línea perdida, de la XP de "muere él" +325/+193 (V/D) es de kills contigo y +95/+31 sin ti. 0 kills tuyos sobre el rival antes del 14: 40% (28–53); 1+: 54% (44–64); 1+ en solitario: 59%.
- 2026-11-07 · Opus: contar el minuto siguiente a tu muerte como "muerto" casi no cambia xp.py (−786/−818 contra −759/−763).

## Decisiones
- 2026-11-07 · Configuración: Opus construye y hace los commits; DeepSeek-Pro revisa cada commit. Tope de DeepSeek: $5.
- 2026-11-07 · Opus: el pick se recomienda con un estimado encogido (M=10) hacia tu WR del campeón, no con el récord crudo contra el rival.
- 2026-11-07 · Opus: la meta del mid game baja a ≤ 2 muertes del 14 al 25 (también en revision.py) y queda como monitor. La regla nueva: no pelear si no hace falta antes de que salga un objetivo.
- 2026-11-07 · Opus: mid sigue siendo el rol principal; si toca top, Mordekaiser o Yone (no Sylas).
- 2026-11-07 · Opus: si esperas perder la línea, Yone antes que Ekko (aguanta ir abajo).
- 2026-11-07 · Opus: regla nueva en prioridad 1: si ya vas abajo, cuida el farm (bajo torre, no roamear a costa de oleadas) más que evitar muertes.
- 2026-11-07 · Opus: esa regla se precisa: abajo, lo que pesa es la XP; quedarse en rango de XP de cada oleada y no perder tiempo fuera de la línea.
- 2026-11-07 · Opus: se corrige la anterior con `xp.py`: el tiempo fuera de la línea no es donde se va la XP. Abajo: no morir otra vez y castigar al rival.
- 2026-11-07 · Opus: "castigar" se precisa con `castigo.py`: el kill en tu línea cuando el rival se pasa (pista), no el gank forzado con jungla.

## Para el usuario (cuando vuelva)
- En champ select: `python scripts/draft.py <rival> [rol]` (p. ej. `draft.py Viktor mid`).
- Al terminar cada sesión: `python scripts/descargar.py` y luego `python scripts/revision.py` (o `revision.py 10`).
- Opus no puede llamar a `ask-deepseek.ps1` (el permiso bloquea PowerShell anidado). Si quieres que lo use, permite ese comando.
