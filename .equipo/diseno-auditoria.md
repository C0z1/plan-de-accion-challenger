# Auditoría de la GUI del companion (`scripts/companion_gui.py`)

Hecha leyendo el código (no se ejecutó la ventana). Las líneas citadas son de `companion_gui.py`. Lo que no pude verificar sin verla corriendo va marcado «sin verificar».

## 1. Qué hay hoy

Una ventana tkinter normal de 420×760 (mínimo 380×560), fondo oscuro, una columna de tarjetas. Estructura fija:

- **Cabecera:** logo «PC», título, perfil (`cozi#1134 · Master 15 LP`, 8 pt) y una píldora con la fase.
- **Banner de aviso** (naranja, 9 pt negrita), oculto hasta que llega un aviso; se inserta bajo la cabecera.
- **Cuerpo:** tarjetas que se reemplazan por completo en cada evento.
- **Pie:** «Solo lectura…» y «key ok / falta RIOT_KEY» (se calcula una vez al abrir).

| Fase | Qué se ve hoy |
|---|---|
| Cliente cerrado / sin actividad | Texto de espera + tarjeta fija «Reglas para esta partida» (3 reglas de la tarjeta) |
| Champ select, rival sin elegir | «espero a que tu rival de línea elija» + reglas |
| Champ select, rival elegido | Tarjeta rival (nombre, nº de partidas, tu WR contra él, oro al 14) → tarjeta Recomendación (pick en 22 pt, hasta 4 filas con barra) → nota de 8 pt → avisos en rojo → reglas |
| Champ select, rol desconocido | Una fila por rival con su mejor pick, sin explicación |
| En partida | «guardo una foto en vivo cada 30 s» + reglas. Los avisos (nivel 5–7, minions al 10) caen en el banner |
| Fin de partida | «Esperando a que Riot publique la partida…» (≥ 60 s, hasta ~7 min) → tarjeta de revisión: V/D, KDA, 4 metas con ✓/✕, racha de oro, detalle |

## 2. Problemas, ordenados por impacto en partida

### Críticos (afectan lo que ves jugando)

1. **La ventana no está pensada para verse mientras juegas.** No hay `-topmost`, ni modo compacto, ni transparencia (no aparece en el código). Con LoL en pantalla completa o ventana sin bordes encima, el companion queda detrás: el pick de draft y los avisos en vivo no se ven salvo que tengas segundo monitor. Sin verificar cómo lo usa el usuario hoy (¿segundo monitor?).
2. **Los avisos en vivo son un banner de 9 pt, sin sonido y sin caducidad.** (l.149, 254) Para algo que debe leerse en 2 s en medio de una pelea de línea: texto pequeño, un solo estilo para todo, y no desaparece (solo se oculta al volver a Lobby/Matchmaking/ReadyCheck, l.250). Un aviso del minuto 6 sigue ahí en el minuto 30 y en la pantalla de post-partida.
3. **Un aviso pisa al anterior.** (l.254) `config` reemplaza el texto: si salta «nivel abajo» y luego «minions al 10», el primero se pierde sin dejar rastro. Tampoco hay urgencia ni diferencia entre aviso accionable y error.
4. **Los errores comparten el banner de los avisos.** (l.127, 254) Un `Error: …` de Python sale del mismo naranja que «no tradees», y el jugador no sabe si es consejo o fallo.
5. **La pantalla «En partida» es relleno.** (l.249) Dice lo que hace el programa (guarda fotos), no lo que le sirve al jugador, y repite las mismas 3 reglas estáticas que en cualquier otra fase. Lo único útil in-game (la meta de la fase: CS al 10, nivel al 6, oro al 14) no se muestra.

### Altos (champ select)

6. **La advertencia más importante va al fondo.** (l.218) Los avisos del pick («counter duro», «pocas partidas») salen después de 4 filas con barras y una nota de 8 pt. Si el aviso cambia la decisión, debería ir pegado al pick, no debajo.
7. **Con la ventana de 760 px el cuerpo puede cortarse.** Rival + recomendación (4 filas) + reglas suman más que el alto útil (sin scroll, sin verificar con DPI alto). Las reglas, que sobran, empujan.
8. **Información que falta para decidir:** el rol se muestra como `MIDDLE` en inglés (l.193), no hay build, no hay runas, no se ve qué banean/eligen los aliados, y la tarjeta del rival no dice cuántas partidas son pocas para fiarse (sí lo hace el aviso, pero lejos).
9. **Rol desconocido: muestra el mejor pick de cada rival sin decir por qué ni contra quién va qué** (l.186–191). Es una lista pelada.
10. **El flujo se bloquea tras la partida.** (l.92–104, 125) `post_partida` corre dentro del mismo hilo que sondea el cliente: duerme 60 s y hasta 3×120 s. Si el jugador pone cola de inmediato, el champ select de la siguiente partida no se detecta hasta que acaba la espera (hasta ~7 min). Es un problema de lógica, no de diseño, pero la pantalla de espera lo esconde: pide un hilo aparte (aviso para Opus).

### Medios (post-partida)

