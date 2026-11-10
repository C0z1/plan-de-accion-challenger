# Limpieza del repo para público (2026-11-10)

Pedido del usuario: dejar solo lo que usa la app HTC, mejorar `README.md` y borrar lo que no sirve. Todo con `git rm` (recuperable), **sin commit**.

## Qué borré (56 archivos, con por qué)

**20 scripts de análisis sueltos** — nada de la app (`companion_web.py` ni `descargar.py`) los importa directa ni indirectamente; son análisis de una sola vez:

`analizar.py`, `anticipa.py`, `castigo.py`, `convertir.py`, `corte6.py`, `early.py`, `linea.py`, `midgame.py`, `minions10.py`, `muertes6.py`, `nivel6.py`, `objetivos.py`, `partida.py`, `placas.py`, `recorrido_ficha.py`, `rol.py`, `sin_objetivo.py`, `timeline.py`, `wards.py`, `xp.py`.

> Ojo: `companion.py` tiene su propia función `minions10()` (no el script) y `objetivos()`/`muertes14` inline, así que borrar esos scripts no rompe la app.

**23 `datos/analisis-*.md`** — salidas de esos scripts (incluye `analisis-2026-11-07.md`, `analisis-partidas-…`, `analisis-timeline-…`, etc.).

**3 `datos/plan-opus-*.md`** (`plan-opus-12`, `plan-opus-t7-2`, `plan-opus-t7-3`) — planes temporales que Opus le pasó a DeepSeek.

**`datos/2026-11-07.md`** — nota vieja.

**7 artboards viejos (no Vino)** — `ChampSelect.dc.html`, `ChampSelect_Paleta3E.dc.html`, `Inv1.dc.html`, `Inv5.dc.html`, `Navy3.dc.html`, `Perfil.dc.html`, `.equipo/diseno/mockup.html`.

**`RESUMEN-NOCHE.md` y `TARJETA.md`** — notas internas de los agentes.

## Qué edité

- **`README.md`** reescrito para el repo público: qué es, instalar, desde el código, fases (Inicio → Draft → Selección → En vivo), las 9 vistas, RIOT_KEY, APIs y privacidad, pruebas, licencia y el aviso legal de Riot **textual**. Fuera las notas internas. (Opus lo mejoró en paralelo con una versión que agrega la URL del repo; la actual en disco es esa, y también cumple el pedido.)
- **`docs/USO.md`**: quité `analizar.py`, `partida.py`, `recorrido_ficha.py`, `minions10.py` y la sección «Análisis profundo» (todos borrados); agregué `--fondo` a `companion_web.py`.
- **`.equipo/PIZARRON.md`**: quité del mapa del repo las filas de lo borrado y actualicé mi sección.

## Lo que dudé y dejé

- **`.equipo/PLAN.md:4`** enlaza a `datos/analisis-2026-11-07.md` y `datos/analisis-timeline-2026-11-07.md` (ahora rotos). No lo toqué: está en «NO borres» y solo me autorizaron a editar `README.md`. → Opus decide si quita el enlace.
- **`companion_gui.py`** (respaldo tkinter, se queda) tiene la cadena «Minuto a minuto: python scripts/partida.py --early»: apunta a un script borrado. Fuera de los tres lugares del paso 6; lo dejo anotado.
- **`.equipo/diseno-contexto.md`** ya estaba modificado por el Diseñador (no es mío); no lo toqué.
- **`test_ds_anticipa.py`** se queda: pese al nombre, prueba `companion_gui.lineas_ficha()`, no `anticipa.py`.
- **`docs/config.ejemplo.json`** se queda aunque trae el `RIOT_ID` de cozi: lo pide la tarea y no es un secreto (ya estaba público).

## Suite

`python -m unittest discover scripts` → **252 OK** al final (mis borrados: 251 antes y 251 después; Opus sumó `scripts/test_descargar.py` en paralelo = 1 más).
