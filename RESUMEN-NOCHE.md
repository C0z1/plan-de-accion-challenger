# Resumen de la noche · 2026-11-07 (05:42 → 06:58)

## Cómo fue
- **Opus (constructor):** 17 iteraciones completas; la 18 se cortó por el límite del plan (06:47). Costo equivalente ≈ $16.5.
- **DeepSeek (revisor):** 6 revisiones de commits. Saldo $9.83 → $8.90 (**$0.93**; tope era $5).
- **Commits:** 17, de `59e6e88` (timeline) a `e5ce83e` (early por campeón), más este de cierre.
- Registro completo: `C:\Users\felix\noche-challenger\estado.log`. Detalle por turno: `datos/notas-equipo.md`.

## Lo que cambió en el PLAN (para jugar)
1. **Oro al 14 es la palanca:** de −1000 a +1000 pasas de 41% a 72% de WR.
2. **Si vas abajo, pesa la XP, no el CS** (a igual oro: 65% contra 27%). La XP se pierde en los minutos muerto. Regla: **no morir otra vez y castigar al rival cuando se pase en tu línea** (no el gank forzado con jungla).
3. **Ventaja de nivel en top/bot:** no pases el río sin ver al jungla rival (×1.89 de muertes). En mid queda la regla general: no seguir al rival a su jungla.
4. **Sylas:** > 68 minions al 10 → 74%; ≤ 68 → 32%. No tradear ni roamear a costa de oleadas antes del 10.
5. **Mid game:** 3+ muertes del 14 al 25 → ~50% (0–2 → 74%). No pelees antes de un objetivo si no hace falta.
6. **Pool:** mid Yone (principal) y Ekko; si esperas perder la línea, Yone. Top: Mordekaiser. Sylas solo con matchup claro.

## Descartado (los datos no lo apoyan)
- Bans: ninguno tiene respaldo (2 rivales bajo tu WR contra ~1.7 por azar).
- Regla de placas ("no irte a base con la oleada entrando"): quitada.
- `turretPlatesTaken`: no mide tus placas; fuera del PLAN y de `revision.py`.
- El farm perdido no depende del matchup (p = 0.30).

## Tu rutina
- Champ select: `python scripts/draft.py <rival> [rol]`
- Al terminar la sesión: `python scripts/descargar.py` y `python scripts/revision.py` (o `revision.py 10`).

## Pendiente para la próxima noche
- Meter "minions @10 con Sylas" como meta en `revision.py`.
- La prioridad 1 del PLAN es muy larga: sacar una tarjeta corta de reglas para tener a la mano en partida.
- Opus no puede llamar a `ask-deepseek.ps1` (el permiso bloquea PowerShell anidado).
