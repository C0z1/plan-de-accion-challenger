# Sonidos de Racha: propuesta y prototipos

Base: canvas Vino, `diseno-acuerdos.md`, `PLAN-ENPARTIDA.md`, `scripts/overlay.py`, `scripts/web/index.html`, `scripts/companion_web.py`.
Prototipos: `generar.py` (solo stdlib) escribe los `.wav` de esta carpeta. Todos: 44,1 kHz, mono, 16 bit, pico -12 dBFS, ataque y liberación en coseno (primera y última muestra en 0, sin clics). Verificado: 7 archivos, 45 a 760 ms, pico -12,0 dBFS.

## Punto de partida

- `PLAN-ENPARTIDA.md` descarta el sonido («solo como opción si la beta lo reclama») y `diseno-propuesta.md` dice «sin sonido por defecto». Se respeta: **el interruptor general «Sonidos» nace APAGADO** y el aviso en la franja tiene además su propio interruptor, también apagado.
- Tono: coach tranquilo. La paleta Vino en audio: senos suaves, registro medio-agudo, colas cortas, nada metálico ni percusivo.
- Fuera de partida (champ select, fin, ajustes) el sonido es de bajo riesgo. **En partida es lo delicado**: compite con el audio de LoL y con la voz del equipo.

## Paleta (7 sonidos)

La columna «Tipo» es el valor del interruptor del tipo una vez prendido el general; con el general apagado nada suena.

| Archivo | Momento | Duración | Carácter | Volumen* | Tipo por defecto |
|---|---|---|---|---|---|
| `listo.wav` | Champ select: llegó tu regla/build (`s.draft` pasa de nulo a datos) | 400 ms | dos notas ascendentes E5 a B5, seno + 15 % triángulo, ataque 14 ms, cola 210 ms | 60 % | ON |
| `fin.wav` | Fin de partida: línea final y 3 momentos clave listos | 760 ms | arpegio suave E5-G5-B5 con caída exponencial; el más cálido | 55 % | ON |
| `actualizado.wav` | Actualización descargada/instalada | 420 ms | quinta ascendente D5 a A5, seno suave | 60 % | ON |
| `enviado.wav` | Reporte enviado (`/api/reporte` ok) | 230 ms | dos toques agudos B5 a E6, el segundo con caída rápida | 50 % | ON |
| `clic.wav` | Interruptores de Ajustes | 45 ms | toque seco 1320 Hz con triángulo, ataque 5 ms | 40 % | ON (también es la confirmación al prender «Sonidos») |
| `aviso.wav` | Sale un aviso corto en la franja en partida | 150 ms | una gota A4 (440 Hz) con descenso de 3 %, seno puro, ataque 15 ms, sin armónicos | 25 % | **OFF** |
| `pico.wav` | Pico de poder del rival (`aviso_pico`) | 320 ms | A4 a E4 descendente, tono de «ojo», sin alarma | 25 % | **OFF** |

\* Relativo al volumen master del usuario (60 por defecto). Los WAV ya van a -12 dBFS: nunca se sube por encima.

- Los ascendentes son «listo/bueno» (listo, actualizado, enviado, fin); el descendente es «atención» (pico). `aviso` es una sola nota neutra: el texto ya da el significado.
- **Recomendación: fusionar `pico` en `aviso`.** El pico ya sale como aviso de la franja; dos sonidos en partida obligan a aprender un código. `pico.wav` queda como alternativa si la beta pide distinguirlo.
- Sin sonido de error: un error no debe asustar; se queda visual (pantalla Errores).

## Reglas

Generales
1. Todo opcional: general on/off, volumen y un interruptor por tipo.
2. **El sonido nunca es el único canal.** Cada evento ya tiene su aviso visual (banner, tarjeta, franja con glifos ▼ ! ✓). Quitar el sonido no quita información.
3. Solo eventos propios de Racha (lo que Racha calcula o hace). Nunca sonido por eventos del juego (kills, objetivos, hechizos, pelea): sería anunciar información de la partida y la política de Riot (nada que el jugador no vea) no lo permite. El sonido de la franja solo dice «apareció texto»; el dato ya salía de lo visible con Tab.
4. Máximo 1 sonido cada 2 s y nunca solapados; si coinciden gana el de mayor prioridad (fin > actualizado > listo > enviado > aviso > clic).
5. Callar mientras se escribe (`document.activeElement` es INPUT/TEXTAREA), salvo `clic`/`enviado`, que son consecuencia de la propia acción.
6. Con la ventana oculta o minimizada (`document.visibilityState !== "visible"`) solo suenan `fin` y `actualizado`.
7. «Reducir movimiento» no apaga el sonido (son cosas distintas), pero como el general nace apagado, quien tiene esa preferencia no oye nada sin pedirlo.

