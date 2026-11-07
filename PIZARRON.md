# Pizarrón del equipo

> Contexto vivo del repo. **Léelo primero.** Cada agente edita **solo su sección** de "Ahora": la actualiza al empezar y al terminar cada turno. En "Hallazgos" y "Decisiones" solo se agregan renglones, no se borran.
> El detalle largo va en `datos/notas-equipo.md`. Aquí van solo líneas cortas.

## Meta
Llevar a `cozi#1134` (LAN) de **Master 15 LP a Challenger** (~1,750 LP). Para lograrlo hay que subir el WR de **54% a 60% o más** (ver `PLAN.md`).

## Ahora

### Opus · constructor
- **Estado:** iteración 5 terminada. `scripts/rol.py` (mid vs top) + chequeo de causalidad en `midgame.py` + PLAN (decisión de rol).
- **Siguiente:** por qué Ekko no convierte (gana la línea, 54% de WR), o lo que pida la revisión de DeepSeek.
- **Actualizado:** 2026-11-07 07:25 (iteración 5, cierre)

### DeepSeek · revisor
- **Estado:** revisé 59e6e88 (timeline), 7166539 (draft.py) y 59119ff (revision.py). Todo correcto, salvo detalles menores.
- **Siguiente:** revisar el análisis de derrotas con oro ≥ 0 al 14 (mid game).
- **Actualizado:** 2026-11-07 06:07

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
- 2026-11-07 · Opus: top 58% contra mid 54% es ruido (permutación p = 0.55). Top es bueno por Mordekaiser (68%); top sin Morde, 53%. Sylas top 4/11.
- 2026-11-07 · Opus: las muertes del 14 al 25 pesan aunque el equipo vaya bien: con línea y equipo ≥ 0 al 14, 0–2 muertes → 82% (69–90); 3+ → 57% (43–70).

## Decisiones
- 2026-11-07 · Configuración: Opus construye y hace los commits; DeepSeek-Pro revisa cada commit. Tope de DeepSeek: $5.
- 2026-11-07 · Opus: el pick se recomienda con un estimado encogido (M=10) hacia tu WR del campeón, no con el récord crudo contra el rival.
- 2026-11-07 · Opus: la meta del mid game baja a ≤ 2 muertes del 14 al 25 (también en revision.py) y queda como monitor. La regla nueva: no pelear si no hace falta antes de que salga un objetivo.
- 2026-11-07 · Opus: mid sigue siendo el rol principal; si toca top, Mordekaiser o Yone (no Sylas).

## Para el usuario (cuando vuelva)
- En champ select: `python scripts/draft.py <rival> [rol]` (p. ej. `draft.py Viktor mid`).
- Al terminar cada sesión: `python scripts/descargar.py` y luego `python scripts/revision.py` (o `revision.py 10`).
- Opus no puede llamar a `ask-deepseek.ps1` (el permiso bloquea PowerShell anidado). Si quieres que lo use, permite ese comando.
