# Plan «día de la aprobación de Riot» (app 904596)

2026-11-13 · Plan de Fable, revisado por DeepSeek, decidido por Opus. Objetivo del usuario: que el día que Riot apruebe la key, Racha quede lo más ligera posible.

## 0. Antes de la aprobación (ya): una duda que decide todo

La key vive hoy como secreto del Worker (`backend/worker.js`), que hace de proxy para los amigos con código. Fable y DeepSeek no coinciden sobre si eso cabe en una Personal Key:

| | Postura |
|---|---|
| Fable | Aceptable: «developer or a small private community», con secreto en el backend, códigos de invitado y allowlist (`PERMITIDO`). |
| DeepSeek | No aceptable: una Personal Key no debe servir a terceros por un backend, aunque sean amigos; para eso, Production Key. |

Ninguno verificó la política vigente. **Decisión: preguntarle a Riot por la pestaña *Messages* de la app** antes de diseñar nada encima. En el mismo mensaje:

- Corregir la descripción: hoy dice «The key stays on my PC», pero la key vive en un backend privado (Cloudflare Worker) que nunca la entrega al cliente.
- Declarar los endpoints reales: account-v1, match-v5 (+ timeline), league-v4, **spectator-v5** (vista de los 10 jugadores) y **champion-mastery-v4** (`matchups.py`).
- Preguntar explícitamente: «¿Puede una Personal Key servir a un grupo privado de ~10 amigos a través de mi backend, o necesito Production?».

## 1. Escenarios

| | A · Personal Key | B · Production Key |
|---|---|---|
| Límite | 20/s y 100/2 min por región (el de hoy) | 500/10 s y 30.000/10 min por región |
| Caduca | No | No |
| Usuarios | Tú y un grupo chico privado | Público, con RSO |
| Exige | Nada más | Producto registrado, página pública, privacidad, borrado de datos, revisión más estricta (botón de runas y frases en partida incluidos) |
| Proxy del Worker para amigos | Depende de la respuesta de Riot (punto 0) | Sí |

Si Riot dice que el proxy necesita Production: pedirla. Mientras tanto, los amigos siguen con agregados ya calculados (builds y matchups en D1, que no gastan key) y pierden solo lo que llama a Riot en vivo (sus partidas, la vista de los 10 jugadores).

## 2. Lo más ligero

- **Dónde corre el rastreo:** en la PC del admin, con el Programador de tareas de Windows, de noche. Cero infraestructura nueva y la key no sale de la PC. `FILAS` ya reanuda si se corta.
  - No en un Cron Trigger del Worker: el plan gratis da ~10 ms de CPU y 50 subrequests por invocación, y cada timeline pesa ~900 KB.
  - GitHub Actions solo si la PC apagada estorba: la key sale a un tercero (hay que declararlo), jobs de 6 h como máximo y hay que persistir `FILAS`.
- **Frecuencia:** la tarea corre a diario, pero solo rastrea si `versions.json` de Data Dragon cambió hace 3 días o más (el día del parche aún no hay partidas), más un refresco a mitad de parche.
- **Qué se guarda:** solo agregados en D1 (`builds`, `matchups`), sin puuid ni nombres.
- **Qué se borra al terminar cada rastreo:** las filas `.jsonl` de parches viejos y `datos/meta/cache`. `datos/raw` (tus partidas) se queda.

## 3. Pasos el día de la aprobación, por prioridad

| # | Paso | Esfuerzo |
|---|---|---|
| 1 | Pegar la key nueva con `renovar-key.ps1` (la pone en el Worker y en Windows); después ya no hace falta renovarla cada 24 h | 5 min |
| 2 | Mensajes: `worker.js` «la key del servidor caducó» → «key revocada, avisa al admin»; quitar el comentario «dev key» de `builds.get` | 15 min |
| 3 | Límite por amigo en el proxy con `limite()` de `extra.js` (p. ej. 60 llamadas a Riot por amigo cada 2 min, solo en fallos de caché), con prueba | ~1 h |
| 4 | Tarea programada (`.ps1`): comprobar parche → `builds.py --ladder` → `--subir` → `matchups.py --pool` → limpieza | 1–2 h |
| 5 | Matchups fase 3: migración `003` con tabla `matchups` (`clave` «A|POS|B», `datos`, `ts`); rutas `/v1/(builds|matchups)` en `extra.js`; `--subir` y `bajar` en `matchups.py`; pruebas | 3–4 h |
| 6 | `RIOT_PAUSA` configurable en `builds.get` (1,2 s en A; ~0,05 s en B) | 15 min |
| 7 | GitHub Actions | 2–3 h, solo si hace falta |
| 8 | Production con RSO | días; solo si Riot la exige o si crece |

## 4. Riesgos

- **Revocación:** Riot puede revocar la key. La app ya degrada: los agregados siguen en D1 y en `builds.json`. Conservar `renovar-key.ps1` como plan B con dev key.
- **Volumen:** 100/2 min compartidas alcanzan para unos 5–10 amigos gracias a la caché. Por encima, Production.
- **Rastreo y amigos a la vez** comparten el límite: rastrear de madrugada.
- **Repo público:** la key nunca en el repo, en logs ni en Actions.