Franja en partida (`aviso`, `pico`): las más estrictas
1. OFF por defecto y con interruptor propio y advertencia: «Un tono suave cuando sale un aviso. Se suma al sonido del juego.»
2. Hereda los topes de F1: 1 aviso a la vez, ≥ 90 s entre avisos, ≤ 6 por partida. Suena exactamente cuando `franja_libre` dio verde y se escribió `franja`; nunca más.
3. **Nunca durante una pelea de equipo.** Racha no sabe si hay pelea (inferirlo sería leer contexto del juego), así que no se promete detectarla; la mitigación honesta es: pocos avisos por partida (tope 6), ventanas de aviso casi sin pelea fija (nivel 5–7 min, CS 10–11 min, muertes 14–25 min) y, como mejor opción, ofrecer el modo **«solo estando muerto»** (F4: el momento muerto es el único instante realmente seguro) como forma recomendada de activar el sonido.
4. Volumen 25 % del master, 150 ms: un golpecito, no una alerta.
5. **Distinguible de LoL**: el juego es denso entre 200 Hz y 4 kHz con transitorios rápidos y percusivos. `aviso.wav` es un seno puro de 440 Hz, ataque lento (15 ms), sin armónicos, un solo tiempo. Evitar campanas, bips de 1 kHz y dos tiempos rápidos (suenan a alarma del juego).
6. Redundante por diseño: el texto está 12 s en la franja con glifo. Quien no oiga no pierde nada.

## Ajustes (bloque «Sonidos» bajo «Reducir movimiento», estilo `tog`)

- Sonidos (general, OFF). Al prenderlo suena `clic.wav`: sirve de prueba y de gesto de usuario para el autoplay.
- Volumen 0 a 100 (60) y botón «Probar» (reproduce `listo.wav`).
- Por tipo: Champ select (`listo`), Al terminar (`fin`), Actualizaciones (`actualizado`), Reporte enviado (`enviado`), Clics (`clic`).
- Aviso en partida (`aviso`), aparte y siempre OFF hasta que el usuario lo prenda; no se enciende solo al activar «Sonidos». Sub-opción: «solo estando muerto».
- Ayuda: «Nada suena si no lo activas. Los avisos siempre se ven aunque no los oigas.»

## Notas de implementación (para Opus; sin cambios de código hechos)

### Archivos
Copiar los `.wav` a `scripts/web/sonidos/` (ya se sirve `scripts/web/`), unos 150 KB. `overlay.py` necesita ruta absoluta: `os.path.dirname(__file__)` + `web/sonidos/`. Comprobar que el empaquetado incluya la carpeta.

### Ajustes nuevos (`scripts/companion_gui.py`, `AJUSTES_DEF`, l.80)
Booleanos: `sonido` False, `sonido_listo` True, `sonido_fin` True, `sonido_actualizado` True, `sonido_enviado` True, `sonido_clic` True, `sonido_aviso` False, `sonido_aviso_muerto` False. Volumen: `sonido_vol` entero 0–100 (60), no booleano como `franja_pos`: añadir su validación en `guardar_ajuste` y casos en `test_ajustes.py`. Llegan solos a web y overlay por `ESTADO["ajustes"]` / `/api/estado`. El cliente de la web escribe por `ajuste(clave, on)` (`index.html` ~l.958); el volumen necesita una variante que envíe un número.

### Dónde dispara cada sonido

