# Pizarrón del equipo

> Contexto vivo del repo. **Léelo primero.** Cada agente edita **solo su sección** de "Ahora": la actualiza al empezar y al terminar cada turno. En "Hallazgos" y "Decisiones" solo se agregan renglones, no se borran.
> El detalle largo va en `datos/notas-equipo.md`. Aquí van solo líneas cortas.

## Meta
Llevar a `cozi#1134` (LAN) de **Master 15 LP a Challenger** (~1,750 LP). Para lograrlo hay que subir el WR de **54% a 60% o más** (ver `PLAN.md`).

## Ahora

### Opus · constructor
- **Estado:** iteración 3 terminada. `scripts/revision.py` + `datos/analisis-revision-2026-11-07.md` + PLAN (revisión y diagnóstico de la racha).
- **Siguiente:** decisión mid vs top con datos, o mid game: qué pasa del 14 al 25 en derrotas con oro ≥ 0 (zona y número de enemigos).
- **Actualizado:** 2026-11-07 06:20 (iteración 3, cierre)

### DeepSeek · revisor
- **Estado:** esperando el primer commit de Opus.
- **Siguiente:** verificar los scripts y los números del commit.
- **Actualizado:** 2026-11-07 05:50

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
| `datos/notas-equipo.md` | Detalle de cada turno y de cada revisión | Ambos (solo agregar) |
| `BITACORA.md` | Sesiones jugadas por el usuario | DeepSeek |
| `PIZARRON.md` | Este pizarrón | Ambos (cada quien su sección) |

## Hallazgos (con datos)
- 2026-11-07 · DeepSeek: KP es 41% en victorias y en derrotas, así que no las separa. Lo que sí separa es muertes (5.8 vs 7.4) y oro contra el rival (+1313 vs −1566).

- 2026-11-07 · Opus: ningún ban tiene respaldo: 2 de 80 rivales quedan bajo el WR base y el azar da ~1.9.
- 2026-11-07 · Opus: Viktor mid 1-7 (Ekko 0-4); Diana mid 2-5 con −1322 de oro al 14.
- 2026-11-07 · Opus: la racha (35% en últimas 20) no es de línea: oro ≥ 0 al 14 en 60% (antes 45%), pero convierte 5 de 12 (42% vs 65%); 60% fuera del pool.

## Decisiones
- 2026-11-07 · Configuración: Opus construye y hace los commits; DeepSeek-Pro revisa cada commit. Tope de DeepSeek: $5.
- 2026-11-07 · Opus: el pick se recomienda con un estimado encogido (M=10) hacia tu WR del campeón, no con el récord crudo contra el rival.

## Para el usuario (cuando vuelva)
- En champ select: `python scripts/draft.py <rival> [rol]` (p. ej. `draft.py Viktor mid`).
- Al terminar cada sesión: `python scripts/descargar.py` y luego `python scripts/revision.py` (o `revision.py 10`).
- Opus no puede llamar a `ask-deepseek.ps1` (el permiso bloquea PowerShell anidado). Si quieres que lo use, permite ese comando.
