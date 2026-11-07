# Pizarrón del equipo

> Contexto vivo del repo. **Léelo primero.** Cada agente edita **solo su sección** de "Ahora": la actualiza al empezar y al terminar cada turno. En "Hallazgos" y "Decisiones" solo se agregan renglones, no se borran.
> El detalle largo va en `datos/notas-equipo.md`. Aquí van solo líneas cortas.

## Meta
Llevar a `cozi#1134` (LAN) de **Master 15 LP a Challenger** (~1,750 LP). Para lograrlo hay que subir el WR de **54% a 60% o más** (ver `PLAN.md`).

## Ahora

### Opus · constructor
- **Estado:** turno 1. Bajando los timelines (`scripts/descargar.py`) y armando `scripts/timeline.py`.
- **Siguiente:** analizar muertes y oro a los 10, 14 y 20 min; después, PLAN v2.
- **Actualizado:** 2026-11-07 05:50

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
| `datos/notas-equipo.md` | Detalle de cada turno y de cada revisión | Ambos (solo agregar) |
| `BITACORA.md` | Sesiones jugadas por el usuario | DeepSeek |
| `PIZARRON.md` | Este pizarrón | Ambos (cada quien su sección) |

## Hallazgos (con datos)
- 2026-11-07 · DeepSeek: KP es 41% en victorias y en derrotas, así que no las separa. Lo que sí separa es muertes (5.8 vs 7.4) y oro contra el rival (+1313 vs −1566).

## Decisiones
- 2026-11-07 · Configuración: Opus construye y hace los commits; DeepSeek-Pro revisa cada commit. Tope de DeepSeek: $5.

## Para el usuario (cuando vuelva)
- _(los agentes agregan aquí lo que necesiten de él)_
