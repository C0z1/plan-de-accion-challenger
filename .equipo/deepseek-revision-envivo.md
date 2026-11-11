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

## Ronda 2: 7b6ad61, 60f6ff3 y 1002796 (A4)

DeepSeek (Sonnet de reemplazo), 2026-11-11. Lectura de los diffs y pruebas sueltas con fotos sintéticas; no se corrió `salud.py` ni nada contra el juego. Los hallazgos 1-4 de la ronda 1 quedaron arreglados en 7b6ad61 (comprobado en `scripts/test_ds_salud.py` y `scripts/dev_practica.py:21-24`).

### Hallazgos

| # | Gravedad | Archivo:línea | Qué pasa | Sugerencia |
|---|---|---|---|---|
| 12 | MEDIA | `scripts/companion.py:159-170` (`unir_eventos`), `scripts/companion_gui.py:354` | La guarda `t(previos) > t(d)` no basta para separar partidas: `foto` solo se vacía en `FIN` (`companion_gui.py:361`), no cuando la partida termina por otro camino (cliente cerrado, salir de la práctica, cancelar). Con una partida anterior más corta que el primer `gameTime` de la siguiente, los eventos viejos se mezclan en la nueva (probado: previos t=100 con un `ChampionKill`, nueva t=120: queda 1 evento ajeno). Ensucia dragones, alma y `muertes14`. | Poner `foto = None` cuando `jugando` pasa de True a False y la fase no es `Reconnect` (junto a `archivo = None`, línea 359), o exigir que `previos` tenga un `GameStart` con `EventTime` 0 y la misma lista de jugadores. |
| 13 | BAJA | `scripts/companion.py:166-168` | Dedupe por `(EventName, EventTime)`: dos eventos con la misma clave en `previos` (dos muertes en el mismo tick) se pierden si la nueva trae solo una (probado: previos [A, B] con la misma clave y nueva [GameStart, A] deja 1 evento). Sin reinicio no pasa nada, porque `d` ya trae ambos. | Incluir `VictimName`/`KillerName` en la clave, o quitar de `previos` solo los que la nueva repite las mismas veces. |
| 14 | BAJA | `scripts/companion.py:164` | «Sin reinicio no cambia nada» no es del todo cierto: la lista se vuelve a ordenar por `EventTime` y se reescribe en cada foto. Inocuo hoy; solo tenerlo en cuenta si algo depende del orden de la Live API. | Unir solo si `d` perdió eventos (menos que `previos`) o trae un `GameStart` con tiempo > 0. |
| 15 | BAJA | `scripts/companion_web.py:60-62` | La pausa compara `meta.t` con la meta anterior: con juego realmente colgado (mismo `gameTime` para siempre) la franja queda congelada y «fresca» (`recibido` se renueva cada 10 s), así que `visible()` no la oculta; solo S3 lo detecta. Además, al empezar la pausa el timer sube de golpe hasta 10 s (pasa de `recibido`+edad a edad 0). La meta ARAM no trae `t`, así que no hay pausa ahí (correcto: sin timers). | Aceptable; anotar en el plan. |
| 16 | BAJA | `scripts/overlay.py:160-168` | Con el mismo número de piezas se reusa `etiquetas`; si el dibujo anterior falló a la mitad del `else` (tras destruir y antes de crear todas), `ultimo[0]` conserva el valor viejo y el siguiente tick actualiza solo las etiquetas que existan: la franja queda incompleta hasta que cambie el número de piezas. Raro (tkinter casi nunca falla ahí) y la excepción sí se registra. | Poner `ultimo[0] = None` al entrar al `else`, antes de destruir. |
| 17 | BAJA | `scripts/salud.py:68` | `(d.get("edad_proceso") or 10 ** 6) >= ARRANQUE`: una edad de 0 s cuenta como proceso viejo (por el `or`); no importa en la práctica. Y la gracia de 180 s también se aplica si el proceso es el `HTC.exe` que acaba de reiniciar por una caída: tapa un bucle de caídas con AVISO. | Comparar con `is None`; cruzar con `grabacion`/`fase` si se quiere detectar reinicios. |
| 18 | BAJA | `scripts/dev_practica.py:21-24` | `reconectar` reutiliza el candado de modo de `salir` (`gameData.queue.gameMode == PRACTICETOOL` en `/lol-gameflow/v1/session`): bien. Si la sesión aún guarda la partida anterior (EndOfGame), podría tocar una práctica ya terminada; inocuo. No comprueba la fase. | Exigir además fase `InProgress` o `Reconnect`. |

### Sin hallazgo
- `unir_eventos` con `previos` None, sin `events`, o `d` None devuelve `d` sin cambios; no modifica `previos` (cubierto por `scripts/test_ds_eventos_pausa.py`).
- `salud.py:222-223` y `:227`: reintento de proceso al reiniciar Racha y vistas fuera de partida son correctos; con `--vistas` en una partida el chequeo S10 se omite en silencio (esperado).
- `overlay.colocar`/`rect_juego` (7b6ad61): solo lee la posición del juego con `FindWindowW`/`GetWindowRect`, sin enviar mensajes; si `ancho_franja` supera el 76 % del ancho se pega al margen izquierdo y puede seguir pisando el marcador (caso extremo, medido por S5).

### Endpoints LCU nuevos
`POST /lol-gameflow/v1/reconnect` (solo `reconectar`, con candado de modo) y `GET /lol-gameflow/v1/session` (lectura para el candado). Estado de política: sin verificar, igual que el resto (`deepseek-politica-overlay.md`).