11. **La revisión no da veredicto ni contexto.** (l.222–240) Hay 4 casillas ✓/✕, pero ninguna frase tipo «perdiste por la línea» ni comparación con tus partidas recientes. No hay tendencia (solo la racha si existe) y tampoco aparece el score relativo al equipo que se está construyendo.
12. **El «Detalle» manda a la terminal.** (l.239–240) «Minuto a minuto: python scripts/partida.py --early» es un comando en una ventana; no se puede copiar con un clic ni abrir. O sale el dato, o sale un botón.
13. **Metas con valores crudos.** `m14`, `cw`, `oro`, `cs` son cadenas de la tabla de `revision.py` (parseadas por posición de columna, l.51); si la tabla cambia una columna, la GUI se rompe en silencio. Sin verificar que haya prueba para ese acoplamiento.
14. **Espera sin progreso.** «Reintento en 2 min…» no dice cuántos intentos quedan ni permite cancelar.

### Bajos (pulido)

15. **Tipografía:** etiquetas, perfil y pie en 8 pt, nota en 8 pt; los números grandes sí son legibles (16–22 pt). La jerarquía es buena en el draft, pobre en todo lo demás.
16. **Anchos fijos:** `wraplength=340/380` está escrito a mano; si se ensancha la ventana el texto no sigue (l.149, 176, 181).
17. **Idioma mezclado:** «champ select», «MIDDLE», «mid», «key ok».
18. **Estado de la key solo al abrir** (l.154): si el usuario hace `setx` con la ventana abierta, sigue diciendo «falta RIOT_KEY».
19. **Logo «PC» y perfil de 8 pt ocupan la franja más visible** para nada accionable.
20. **Colores:** bien elegidos (azul/naranja distinguibles en daltonismo, acento ámbar), pero se pensaron para una ventana de escritorio sobre fondo claro-oscuro; contra el cliente de LoL (azul oscuro y dorado) el ámbar `#F2B33D` se confunde con el dorado del cliente si la ventana flota encima (sin verificar).

## 3. Lo que ya funciona (conservar)

- Pick recomendado en 22 pt con su % a la derecha: se lee de un vistazo.
- Paleta azul/naranja (no rojo/verde) y fondo oscuro.
- Estados de espera claros: nunca queda en blanco.
- Solo lectura, y la separación lógica/ventana (`parsear_revision`, `recomendaciones`) permite rediseñar sin tocar la lógica.

## 4. Lo que el rediseño necesita de Opus (en una línea cada uno)

- Un hilo aparte para `post_partida` (problema 10).
- Avisos como objetos `{texto, tipo: consejo|error, minuto}` en vez de cadena, para poder apilarlos, caducarlos y colorearlos.
- `draft.datos_draft` ya devuelve `avisos`; falta que cada aviso diga si cambia la decisión (para subirlo sobre el pick).
- Cuando existan: builds de los top por campeón del pool y score relativo al equipo por partida (con las últimas N para la tendencia), como datos estructurados, no como texto de tabla.

## 5. Consulta a DeepSeek

Ver `.equipo/diseno-propuesta.md` (aún no escrita) y las notas del equipo; la crítica de esta auditoría está en `.equipo/notas-equipo.md`, sección Diseñador, iteración 1.

## 6. Revisión de la build: En vivo «Tu rival» y «Objetivos» (iteración 3 noche, 2026-11-09)

Contra `EnPartida_Vino.dc.html`, leyendo `scripts/web/index.html` (`envivo()`); sin ejecutar la app. Ordenado por impacto en partida.

1. **Marcador sin leyenda (alto).** `kills 12–8` y `torres 3–2` solo se distinguen por color (salvia = tú, rojo = rival). El artboard rotulaba cada número; con daltonismo o de reojo no se sabe cuál es cuál. Propuesta: prefijo «Tú» / «Rival» una vez (p. ej. «Tú 12 · 8 Rival»).
2. **El dato accionable va pequeño y a la derecha (alto).** «Dragón · en 2:10» y «Barón · en 3:40» son lo que decide una jugada, pero salen en 14 px, color `muted`, al borde. Propuesta: el tiempo en 17–18 px, `--acc2` cuando falten < 60 s y «vivo» en `--teal`.
3. **Color fuera de la paleta (medio).** `#FF8A8A` fijo en `va()`; el resto usa `--red`/`--teal` (acuerdo 13). Además los puntos de color de cada objetivo (rosa/salvia/gris) no significan nada y se leen como estado; quitarlos o usar un ícono por objetivo.
4. **Íconos de ítems sin nombre (medio).** `img("item", i, "item", "")` deja `alt=""`: sin tooltip ni lector, y si la imagen falla queda un hueco invisible (`visibility:hidden`). Poner el nombre en `alt`/`title` si el payload lo trae.
5. **«?» como dato ausente (bajo).** «nivel ?», «? CS»: mejor «—».
6. **Etiqueta de nivel (bien).** «1 nivel arriba» (rojo) / «abajo» (verde) lleva palabra, no solo color. Se queda.
7. **Jerarquía del aside (observación).** «Ahora» arriba está bien; la tarjeta de rival es más alta que la de objetivos aunque estos cambian más. Si falta espacio a 1440×1024, objetivos primero.

**Está bien:** regla activa arriba y grande, tags con símbolo (✓/✕/▲), y que ambas tarjetas desaparezcan al terminar.
