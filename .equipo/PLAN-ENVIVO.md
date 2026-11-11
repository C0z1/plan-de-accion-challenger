# Plan En vivo: que la franja y las ventanas funcionen en partida (v0.14.x)

Hecho por Fable (planificador) el 2026-11-11, guardado por Opus. Complementa `PLAN-ENPARTIDA.md`. No agrega funciones: primero se mide con un chequeo de salud y luego se arregla solo lo que falle.

## 1. Diagnóstico

[C] = comprobado leyendo el código o las capturas. [S] = supuesto, se confirma en la prueba real.

| # | Qué puede fallar | Evidencia |
|---|---|---|
| D1 | [C] En Practice Tool la franja sale con el formato ARAM («Kills 0 vs 0 · Tu KDA»), sin dragón ni barón. | `companion.grieta()` solo acepta `CLASSIC`; la captura `20261109-173828.jsonl` trae `PRACTICETOOL`, mapa 11, 1 jugador, `position` `NONE`. |
| D2 | [C] Si el cliente de LoL se cierra a media partida, la franja se esconde aunque los datos sigan llegando. | `overlay.py:121` exige `fase == "InProgress"`. |
| D3 | [C] Si el puerto 2999 deja de responder con la fase aún `InProgress`, la franja sigue descontando timers con la foto vieja. | `overlay.partes` no limita `edad`; `meta` solo se limpia en `ChampSelect`. |
| D4 | [C] Con LoL en un segundo monitor o en modo ventana, la franja sale en el monitor principal. | `overlay.py:131` usa `winfo_screenwidth/height`. |
| D5 | [C] Ninguna llamada de DPI en `overlay.py`, `ventana.py` ni `companion_web.py`. [S] A 125–150 % el texto sale borroso. | grep sin resultados. |
| D6 | [C] `-topmost` se pone una vez y no se reafirma. [S] Puede quedar debajo del juego tras alt-tab. | `overlay.py:106,132`. |
| D7 | [C] Si la franja truena no queda rastro en ningún log. | `except Exception: pass` en `companion_web.py` y `overlay.py`. |
| D8 | [C] El aviso de pantalla completa solo se calcula al entrar a `ChampSelect`/`InProgress`. Aceptable. | `evento()`. |
| D9 | [C] La franja no tiene tope de ancho. [S] Con 4 piezas + aviso de 48 caracteres puede llegar al marcador en 1366/1600 px. | `overlay.py:103,131`. |
| D10 | [C] En `Reconnect` se reinician `avisado` y el archivo de captura: al volver, un aviso se repite y la grabación se parte. | `companion_gui.py:340,359`. |
| D11 | [S] 13 de los 15 `.jsonl` de `datos/vivo` tienen 1 línea; probablemente reinicios en desarrollo. | Verificar: 1 partida = 1 archivo. |
| D12 | [S] La cadena selección → carga → partida → fin → revisión no se ha visto de punta a punta en juego real desde la v0.11. | `index.html`. |
| D13 | [S] En vivo actualiza cada 10 s y no descuenta timers entre fotos; la franja sí. Aceptable. | `tick()`. |
| D14 | [S] CPU en partida con sondeo de 10 s sin medir; FPS sin medir. | — |
| D15 | [C] Un error de vista se pinta como «Esta vista falló: …»: se detecta leyendo el DOM. | `index.html`. |

## 2. Chequeo de salud (`scripts/salud.py`, solo stdlib + ctypes)

Recolectores con E/S y una función pura `evaluar(datos, ahora) -> [{id, nivel, medido, umbral, detalle}]` (OK, AVISO, FALLA). `python scripts/salud.py` hace una pasada y sale con 1 si hay FALLA; opciones `--cada N`, `--vistas`, `--foto`. Puerto de `datos/cache/htc.port`. Cadencia: 60 s en partida (S1–S6), 300 s fuera, `--vistas` cada 30 min y nunca en partida salvo en la prueba.

