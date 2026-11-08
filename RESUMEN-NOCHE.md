# Turno 3 · 2026-11-08 00:25

## Qué se construyó
- **Funciona para cualquier cuenta:** `DATOS_DIR` en todos los scripts, partidas de cualquier región (`*_*.json`), pool y meta de minions desde `config.json` opcional (el tuyo ya está; ejemplo en `config.ejemplo.json`). Sin config, el pool son tus 3 más jugados. Probado de punta a punta con JUGKING#1345 (Challenger LAN) en carpeta aparte; datos de prueba borrados.
- **Referencias de `revision.py` calculadas de tus partidas** (no números fijos); `convertir.py`/`linea.py` enfocan tu campeón más jugado; `rol.py` compara tus 2 roles más jugados y elige el campeón del 2.º rol por WR encogido (Mordekaiser para ti).
- **CI** (`.github/workflows/pruebas.yml`, Ubuntu y Windows): las pruebas ya corren sin `datos/raw` (antes el CI habría salido rojo). 19 pruebas OK.
- **`companion.py --help`** y README del companion; **captura en vivo** con la Live Client Data API cada 30 s durante la partida en `datos/vivo/` (solo tu PC).

## Qué se descubrió
- En las últimas 5 partidas llegaste al 14 con oro < 0 en las 5 (media −786, CS −11) y aun así ganaste 3; 2 fueron fuera del pool. n=5: pista.
- Ninguna ✅/❌ de `revision.py 20` cambió al calcular las referencias de tus datos: las metas del plan siguen igual.

## Cómo usarlo en tu próxima partida
1. Deja abierto `python scripts/companion.py` (reinícialo para tomar la captura en vivo). En champ select te recomienda pick contra tu rival; al terminar baja y revisa la partida.
2. Prioridad en línea: no salir del 6 con nivel abajo, y con Sylas 69+ minions al 10.

## Antes del push (pendiente tuyo)
- `git rm -r --cached scripts/__pycache__` y commit: los `.pyc` rastreados traen tu ruta `C:\Users\…` (Opus no tiene `git rm`).
- El historial viejo aún trae tu ruta y el saldo de DeepSeek; no hay keys. Reescríbelo solo si te importa.

## Qué sigue
- Juntar varias partidas en `datos/vivo/` y analizarlas (oro contra el rival minuto a minuto con ítems).
- Probar el companion en un champ select real.

# Turno 2 · 2026-11-07 23:30

## Qué se construyó
- **`scripts/companion.py`**: un solo proceso que lee el cliente de LoL (solo GET, nunca toca acciones). En champ select corre `draft.py` contra **tu rival de línea** (si hay roles, espera a que lo elija en vez de recomendar contra el jungla). Al terminar la partida espera 60 s y corre `descargar.py 5` + `revision.py 1`. Cliente cerrado: espera sin fallar. Probado en vivo en `Lobby` y `EndOfGame`.
- **`descargar.py` más robusto**: con key caducada (401/403) abre developer.riotgames.com y te dice que la renueves; lee `RIOT_KEY` del proceso o de tu variable de usuario de Windows; reintenta 5xx y cortes; escribe a `.tmp` y renombra; un 404 de partida recién terminada ya no rompe la corrida.
- **17 pruebas sin red** (`python -m unittest discover scripts`): companion con fixtures, draft (incluida una que prueba que el encogimiento cambia la recomendación) y humo de revision.
- Análisis nuevos: `muertes6.py`, `wards.py`, `partida.py --early` (narra 0–12), meta de Sylas (69+ minions al 10) en `revision.py`.

## Qué se descubrió
- Morir antes del 6 no baja el WR por sí solo (59% contra 50%); ir **abajo de nivel al 6** sí apunta (44%).
- Control wards antes del 14 no bajan los ganks ni suben el WR en 1,431 jugadores de línea: quedó como hábito, no regla.
- El companion manejó bien su primer uso real: Riot aún no publicaba la partida (404) y avisó sin revisar la anterior.

## Cómo usarlo en tu próxima partida
1. Abre el cliente y corre `python scripts/companion.py` en una terminal; déjalo abierto.
2. En champ select te imprime la recomendación cuando aparece tu rival.
3. Al terminar, descarga y revisa solo. Si dice «renueva RIOT_KEY»: copia la key nueva del portal en tu variable de usuario y vuelve a correrlo.

## Qué sigue
- Probar el companion en un champ select real (solo se probó con fixtures, Lobby y EndOfGame).
- Bajar la partida del último `EndOfGame` cuando Riot la publique: `descargar.py 5` + `revision.py 1`.
- `companion.py` no acepta `--help`: cualquier argumento distinto de `--fixture` arranca el modo en vivo.
- Opcional: captura en vivo con la Live Client Data API (no se hizo).

# Resumen de la noche · 2026-11-07 (05:42 → 06:58)

## Cómo fue
- **Opus (constructor):** 17 iteraciones completas; la 18 se cortó por el límite del plan (06:47). Costo equivalente ≈ $16.5.
- **DeepSeek (revisor):** 6 revisiones de commits.
- **Commits:** 17, de `59e6e88` (timeline) a `e5ce83e` (early por campeón), más este de cierre.
- Registro completo: `estado.log` del turno nocturno (fuera del repo). Detalle por turno: `datos/notas-equipo.md`.

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
