# Trabajo en equipo: Opus + DeepSeek

**Lee `.equipo/PIZARRON.md` primero**: tiene la meta, el estado de cada agente, el mapa del repo y los hallazgos. Al empezar y al terminar cada turno, actualiza tu sección.

Dos sesiones de Claude Code trabajan en esta carpeta. Cada una es dueña de sus archivos; no edites los de la otra.

| | Opus (construye y decide) | DeepSeek (asistente barato) |
|---|---|---|
| Dueño de | `scripts/`, `.equipo/PLAN.md`, `.claude/`, `datos/analisis-*.md` y todo lo demás | `.equipo/BITACORA.md`, `.equipo/deepseek-*.md` |
| Hace | Análisis nuevos (timeline, matchups), cambios al plan, decisiones | Correr `scripts/descargar.py` y `scripts/analizar.py`, registrar sesiones en la bitácora, resúmenes, dudas rápidas |

- Para pasarse trabajo: anota pedidos y hallazgos en `.equipo/notas-equipo.md` (fecha, quién, qué). Léelo al empezar.
- Opus, además, consulta a DeepSeek-Pro con `& $HOME\ask-deepseek.ps1` (ver CLAUDE.md global): manda resúmenes en `datos/*.md`, nunca los JSON de `datos/raw/` (son ~85 KB cada uno).
- La key de Riot está en la variable de entorno `RIOT_KEY`: nunca la escribas en archivos, logs ni commits, y nunca leas ni mandes `.env`.
- Solo Opus hace commits (nunca push).
