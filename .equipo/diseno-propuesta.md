# Propuesta de rediseño del companion

Parte de `.equipo/diseno-auditoria.md` (los números entre paréntesis, p. ej. (#2), son los problemas de esa lista). Es una propuesta para hablarla, no un compromiso: nada de esto está construido. El mockup visual va aparte en `.equipo/diseno/mockup.html` (aún no hecho).

## 1. Principios

1. **Dos velocidades.** Champ select tiene ~30 s y se puede leer con calma; in-game se lee en 2 s o no se lee. Son dos diseños distintos, no uno solo.
2. **Una sola cosa grande por pantalla.** Draft: el pick. In-game: el aviso. Post-partida: el veredicto.
3. **La decisión arriba, la evidencia abajo.** El pick y su advertencia pegados; las 4 filas, la build y las reglas se despliegan o van debajo (#6).
4. **Nunca un número suelto.** Todo valor lleva su referencia (50 = tu rol, tu WR contra su WR, n de partidas).
5. **Solo lectura, sin sonido por defecto.** Se mantiene la promesa de la barra inferior.

## 2. Estructura general

Dos modos de la misma ventana, el cambio es automático por fase:

| Modo | Cuándo | Tamaño | Comportamiento |
|---|---|---|---|
| **Completo** | Champ select, post-partida, espera | 420×760, columna (como hoy) | Ventana normal |
| **Compacto** | En partida (`InProgress`) | franja ~360×110 anclable a una esquina | Siempre encima (`-topmost`), semitransparente, sin bordes, arrastrable |

Cabecera: se quita el logo «PC» y la línea de perfil sube al pie; la franja de arriba queda solo para la **píldora de fase** y el **estado de la key** (se re-evalúa cada minuto, #18). (#19)

Nota técnica: `-topmost` solo ayuda si LoL corre en **ventana sin bordes**; en pantalla completa exclusiva ninguna ventana flota encima. Es la primera pregunta (P1).

## 3. Pantallas

### 3.1 Champ select (completo)

Orden de arriba abajo:

1. **Rival de línea** (una línea): `Ahri · 6 partidas · tu WR 33% · oro al 14 −210`. Si son pocas partidas (< 5) lleva una etiqueta gris «pocas» al lado (#8).
2. **Tarjeta del pick** (la principal, borde ámbar):
   - Nombre del pick en 28 pt + su WR estimado a la derecha en mono.
   - Debajo, **inmediatamente**, la advertencia que cambia la decisión (si hay): píldora naranja «counter duro» o «pocas partidas». (#6)
   - Las otras 3 opciones: una línea cada una, barra fina, **colapsadas por defecto** («3 más ▾»).
3. **Build de los mejores** para el pick, formato de dos filas con iconos o iniciales:
   - Fila 1: `Rey Arruinado → Arcoescudo → Filo` (3 ítems core, flechas) + botas.
   - Fila 2: runa principal · orden de habilidades `Q > E > W` · n de partidas de los top (`12 partidas de Challenger`).
   - Mi WR con ese primer ítem frente al otro, en gris, con la n. Sin key: la tarjeta dice «sin datos de los top (key caducada)» en vez de desaparecer.
4. **Reglas**: una línea plegable al fondo («Reglas ▸»), cerradas por defecto. Hoy ocupan una tarjeta que empuja lo importante (#7).

Rol en español (`Mid`, `Top`, `Jungla`, `ADC`, `Support`) (#17). Rol desconocido: tabla de dos columnas `rival → tu mejor pick`, con un título que explique «no sé tu línea: te muestro el mejor pick contra cada rival» (#9).

### 3.2 En partida (compacto)

Una franja con **tres zonas**:

- **Izquierda:** la meta de la fase como mini-barra: `Min 7 · CS 52/70 · Nv 6 ✓`. Cambia con el reloj: CS al 10, nivel al 6, oro al 14. Datos: ya existen en la foto en vivo de 30 s.
- **Centro (solo cuando hay aviso):** el **banner de aviso** crece a 18–20 pt, ocupa la franja, texto máximo 6 palabras («Minions al 10: Sylas 74%», «Nivel 5: no tradees»), color de alto contraste sobre fondo oscuro.
- **Derecha:** el reloj de la partida en mono y un punto de estado (verde = leyendo bien).

Reglas de avisos (#2, #3, #4):
- Cada aviso es un objeto `{texto, tipo, minuto}`. Tipos: **consejo** (ámbar), **crítico** (naranja, parpadea una vez), **error** (gris con ícono ⚠, nunca en el color de los consejos).
- Caducan solos: consejo 20 s, crítico 30 s o hasta tocarlos, error 10 s. Se **apilan** (máx. 2 visibles; el más nuevo arriba); el pasado queda en un historial al pasar el ratón.
- Sin sonido por defecto; un tono suave opcional para «crítico».

### 3.3 Post-partida (completo)

Orden:

1. **Veredicto de una frase** en 20 pt: `Victoria · 24 min · Yone 8/2/9`, y debajo la causa más grande en palabras: «Línea: +340 de oro al 14» o «Perdiste por 3 muertes del 14 al 25». Calculada a partir de las metas (#11).
2. **Score relativo al equipo** (el dato nuevo):
   - Barra 0–100 horizontal con la marca de **50 = típico de tu rol** y tu score como punto (no número suelto).
   - Al lado: `puesto 2.º de 5 en tu equipo`.
   - **Tendencia:** sparkline de las últimas 20 partidas (score por bloques) con el valor medio. Texto: «Últimas 20: 49.2 · igual que antes».
3. **Qué te sube / qué te baja:** los 8 componentes como barras divergentes (izquierda rojo-naranja, derecha azul, 0 al centro), ordenadas por tamaño; solo los 3 más bajos arriba y «ver los 8 ▾». Idea de DeepSeek incorporada.
4. **Metas del plan:** las 4 casillas ✓/✕ de hoy (se conservan) en una fila de 4 chips en vez de 4 filas (ahorra alto).
5. **Por campeón** (una línea con el pick de la partida): `Yone: 57% WR · score 51 en 40 partidas`, siempre juntos (WR y score), porque el score no captura «ganar sin destacar» (Mordekaiser 68% WR con 47.5).
6. **Botón «Minuto a minuto»** que abre el análisis en una vista, o copia el comando con un clic (#12). Nada de texto que mande a la terminal.

### 3.4 Esperas y errores

- Espera de la partida publicada: barra de progreso con `intento 1 de 3 · próximo en 1:40` y botón «Cancelar» (#14).
- Cliente cerrado: una línea y el último resultado en pequeño (lo que se vio al cerrar), no una pantalla vacía.
- Los errores van en una **tira propia al pie** (gris, ícono ⚠, texto + «copiar»), jamás en el banner de avisos (#4).

## 4. Jerarquía tipográfica

Una familia sans (Segoe UI, ya en uso) y Consolas para números. Mínimo **10 pt** en la ventana completa, **14 pt** en la franja compacta.

| Nivel | Uso | Tamaño |
|---|---|---|
| Héroe | Pick (draft), aviso (in-game), veredicto (post) | 28 / 20 / 20 pt, negrita |
| Dato | Valores en mono: WR, score, oro | 16 pt |
| Cuerpo | Filas, reglas, build | 11 pt |
| Etiqueta | Títulos de tarjeta en mayúsculas | 9 pt, negrita, espaciado |
| Nota | Aclaraciones | 9 pt (hoy 8; nada baja de 9) |

## 5. Colores (que se lean sobre el cliente de LoL)

El cliente es azul marino profundo con dorado. El ámbar actual (`#F2B33D`) se confunde con ese dorado si la ventana flota encima. Propuesta:

| Rol | Hoy | Propuesto | Por qué |
|---|---|---|---|
| Fondo ventana | `#0E1015` | `#0B0E14` con 92% opacidad en compacto | Más negro que el azul del cliente: se separa |
| Panel | `#171A21` | `#151A24` | |
| Acento principal (pick, fase activa) | ámbar `#F2B33D` | **cian `#4FD1C5`** | No compite con el dorado del cliente |
| Bien / a favor | azul `#7DB8FF` | azul `#6AA9FF` | Se mantiene azul (no rojo/verde, daltonismo) |
| Mal / aviso | naranja `#F59E5B` | naranja `#FF8A3D` | Más saturado, se lee en 2 s |
| Error | (naranja) | gris `#8A93A3` + ⚠ | Distinto de un consejo |
| Texto / atenuado | `#E8EAF0` / `#9AA3B2` | igual | |

Regla: **nunca solo el color** — cada estado lleva también ícono o palabra (✓ ✕ ⚠ ▲ ▼).

## 6. Datos que necesita cada pantalla

| Pantalla | Dato | Estado hoy |
|---|---|---|
| Draft | rival, `vs`, recomendaciones, avisos | Ya está en `datos_draft()` |
| Draft | cuál aviso cambia la decisión | **Falta** (`avisos` es lista de cadenas) |
| Draft | build de los top (3 ítems, botas, runa, orden), n y mi WR por ítem | Hay 3 líneas de texto; **falta estructurado** (el dict de `resumir`) |
| Draft | tu build (sin key) | **Falta** en `builds.json` |
| In-game | meta de la fase (CS/nivel/oro vs objetivo) | Está en la foto de 30 s; **falta exponerla** a la GUI |
| In-game | avisos `{texto, tipo, minuto}` | **Falta** (hoy cadena) |
| Post | score de la partida, puesto, 8 componentes en z | Está en `score.py`; **falta como dict** (hoy cadena en la tabla) |
| Post | tendencia: score medio por bloque de 20 | Está en el análisis; **falta como lista** |
| Post | causa principal de la derrota/victoria | **Falta** (calcular de las metas) |
| Post | WR + score por campeón | Está en `score.py`; falta como dict |
| General | estado de la key en vivo | **Falta** (se calcula una vez) |

## 7. Preguntas para la charla

1. **¿Cómo juegas hoy?** (a) LoL en ventana sin bordes, (b) pantalla completa, (c) segundo monitor. Si es (b), el modo compacto flotante no sirve y la franja iría al segundo monitor o a un overlay externo.
2. **¿Qué quieres ver en partida?** (a) solo avisos, (b) avisos + meta de la fase, (c) nada: lo miras al morir o en el lobby.
3. **¿Aviso con sonido?** (a) nunca, (b) solo los críticos, (c) todos.
4. **¿Cuántas opciones de pick quieres ver en champ select?** (a) solo la mejor, (b) 3 con la mejor destacada, (c) 4 como hoy.
5. **Build de los top: ¿cuánto detalle?** (a) 3 ítems y botas, (b) además runas y orden de habilidades, (c) todo el detalle incluyendo inicio y consumibles.
6. **¿Cómo prefieres el score?** (a) barra 0–100 con la marca de 50, (b) número grande con flecha de tendencia, (c) solo la tendencia de 20 partidas.
7. **Colores:** ¿probamos el cian en lugar del ámbar (mockup con los dos), o conservas el ámbar?
8. **Tamaño de la ventana completa:** (a) 420×760 como hoy, (b) más ancha (~560) con dos columnas (pick a la izquierda, build a la derecha), (c) lo que quepa en el monitor.
9. **¿Dónde se ve el historial?** (a) aquí, en una pestaña «Partidas», (b) solo en los análisis `.md`, (c) no hace falta.
10. **Idioma de la interfaz:** (a) todo en español (`Jungla`, `Selección de campeón`), (b) términos del juego en inglés (`champ select`, `ADC`) y el resto en español.

## 8. Lo que pido a Opus (una línea cada uno)

- Avisos como `{texto, tipo, minuto, cambia_decision}` en vez de cadena.
- `builds.guardado()` que devuelva el dict estructurado (ítems, botas, runa, orden, n) además de las 3 líneas.
- `score.py` exponga un dict por partida: `{score, puesto, componentes_z, tendencia}`.
- Que la foto en vivo exponga la meta de la fase (CS/nivel/oro) como números.
- Estado de la key re-evaluable (función `hay_key()` ya existe; que se llame periódicamente).

## 9. Consulta a DeepSeek

Pendiente en esta iteración; ver `.equipo/notas-equipo.md`, sección Diseñador, iteración 2.