| ID | Qué mide | FALLA si… |
|---|---|---|
| S1 servidor | GET `/api/estado` | no responde 200 en 1 s, JSON inválido, falta `fase`/`meta`/`ajustes`/`v`, o pesa > 200 KB |
| S2 fase | `ESTADO.fase` contra el LCU | distintas tras reintentar a los 7 s |
| S3 Live API | `companion.vivo()` dos veces con 2 s | no responde tras 3 intentos, no te encuentra, o `gameTime` no avanza (en carga: AVISO) |
| S4 frescura | `ahora − meta.recibido` | > 25 s con S3 en OK |
| S5 franja en partida | `EnumWindows` «Racha franja» y la ventana del juego | no existe, invisible, colgada, sin TOPMOST/TRANSPARENT/NOACTIVATE, otro monitor, fuera del juego, ancho > 60 % o alto > 5 %, o pisa una zona prohibida |
| S6 franja fuera de partida | misma búsqueda | visible fuera de `InProgress` o con meta de más de 30 s |
| S7 pantalla completa | `companion.pantalla_completa()` | AVISO si es True en partida |
| S8 CPU y memoria | `GetProcessTimes` del dueño del puerto en 10 s | > 1 % de un núcleo dos pasadas seguidas, o RSS > 200 MB |
| S9 grabación | `.jsonl` más nuevo de `datos/vivo` | en partida de más de 60 s, última escritura > 45 s, o más de 1 archivo por partida |
| S10 vistas | Edge headless `--dump-dom` de las 9 vistas | «Esta vista falló» o «Sin conexión», `#main` < 50 caracteres, o > 8 s |

- Zonas prohibidas (fracciones del juego, se calibran con la primera captura): minimapa x > 0,80 e y > 0,70; marcador x > 0,78 e y < 0,06; HUD 0,28 < x < 0,72 e y > 0,85; chat x < 0,25 e y > 0,60.
- Una vez por build, Opus recorre las 9 vistas con Playwright y exige 0 `console.error` y 0 404 de `/img`.
- Log: una línea JSON por pasada en `datos/salud/salud.jsonl`; en FALLA, `datos/salud/fallo-<ts>.json` (estado sin `rendimiento`, `cuenta` ni `nube`) y con `--foto` un PNG. Tres fallas seguidas del mismo ID = `persistente`.
- Nunca arregla solo: no reinicia Racha, no mueve ventanas, no toca `game.cfg`.

## 3. Tareas (cada una ≤ 1 h)

Opus toca `scripts/*.py` salvo `test_ds_*`; DeepSeek toca `scripts/test_ds_*.py` y `.equipo/deepseek-*.md`.

