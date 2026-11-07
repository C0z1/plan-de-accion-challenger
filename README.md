# Plan de acción para llegar a Challenger

**Meta:** llegar a Challenger en LAN Solo/Duo lo antes posible y con el mejor win rate posible.

**Cuenta:** `cozi#1134` (LAN) · [OP.GG](https://www.op.gg/summoners/lan/cozi-1134) · [League of Graphs](https://www.leagueofgraphs.com/summoner/lan/cozi-1134)

## Punto de partida (2026-11-07)

| Dato | Valor |
|---|---|
| Rango actual | Master 15 LP |
| Pico | Master 346 LP |
| Temporada S2026 | 185W 156L (341 partidas, 54% WR) |
| Últimas 20 partidas | 40% WR (bajó 14 puntos) |
| Ladder | #8,907 (top 1.12%) |
| Temporada anterior | Gold 3 (S2025) |
| Clases | Mago 60%, Tirador 24%, Luchador 11% |
| Campeones (maestría) | Ekko, Sylas, Yasuo, Yone |
| KDA / KP promedio | 2.35 / 46% |

Fuente: OP.GG. Los datos de cada partida y el WR por campeón están pendientes.

## Cómo se usa

El agente `coach-challenger` (`.claude/agents/coach-challenger.md`) se encarga de planear todo: diagnóstico, plan semanal y seguimiento. Abre Claude Code en esta carpeta y pídele algo como:

> Usa el agente coach-challenger para hacer el diagnóstico inicial.

## Estructura

- `datos/`: snapshots del perfil y notas de partidas
- `PLAN.md`: plan de acción vigente (lo escribe el agente)
- `BITACORA.md`: registro de sesiones, LP y lecciones
