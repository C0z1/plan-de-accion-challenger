# Revisión En vivo: salud.py, dev_practica.py y T6-T9 (D-e)

DeepSeek (Sonnet de reemplazo), 2026-11-11. Solo lectura del código; no se corrió `salud.py` contra la app. Pruebas puras en `scripts/test_ds_salud.py` (25, 2 `expectedFailure` que documentan los hallazgos 1 y 3). Gravedad: A = puede dañar al usuario o dar un resultado engañoso en la prueba real, M = falso positivo o negativo de la medición, B = menor.

## Hallazgos

| # | Gravedad | Archivo:línea | Qué pasa | Sugerencia |
|---|---|---|---|---|
| 1 | A | `scripts/dev_practica.py:20` | `salir` hace `POST /lol-gameflow/v1/early-exit` sin mirar la fase ni el modo. Si el usuario lo corre por error durante una partida real (normal o ranked), abandona esa partida: aviso de abandono y penalización. El docstring promete «se niega fuera de None/Lobby», pero `salir` se salta ese candado. | Antes de escribir, leer `gameflow-session` y exigir `gameData.queue`/modo `PRACTICETOOL` (o la fase `InProgress` con el modo de práctica); si no, negarse. Agregar la prueba a `test_dev_practica.py`. |
| 2 | M | `scripts/salud.py:34` y `:203` (el mismo cálculo en `evaluar`) | `jugando` es True cuando el LCU da `None` y la fase de Racha es `None`. La fase de Racha pasa a `None` cuando el cliente de LoL se cierra (`companion_gui.trabajador` manda `None`), también sin partida. Entonces S3 queda en AVISO 120 s y luego FALLA para siempre (`vivo` `None`), y S5/S6 cambian de rama. Es falso positivo cada vez que se deja `salud --cada` corriendo con LoL cerrado. | Exigir además `meta` fresca (`recibido` < 30 s) para contar «jugando» cuando el LCU es `None`, o responder S3 solo si el puerto 2999 respondió alguna vez en esta partida. Prueba: `test_falso_positivo_fase_none_en_racha_y_cliente_cerrado_no_es_partida` (hoy `expectedFailure`). |
| 3 | M | `scripts/salud.py:46` y `:60` | Con la partida en curso y `franja_debe` False (por ejemplo meta de más de 30 s), no se evalúa ni S5 ni S6: `elif not jugando` solo corre fuera de partida. El plan pide S6 FALLA si la franja está visible con meta de más de 30 s. Falso negativo exactamente en el caso D3. | Cambiar a `elif not debe:` (franja visible sin que deba verse es FALLA, esté o no la partida en curso). Prueba: `test_falso_negativo_franja_visible_con_meta_de_mas_de_30_s_en_partida`. |
| 4 | M | `scripts/salud.py:33` y `:201-202` | El reintento de S2 nunca puede detectar nada: `pasada` reemplaza `e["json"]` por la segunda lectura de Racha y `fase_reintento` sale de esa misma lectura, así que `fase == fase_reintento` siempre y S2 no llega a FALLA salvo que Racha deje de responder. No hay prueba que lo cubra porque `evaluar` solo ve el resultado. | Tras la espera de 7 s, volver a pedir la fase al LCU y comparar contra la fase de Racha de la segunda lectura. |
| 5 | B | `scripts/salud.py:28` y `:30` | El umbral es 200 000 bytes pero el detalle muestra KiB (`round(bytes/1024, 1)`) contra «200»: 200 000 bytes se ven como 195,3 y FALLA a 200 001. Confunde al leer el log. | Mostrar `bytes / 1000` o fijar el umbral en 200 KiB (204 800). |
| 6 | B | `scripts/salud.py:64` | S7 da FALLA cuando Racha y el juego discrepan en pantalla completa, pero el plan solo define AVISO si es True. Si el usuario cambia `WindowMode` tras entrar a `ChampSelect`, sale FALLA aunque Racha funcione. | Dejarlo en AVISO si difieren, o documentarlo en el plan. |
| 7 | B | `scripts/salud.py:215` y `:216` | `mem["pid"]` se guarda una vez; si Racha se reinicia, `cpu_rss` devuelve `(None, None)` y S8 desaparece en silencio hasta reiniciar `salud`. | Si `cpu_rss` da `None`, olvidar `mem["pid"]`. |
| 8 | B | `scripts/salud.py:105`, `:122` | `rect` de la franja usa `GetWindowRect` del proceso consciente de DPI de `salud`, y la franja de Racha no lo es (D5). Los píxeles coinciden en `GetWindowRect` de otro proceso, pero `x = 0.22 * winfo_screenwidth` sigue usando la pantalla principal (D4/T10): la verificación de «otro monitor» se hará bien, el arreglo de posición no está hecho. | Sin cambio; confirmar en P1 con dos monitores. |
| 9 | B | `scripts/overlay.py:117-121` | El texto registrado es solo la última línea del traceback; dos errores distintos con el mismo mensaje se registran una vez. Además `registrar` escribe en `gui.REPO/datos/salud/franja.log` sin límite de tamaño. | Incluir la línea del archivo; rotar o limitar el log. |
| 10 | B | `scripts/overlay.py:107-109` | `visible` acepta fase `None` con meta fresca: tras cerrar LoL al terminar una partida, la franja sigue hasta 30 s. Es el compromiso buscado en D2; solo se anota. | Ninguna. |
| 11 | B | `scripts/replay.py:96` | `--validar` marca piezas de línea fuera de CLASSIC como fallo; con `PRACTICETOOL` y rival real (T6) un replay válido daría falso fallo. Hoy pasa porque la captura trae 1 jugador sin rival. | Aceptar también `PRACTICETOOL` en `replay.py:96`. |