| ID | Qué | Aceptación | Dueño |
|---|---|---|---|
| T1 | `salud.py` con S1–S4, S7–S9, `evaluar` pura, log, `--cada`; `datos/salud/` en `.gitignore` | Con demo sale 0 y escribe una línea; servidor muerto → 1 con S1 en FALLA | Opus |
| T2 | La franja se llama «Racha franja»; S5 y S6 por Win32 | S5 la encuentra en demo con `--overlay`; después S6 OK | Opus |
| T3 | `--vistas` (S10) y `--foto` | 9/9 vistas OK en demo | Opus |
| T4 | `scripts/dev_franja.py`: `overlay.correr` con `replay.repetir(<jsonl>)` a 10× | Se ven todas las fases y un aviso sobre el escritorio | Opus |
| T5 | `scripts/dev_practica.py`: lobby de Practice Tool por LCU; se niega fuera de `None`/`Lobby`; `--seco` | La fase llega a `ChampSelect` con `PRACTICETOOL` | Opus |
| P1 | Primera prueba real (sección 4) → `datos/salud/prueba-1.md` | Tabla pasa/falla con capturas | Opus |
| T6 | D1: `grieta()` acepta `PRACTICETOOL` | La foto `20261109-173828` da Dragón y Barón; replay 0 fallos | Opus |
| T7 | D2 + D3: `overlay.visible(s, ahora)` (overlay prendido, meta < 30 s, fase `InProgress` o `None`) | Cliente cerrado con meta fresca → visible; meta de 31 s → oculta; `EndOfGame` → oculta | Opus |
| T8 | D7: errores de la franja una vez por texto a `datos/salud/franja.log` | Un `leer()` que lanza deja 1 línea y la franja sigue | Opus |
| T9 | D10: `Reconnect` no reinicia `avisado` ni `archivo` | `InProgress` → `Reconnect` → `InProgress`: 1 archivo, sin aviso repetido | Opus |
| T10 | D4: posición relativa a la ventana del juego (D5 solo si P1 lo muestra) | Prueba pura con el juego en (1920, 0, 2560×1440) | Opus |
| T11 | Solo si P1 lo muestra (D6): reafirmar topmost cada 5 s sobre la franja | Tras alt-tab, S5 OK en ≤ 10 s | Opus |
| T12 | Solo si P1 o D-c lo muestran (D9): que no pise el marcador | S5 sin zonas prohibidas a 1366, 1920 y 2560 | Opus |
| T13 | Segunda prueba real + rebuild + humo + `salud.py --vistas` contra el `.exe` → `prueba-2.md` | Todo OK o AVISO justificado; release solo con permiso | Opus |
| D-a | Pruebas de borde de `salud.evaluar` (tras T1) en `scripts/test_ds_salud.py` | ≥ 12 pruebas sin red ni Win32 | DeepSeek |
| D-b | `expectedFailure` de D1, D2, D3 y D10 en `scripts/test_ds_franja_vida.py` | Fallan hoy por la razón escrita | DeepSeek |
| D-c | Tabla de anchos de la franja por fase → `.equipo/deepseek-anchos-franja.md` | Archivo, minuto y texto | DeepSeek |
| D-d | `replay.py --validar --precios` en las capturas → `.equipo/deepseek-replays-envivo.md` | 0 fallos o lista | DeepSeek |
| D-e | Revisión escrita de `salud.py`, `dev_practica.py` y diffs T6–T12 → `.equipo/deepseek-revision-envivo.md` | Hallazgos con archivo:línea | DeepSeek |
| D-f | «Qué mirar al llegar» (≤ 15 renglones) y nota de política de overlays → `.equipo/deepseek-al-llegar.md`, `.equipo/deepseek-politica-overlay.md` | Entregados | DeepSeek |

## 4. Protocolo de prueba real (Practice Tool)

1 jugador, sin rival de línea; Opus no manda entradas al juego. Se prueban ventana, posición, transiciones, timers, frescura y CPU; línea, muerte y avisos con `dev_franja.py` sobre el juego real.

1. Antes: Racha corriendo, `salud.py --vistas` OK; anotar `WindowMode`, resolución, escala y monitores.
2. Lanzar con `dev_practica.py`.
3. Durante: `salud.py --cada 60 --foto`; capturas en selección, carga, 0:30, 2:00, 5:00, franja abajo, overlay apagado/prendido y `dev_franja` en su peor ancho.
4. Pasa si: sin franja en carga; aparece ≤ 15 s tras `gameTime` > 0; S5 OK y no tapa minimapa, marcador ni HUD; Dragón ±2 s; En vivo coincide; S8 < 1 %; 1 solo `.jsonl` con una línea cada 30 s.
5. Cierre del juego (máx. 25 min, máx. 3 partidas): la franja se oculta en ≤ 30 s, la fase cambia, sin «Error», `salud` vuelve a OK.
6. Resultado en `datos/salud/prueba-N.md`. FPS con y sin franja lo mide el usuario.

## 5. Riesgos y qué NO hacer

- Vanguard: la franja es una ventana normal siempre-encima, sin inyección. No leer memoria, no mandar entradas ni mover la ventana del juego, no hooks de teclado, no editar `game.cfg`.
- Riot: solo Live Client Data de lo que se ve con Tab; avisos cortos sin órdenes; ≤ 4 piezas + 1 aviso; sin sonido por defecto.
- LCU de escritura: solo en `dev_practica.py` (no se distribuye) y solo Practice Tool. Nunca colas ranked/normales, aceptar partida ni pick/ban desde Racha.
- El chequeo no cura; nada de `datos/` se sube ni se manda crudo a DeepSeek.
- No hacer: piezas nuevas, watchdog que reinicie Racha, dependencias nuevas, release o push sin permiso, emojis en docs públicas.