| Sonido | Dónde | Condición |
|---|---|---|
| `listo` | `scripts/web/index.html`, `tick()` (~l.1002) | `s.fase === "ChampSelect"` y `s.draft` pasa de nulo a datos; comparar con el valor anterior como ya se hace con `ultFase` |
| `fin` | `index.html`, `tick()` | aparece `s.fin` (o `s.revision` con momentos) cuando antes no había; el servidor lo crea en `companion_web.py`, manejador `tipo == "fin"` (~l.61) |
| `actualizado` | `index.html`, `tick()`, donde se pinta `s.nueva` (~l.1017) | `s.nueva.estado` pasa a instalada/lista; una vez, no en cada tick |
| `enviado` | `index.html`, `reportar()` (~l.848) | dentro de `if (r.ok)` |
| `clic` | `index.html`, `ajuste()`, `quieto()` y `autoarranque()` | al pulsar un interruptor (la pulsación es el gesto de usuario) |
| `aviso` / `pico` | `scripts/overlay.py`, `correr()` → `dibujar()` | cuando `pieza_aviso(...)` pasa de `None` a algo con un `aviso["franja"]` distinto del último sonado (variable junto a `ultimo`); `pico` se reconoce por la clave `pico:` si se separa |

El «ya sonó» vive en el cliente (variable del `tick` / de `dibujar`), no en el servidor: recargar o abrir la ventana no repite sonidos.

### Ventana (Edge): sin dependencias
Un objeto JS con `new Audio("/sonidos/listo.wav")` por sonido, `preload="auto"`, `volume = sonido_vol/100`; reutilizar el elemento con `currentTime = 0`. Llamar siempre `.play().catch(() => {})`. Crearlos solo si `ajustes.sonido` es true. WebAudio no aporta nada para sonidos tan cortos.
- **Autoplay de Edge**: `play()` rechaza con `NotAllowedError` hasta que hay un gesto del usuario en la página. Un clic cualquiera basta; prender «Sonidos» (suena `clic`) lo cumple. Sin gesto: tragar el error, sin reintentos en bucle. Si el lanzador abre Edge en modo app, se puede añadir `--autoplay-policy=no-user-gesture-required`, pero no depender de ello.

### Franja (tkinter): `winsound`
`winsound` es stdlib solo de Windows: importarlo dentro de la función de sonar con `try/except ImportError`, para que `test_aram.py`, `replay.py` y la CI de Ubuntu (que importan `overlay`) no se rompan. Llamada: `winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)`.
- **Sin `SND_ASYNC` bloquea el hilo de tkinter** (la franja se congela el tiempo del sonido). Con él vuelve al instante.
- `PlaySound` no tiene volumen. Opciones: reescalar el WAV con `wave`+`struct` según `sonido_vol` y guardarlo en `%TEMP%` (6 KB, se regenera si cambia el volumen), o decir en Ajustes que el volumen no afecta al aviso. La primera es mejor.
- Un solo sonido a la vez (el nuevo corta al anterior): coherente con «1 aviso a la vez».

### Trampas
- **LoL en pantalla completa exclusiva**: la franja no se ve (ya documentado en `overlay.py`) pero el sonido sí se oiría, un aviso sin texto. Condición: `visible[0] and aj.get("sonido") and aj.get("sonido_aviso") and aj.get("overlay", True)`.
- «Solo estando muerto» necesita el estado `isDead` propio del jugador (F4, sondeo 10 s); si F4 no está, no ofrecer la sub-opción.
- No sonar mientras se escribe en la ventana (el `tick()` ya sale temprano si hay INPUT/TEXTAREA activo; aplicar lo mismo al reproductor).
- Reproducir un WAV propio desde otro proceso no toca el juego; no usar hooks de audio ni capturar el audio de LoL.
- Accesibilidad: `aria-label` en interruptor y deslizador; los avisos siguen con `role="status"`.
- Pruebas: un test que abra cada `.wav` y compruebe 44100 Hz, mono, 16 bit, duración < 1 s y pico ≤ -10 dBFS; otro que con `sonido` OFF ninguna ruta llame a `play`/`PlaySound`.

## Orden sugerido
1. Ajustes + `clic`, `enviado`, `actualizado`, `listo`, `fin` en la ventana (valor alto, riesgo casi nulo), con el general apagado de fábrica.
2. Beta con todo apagado. Solo si alguien lo pide: `aviso` en la franja con las reglas de arriba.
3. No ampliar la paleta sin una razón de la beta.