## Endpoints LCU de `dev_practica.py`

| Método | Ruta | Cuándo | Notas |
|---|---|---|---|
| GET | `/lol-gameflow/v1/gameflow-phase` | siempre | Candado: solo `None` o `Lobby` (línea 14). |
| GET | `/lol-lobby/v2/lobby` | tras el candado | Si ya hay un lobby de otro modo en `Lobby`, el POST siguiente lo reemplaza (descarta un grupo que el usuario tuviera armado; no entra a cola). |
| POST | `/lol-lobby/v2/lobby` | si no hay lobby de práctica | Crea la Herramienta de práctica (queue 3140, mapa 11). |
| POST | `/lol-lobby/v1/lobby/custom/start-champ-select` | siempre | Lanza la selección. |
| GET | `/lol-champ-select/v1/session` | cada 2 s, hasta 60 veces | Lectura. |
| PATCH | `/lol-champ-select/v1/session/actions/{id}` | por cada `pick` propio sin completar | Elige y confirma el campeón de la práctica; no toca bans. |
| POST | `/lol-gameflow/v1/early-exit` | solo con `salir` | Sin candado de fase ni de modo: hallazgo 1. |

Nada pide cola, acepta partida ni banea. Esto se separa de lo que Riot pide declarar (`.equipo/deepseek-politica-overlay.md`: la LCU no está soportada, sin verificar si estos endpoints son aceptables). `companion.lcu_escribir` solo acepta POST/PUT/DELETE según su docstring, y aquí también envía PATCH (acepta cualquier método en `metodo`): conviene actualizar el docstring (`companion.py:33`).

## Diff T6-T9 (`git diff` de overlay, companion, companion_gui, companion_web)

- T6 `companion.py:156` — correcto. Otros usos de `grieta()` (`companion.py:209`, `:314`, `:367`, `:413`, `postpartida.py:120`) también activan sus reglas en Practice Tool; es el efecto buscado y no se ve riesgo, salvo el hallazgo 11.
- T7 `overlay.py:107-111` — `visible` exige `recibido` no `None`; la meta de una captura recargada (`companion_web.py:189`, `recibido` `None`) nunca se verá: correcto para la franja. Con `ajustes.overlay` en `False` se oculta; con `fase` `"None"` (cadena, cliente abierto sin partida) también. Aceptación del plan cumplida (tres casos probados en `test_ds_franja_vida.py`).
- T7 `overlay.py:131-132` — `partes` sigue usando `time.time()` y se llama aparte de `visible`; no hay doble lectura de `meta`. Sin hallazgo.
- T8 `overlay.py:117-121` y `companion_web.py:683-689` — registra una vez por texto; hallazgo 9. `except OSError: pass` en `registrar` es correcto (no tumba la franja).
- T9 `companion_gui.py:359` — correcto para `InProgress` → `Reconnect` → `InProgress` (probado en `test_d10_...`). Caso no cubierto: si el cliente se cierra durante `Reconnect` (`fase` `None`), `real` es `"Reconnect"`, `jugando` es False y se reinician archivo y avisos; es razonable (la partida pudo terminar).

## Falsos positivos probables para la prueba real (resumen)

1. S3/S5/S6 con LoL cerrado y Racha corriendo (hallazgo 2).
2. S2 nunca se activará (hallazgo 4): un 0 en S2 no prueba que las fases cuadren.
3. S6 no avisa de una franja visible con meta vieja en partida (hallazgo 3).
