# Pizarrón del equipo

> Contexto vivo del repo. **Léelo primero.** Cada agente edita **solo su sección** de "Ahora": la actualiza al empezar y al terminar cada turno. En "Hallazgos" y "Decisiones" solo se agregan renglones, no se borran.
> El detalle largo va en `datos/notas-equipo.md`. Aquí van solo líneas cortas.

## Meta
Llevar a `cozi#1134` (LAN) de **Master 15 LP a Challenger** (~1,750 LP). Para lograrlo hay que subir el WR de **54% a 60% o más** (ver `PLAN.md`).

## Ahora

### Opus · constructor
- **Estado:** turno 7, iteración 3: la app web tiene la ventana 2, «Tu rendimiento» (Perfil), con `score.resumen(20)` y `tilt()`: score y WR de las últimas 20, tendencia por bloques, los 3 componentes más bajos, tilt hoy, cuenta (WR contra meta 60%) y campeones. El nav alterna Companion/Perfil; fuera de champ select y partida se ve Perfil. Se recalcula en un hilo al arrancar y tras cada revisión. 189 OK.
- **Iteración 4:** primera build `Companion.exe` v0.1.0 (entrada `companion_web.py`, `--add-data scripts/web;web`); arranca con `--demo`, sirve la página y el JSON (fase InProgress, Perfil con datos). Tag `v0.1.0`. 189 OK.
- **Iteración 5:** la página va con `Content-Security-Policy` (`default-src 'none'`, solo deja imágenes y fetch del mismo origen), que era la idea 2 de DeepSeek. `lineas` sigue en `draft_json` porque `test_ds_web` lo exige. 190 OK.
- **Iteración 6:** tarjeta «Muertes 14–25» en Perfil (`score.muertes14_25()` desde el timeline; `resumen()` lo da por partida). Media real de las últimas 20: 3.0, con meta ≤ 2. Paletas en config descartadas: no salen baratas. 193 OK.
- **Iteración 7:** ideas 1–3 de DeepSeek en Perfil: el pie dice «±22 (95%)» y se calcula con el n real; con 0 partidas sale «Sin partidas». Rebuild `Companion.exe` v0.1.1 (CSP + Muertes 14–25 + esto); tag `v0.1.1`. No corrí el humo del `.exe`: el harness no dejó ejecutarlo. 193 OK.
- **Iteración 8:** un timeline roto ya no vacía Perfil: `muertes14_25` da None solo para esa partida (tarea c de DeepSeek). Humo del `.exe` otra vez bloqueado por el harness. 195 OK.
- **Iteración 9:** con n ≤ 3, el pie del WR dice «Pocas partidas: el WR casi no dice nada» (idea 1 de DeepSeek). El humo del `.exe` y el asesor siguen bloqueados por el harness. 196 OK.
- **Iteración 10:** con 0 partidas, «Qué está fallando» dice «Sin partidas todavía.» en vez de «Últimas 0». Rebuild `Companion.exe` v0.1.2 (iteraciones 8–10), tag `v0.1.2`. Humo y asesor bloqueados por el harness. 197 OK.
- **Iteración 11:** primer humo real del `.exe`: `scripts/humo_exe.py` lo lanza con `--demo --no-abrir`, encuentra el puerto (tasklist + netstat), pide `/api/estado` y lo mata. v0.1.2 **arranca y responde** (11 claves, fase `inicio`) y no deja procesos vivos. 197 OK.
- **Iteración 12 (pedido del usuario):** íconos propios (Lucide, ISC) por métrica y en el nav; «Cómo jugarlo» en filas con tu dato real contra la meta y ✓/✕ con n (`draft.tu_regla`); «Qué está fallando» con los 8 componentes en unidades contra tu rol, barra divergente y una acción por fila (`score.unidades`). Falta la revisión en navegador y el rebuild del .exe. 200 OK.
- **Iteración 13:** `OSError` en `muertes14_25`, humo que ignora puertos de un Companion.exe ya abierto, acción de visión sin «control ward» (no tiene respaldo en el PLAN). Rebuild `Companion.exe` v0.1.3 (con la iteración 12), humo OK, tag `v0.1.3`. 200 OK.
- **Siguiente:** revisión visual, rebuild v0.1.3 y RESUMEN-NOCHE.
- **Actualizado:** 2026-11-09 (turno 7, iteración 12)

- **Iteración 14:** vista «Partidas» nueva (botón de historial en el nav): las últimas partidas de `resumen()` con ✓/✕, campeón, KDA, el componente que más te subió o bajó, score y fecha. Sin Python nuevo. Ajustes sigue sin vista. 201 OK.
### DeepSeek · revisor
- **Estado:** revisado ef71e63 (turno 7, iter 11): humo real de `Companion.exe` v0.1.2 con `scripts/humo_exe.py` — lo corrí, `exit=0` y `/api/estado` responde (11 claves); no deja procesos vivos. Riesgo (b) confirmado: con otra instancia abierta, `ports[0]` puede leer su puerto (falso OK); sugerí foto previa de netstat en vez de filtrar por PID hijo.
- **Siguiente:** RESUMEN-NOCHE; cubrir el `OSError` de `muertes14_25` (pendiente de 4355eaa).
- **Actualizado:** 2026-11-09 03:41 (turno 7, revisión ef71e63)

### Diseñador
- **Estado:** canvas «Base LOL» de vuelta a su versión anterior (Perfil, ChampSelect y 3 paletas) más ChampSelect en Paleta 3E. Las ventanas de franja y post-partida que hice se quitaron del canvas. Contexto en `datos/diseno-contexto.md`; sigue abierto el error de copy (82/57 → 68/43).
- **Siguiente:** publicar los cambios que pida el usuario al canvas; al cerrar, acuerdos en `datos/diseno-acuerdos.md`.
- **Actualizado:** 2026-11-09 (revierte franja/post y agrega ChampSelect 3E)

## Mapa del repo
| Archivo | Qué es | Dueño |
|---|---|---|
| `PLAN.md` | Plan de acción vigente | Opus |
| `scripts/descargar.py` | Baja partidas y timelines de la Riot API a `datos/raw/` | Opus |
| `scripts/analizar.py` | Estadísticas agregadas → `datos/analisis-*.md` | Opus |
| `scripts/timeline.py` | Análisis de timeline (muertes, oro por minuto) | Opus |
| `scripts/draft.py` | Guía de matchups (sin args) o recomendación de pick: `draft.py <rival> [rol]`; `ficha()` da por qué el pick, cuidado con el rival y counters como dict | Opus |
| `scripts/recorrido_ficha.py` | Champ select en texto contra tus N rivales más frecuentes de un rol, para revisar lo que ve el usuario: `recorrido_ficha.py [rol] [N]` | Opus |
| `scripts/corte6.py` | ¿Tu media de nivel al 6 contra un rival anticipa la siguiente partida contra él? (leave-one-out, cortes 0 a −0.5) | Opus |
| `datos/analisis-corte6-*.md` | Salida de `corte6.py` | Opus |
| `scripts/anticipa.py` | ¿Cada medida de «Cuidado con el rival» anticipa la próxima partida contra él? (LOO y temporal, permutación, MSE) | Opus |
| `datos/analisis-anticipa-*.md` | Salida de `anticipa.py` | Opus |
| `datos/matchups-notas.json` | Opcional, a mano: `{"Rival": "nota" o ["…"]}`; sale en `ficha()["cuidado"]["notas"]` (si no existe, nada) | Usuario |
| `datos/analisis-aviso-muertes-*.md` | Verificación del aviso de muertes 14–25 (WR por número de muertes, con y sin equipo arriba) | Opus |
| `datos/analisis-matchups-*.md` | Guía de matchups y bans generada por `draft.py` | Opus |
| `scripts/revision.py` | Últimas N partidas contra las metas del plan (✅/❌), racha de oro < 0 al 14 (3+ de las últimas 5) con 2 sugerencias, y tabla por partida: `revision.py [N]` | Opus |
| `datos/analisis-revision-*.md` | Salida de `revision.py 20` | Opus |
| `scripts/midgame.py` | Mid game en partidas con la línea ganada al 14: oro del equipo, muertes 14–25 (pick-off, objetivo perdido, zona) | Opus |
| `datos/analisis-midgame-*.md` | Salida de `midgame.py` | Opus |
| `scripts/rol.py` | Mid contra top (y demás roles): WR, línea, conversión, campeones, tendencia, permutación | Opus |
| `datos/analisis-rol-*.md` | Salida de `rol.py` | Opus |
| `scripts/convertir.py` | Línea ganada al 14 por campeón y V/D de uno: `convertir.py [Campeón]` (por defecto tu más jugado) | Opus |
| `datos/analisis-convertir-*.md` | Salida de `convertir.py` | Opus |
| `scripts/linea.py` | Línea perdida al 14: muertes por gank/1v1, CS, XP, por campeón y V/D: `linea.py [Campeón]` | Opus |
| `datos/analisis-linea-*.md` | Salida de `linea.py` | Opus |
| `scripts/xp.py` | XP vs rival 2–14 minuto a minuto según tu estado (muerto, matas al rival, base, fuera, línea) | Opus |
| `datos/analisis-xp-*.md` | Salida de `xp.py` | Opus |
| `scripts/castigo.py` | Línea perdida: cómo muere tu rival antes del 14 (tú solo, con jungla, sin ti), XP tuya contra ajena, WR | Opus |
| `datos/analisis-castigo-*.md` | Salida de `castigo.py` | Opus |
| `scripts/placas.py` | Placas reales del timeline en tu línea (tuyas, del equipo, perdidas) contra WR, a igual oro y por campeón | Opus |
| `datos/analisis-placas-*.md` | Salida de `placas.py` | Opus |
| `scripts/nivel6.py` | Diferencia de nivel con tu rival 0–14: muertes/kills por 10 min (con y sin jungla rival), zona de la muerte (arriba contra igual), carrera al 2 y al 6 | Opus |
| `datos/analisis-nivel-*.md` | Salida de `nivel6.py` | Opus |
| `scripts/early.py` | Qué separa V/D en el early por campeón (challenges + timeline @14, permutación y q de BH, control a igual oro) | Opus |
| `datos/analisis-early-*.md` | Salida de `early.py` | Opus |
| `scripts/partida.py` | Replay en datos de una partida (min 12–26, o 0–12 con `--early`) o de las últimas derrotas con la línea ganada: `partida.py [id [--early] | --ultimas N]` | Opus |
| `datos/analisis-decisiones-*.md` | Revisión de decisiones en derrotas con la línea ganada | Opus |
| `scripts/objetivos.py` | Presencia en objetivos, minuto de los ganks y muertes del late a igual oro | Opus |
| `datos/analisis-objetivos-*.md` | Salida de `objetivos.py` | Opus |
| `scripts/muertes6.py` | Muertes antes del 6: tipo (1v1/gank), nivel al 3 y al 6, WR y oro @14, por campeón y rival, últimas 10 | Opus |
| `datos/analisis-muertes6-*.md` | Salida de `muertes6.py` | Opus |
| `scripts/wards.py` | Control wards: tú y los 1,431 jugadores de línea ajenos (gank <14 y WR, a igual oro y por rol) | Opus |
| `datos/analisis-wards-*.md` | Salida de `wards.py` | Opus |
| `scripts/companion.py` | Lee el cliente de LoL (solo lectura): en champ select corre `draft.py` contra tu rival; al terminar, `descargar.py 5` + `revision.py 1`; en partida, avisos de nivel (5–7), minions (10) y muertes desde el 14 (2+ antes del 25); al terminar, una línea de la última foto en vivo (`resumen_fin()`, sin key). `rango()` da tu LP del cliente (sin key). `--fixture <carpeta>` para probar | Opus |
| `scripts/companion_web.py` | Companion con UI web local (diseño del canvas): servidor en 127.0.0.1 con `/api/estado`, íconos de Data Dragon en caché; abre Edge `--app`. `--demo`, `--no-abrir` | Opus |
| `scripts/web/index.html` | La página del companion (champ select del canvas; polling a `/api/estado`) | Opus |
| `scripts/humo_exe.py` | Humo de la build: corre `Companion.exe --demo --no-abrir`, busca su puerto y comprueba `/api/estado`; sale 0 si responde | Opus |
| `scripts/test_companion_web.py` | Pruebas del servidor web (estado JSON, HTTP, Host, imágenes) sin red ni navegador | Opus |
| `datos/vivo/` | Fotos en vivo de la Live Client Data API que guarda `companion.py` (una línea JSON cada 30 s; en `.gitignore`) | Opus |
| `scripts/fixtures/` | JSON de ejemplo de la LCU (gameflow-phase, champ-select session) | Opus |
| `scripts/fixtures/vivo/allgamedata.json` | Foto sintética de la Live Client Data API (min 6, Ekko 5 contra Zed 6; nombres inventados) | Opus |
| `scripts/test_companion.py` | Pruebas sin red: `python -m unittest discover scripts` (incluye `Robusto`: lockfile, timeouts, JSON cortado, reinicio a media partida) | Opus |
| `scripts/score.py` | Score por partida contra tu equipo y la partida (8 componentes en z contra los 10, corregido por rol; 50 = típico): tendencia, V/D, duelo con tu rival de línea, por campeón, qué te baja: `score.py [N]`; `score.resumen(n)` lo da como dict; `score.tilt()` da hoy, racha y WR tras 2 derrotas seguidas | Opus |
| `datos/analisis-score-*.md` | Salida de `score.py` | Opus |
| `scripts/builds.py` | Build de los mejores (Challenger/GM de la1 y kr, Riot API) y la tuya (`datos/raw`): `builds.py <Campeón> [rol]` o `--pool`; `guardado_dict()` la da como dict para la GUI | Opus |
| `datos/analisis-builds-*.md` | Salida de `builds.py --pool` | Opus |
| `datos/meta/` | Caché de Riot API y Data Dragon, y `builds.json` que lee `draft.py` (en `.gitignore`) | Opus |
| `scripts/test_builds.py` | Pruebas de `builds.py` con la Riot API simulada | Opus |
| `scripts/test_score.py` | Pruebas de `score.py` y de la columna Score de `revision.py` | Opus |
| `scripts/test_ds_*.py` | Pruebas de casos borde que escribe DeepSeek | DeepSeek |
| `scripts/test_flujo.py` | Humo del companion de punta a punta sin cliente (champ select, partida, post-partida); corre en el CI | Opus |
| `scripts/test_draft.py` | Pruebas de `draft.py` (funciones y recomendación con partidas sintéticas) y humo de `revision.py 1` | Opus |
| `scripts/fixtures/datos/` | Perfil y una partida mínima: `test_draft` los usa si no hay `datos/raw` (CI, clon nuevo) | Opus |
| `.github/workflows/pruebas.yml` | CI: `python -m unittest discover scripts` en Ubuntu y Windows | Opus |
| `config.ejemplo.json` | Ejemplo (cozi) de `config.json`: pool y meta `minions10` para `revision.py`; `config.json` va en `.gitignore` | Opus |
| `datos/notas-equipo.md` | Detalle de cada turno y de cada revisión | Ambos (solo agregar) |
| `BITACORA.md` | Sesiones jugadas por el usuario | DeepSeek |
| `PIZARRON.md` | Este pizarrón | Ambos (cada quien su sección) |
| `RESUMEN-NOCHE.md` | Resumen del turno nocturno para el usuario | Opus |
| `TARJETA.md` | Reglas del PLAN en una página, para jugar | Opus |

## Hallazgos (con datos)
- 2026-11-07 · Opus: cierre del turno 2: companion, descargar robusto y 17 pruebas; falta champ select real.
- 2026-11-08 · Opus: la prueba vieja de draft pasaba también sin encogimiento; la nueva `test_encoge_un_record_corto` falla con M≈0 (elige Yone 100%) y pasa con M=10 (Ekko).
- 2026-11-07 · DeepSeek: KP es 41% en victorias y en derrotas, así que no las separa. Lo que sí separa es muertes (5.8 vs 7.4) y oro contra el rival (+1313 vs −1566).

- 2026-11-07 · Opus: ningún ban tiene respaldo: 2 de 80 rivales quedan bajo el WR base y el azar da ~1.9.
- 2026-11-07 · Opus: Viktor mid 1-7 (Ekko 0-4); Diana mid 2-5 con −1322 de oro al 14.
- 2026-11-07 · Opus: la racha (35% en últimas 20) no es de línea: oro ≥ 0 al 14 en 60% (antes 45%), pero convierte 5 de 12 (42% vs 65%); 60% fuera del pool.
- 2026-11-07 · DeepSeek: el "convierte 5 de 12 (42%)" es pista, no hecho: n=12, IC 19–68% se cruza con el 65% (56–73%) de la temporada.
- 2026-11-07 · DeepSeek: `gameEndedInEarlySurrender` no existe en los 300 JSON; el filtro de remakes vive solo de `gameDuration < 300` (alcanza: las 18 remakes son <300s). Código muerto en timeline/draft/revision.
- 2026-11-07 · Opus: con la línea ganada al 14, si el equipo va < 0 de oro gana 40% (25–58), y si va ≥ 0, 69% (60–78). Con 3+ muertes del 14 al 25, 50%; con 1–2, 74%.
- 2026-11-07 · Opus: en las derrotas, el 72% de las muertes del 14 al 25 vienen seguidas de un objetivo perdido en 90 s (línea base 58%). Los pick-offs no separan (37% contra 33%).
- 2026-11-07 · Opus: la permutación a nivel de partida (sugerida por DeepSeek) confirma que no hay bans con respaldo: 2 reales contra ~1.7 del azar (p = 0.50).
- 2026-11-07 · DeepSeek: la base de "objetivo perdido en 90 s" tiene sesgo leve por partidas cortas (56% vs 58% en partidas ≥ 25 min): no cambia la conclusión.
- 2026-11-07 · DeepSeek: cortando por oro del equipo al 20 (con equipo ≥ 0), 0–2 muertes 14–25 → 84% (n=44) y 3+ → 61% (n=36, IC se cruzan): el efecto de las muertes se mantiene pero se debilita.
- 2026-11-07 · Opus: top 58% contra mid 54% es ruido (permutación p = 0.55). Top es bueno por Mordekaiser (68%); top sin Morde, 53%. Sylas top 4/11.
- 2026-11-07 · Opus: las muertes del 14 al 25 pesan aunque el equipo vaya bien: con línea y equipo ≥ 0 al 14, 0–2 muertes → 82% (69–90); 3+ → 57% (43–70).
- 2026-11-07 · Opus: Ekko sí convierte: con línea ganada 60% (45–74), igual que el resto (62%). Con línea perdida 42%, como Sylas (43%); Yone 57%.
- 2026-11-07 · Opus: `turretPlatesTaken` no mide tus placas (da hasta 23 por jugador; el máximo de un equipo es 15). Se quitó del PLAN.
- 2026-11-07 · Opus: con la línea perdida (148), las muertes <14 no separan (V 2.62, D 2.32); sí CS y XP @14 (−11/−529 contra −16/−806). Solo 5/148 líneas perdidas sin morir.
- 2026-11-07 · Opus: Ekko con línea perdida: V llega con CS −0.2 y XP +24, D con −17 y −715. > 10 CS abajo: 4/17 (24%); ≤ 10: 9/14 (64%).
- 2026-11-07 · Opus: a igual oro (−1500 a −500 al 14, n=74) el CS no separa (47% vs 44%) y la XP sí: ≥ mediana 65% (49–78), < mediana 27% (15–43).
- 2026-11-07 · Opus: el CS @14 por rival de línea no se aleja del azar (19 rivales, permutación p = 0.30): el farm perdido no es de matchup.
- 2026-11-07 · DeepSeek: dentro de Sylas solo el CS @14 por rival sigue variando (Yasuo −26, Qiyana −20, Viktor −28, contra Zed +4): el p=0.30 no es confusión con tu campeón, es que 3 rivales que niegan farm se diluyen entre ~19 neutros. Muestra chica (pista).
- 2026-11-07 · DeepSeek: el filtro "20+ min" (`len(fr) <= 20`) deja entrar 2 partidas que acaban en 19:21 y 19:36; su "@20" lee el frame final. Menor (2 de 275).
- 2026-11-07 · Opus: con la línea perdida, los minutos de muerte cuestan −760 de XP en V y en D; regresos y roams ~0. La brecha V/D (−529 vs −806) es 70% XP de matar al rival (+420 vs +226).
- 2026-11-07 · Opus: con la línea perdida, de la XP de "muere él" +325/+193 (V/D) es de kills contigo y +95/+31 sin ti. 0 kills tuyos sobre el rival antes del 14: 40% (28–53); 1+: 54% (44–64); 1+ en solitario: 59%.
- 2026-11-07 · Opus: contar el minuto siguiente a tu muerte como "muerto" casi no cambia xp.py (−786/−818 contra −759/−763).
- 2026-11-07 · Opus: corrige el renglón de `turretPlatesTaken`: en este parche hay hasta 15 placas por línea y equipo (3 torres) y caen después del 14. Igual no son tus placas (cuadra con los last hits del timeline en 159/600).
- 2026-11-07 · Opus: tus placas antes del 14 no separan V/D (ganada 2.17/2.02, perdida 1.28/1.13). Las perdidas sí, a igual oro: 0–1 contra 3+ → 58/36, 65/54, 76/50% en las 3 bandas (pista).
- 2026-11-07 · DeepSeek: a igual oro (−1500 a −500, n=73) el "1+ kill → 54%" baja a 39% vs 52% (IC 25–56 vs 37–67): parte es ir menos perdido (−844 vs −1201 de oro); el kill con jungla llega con el peor CS @14 (−16.1).
- 2026-11-07 · Opus: placas perdidas <14: estando fuera (base/roam) no separan (0 → 56%, 1+ → 52%); estando en tu línea sí (63% contra 48%); muerto 0.89/1.18 V/D. Es el rival con prioridad, no irte.
- 2026-11-07 · DeepSeek: ese "estando en tu línea separa" es artefacto de la foto gruesa: con placas a ≤15 s de un frame (316/645) pasa de 63 vs 48% a 54 vs 56%, y se invierte en 2 bandas. No concluyente.
- 2026-11-07 · Opus: el filtro `gameDuration ≥ 1200` en linea/convertir/xp saca 2 derrotas de 19:xx; nada cambia de conclusión (Ekko abajo 43%, XP en D −816).
- 2026-11-07 · Opus: yendo 1 nivel arriba de tu rival antes del 14 mueres ×1.31 (1.06–1.61) que a nivel igual; 65% con el jungla rival (49% igual). Abajo, ×1.04: no mueres más.
- 2026-11-07 · Opus: medir el nivel en el instante de la muerte da un "1 abajo" falso (×1.5) por el LEVEL_UP que tu kill le da al rival; se mide 3 s antes.
- 2026-11-07 · Opus: primero al 6: 62% contra 48%, pero a igual oro 52/44, 56/47, 69/62 (IC cruzados): casi todo es reflejo de ir arriba. Primero al 2: 59% contra 51%.
- 2026-11-07 · DeepSeek: placas perdidas "estando en tu línea" no separan con placas a ≤ 15 s de una foto (54% contra 56%): era artefacto de la foto por minuto.
- 2026-11-07 · Opus: yendo arriba de nivel, en tu lado de la línea mueres menos (×0.75, 0.52–1.08); pasado el río ×1.89 (1.35–2.64); jungla rival ×2.53 (1.23–5.21).
- 2026-11-07 · Opus: tu ward en los 90 s previos a morir no cambia la proporción de ganks (arriba 64% contra 67%); el timeline no trae la posición del ward.
- 2026-11-07 · Opus: bootstrap por partida: ×1.31 (1.07–1.58), pasado el río ×1.89 (1.28–2.62) aguantan; pero en mid 1 arriba ×1.12 (0.85–1.44) y pasado el río ×1.43 (0.82–2.25). Es efecto de top/bot (×2.43).
- 2026-11-07 · Opus: muertes <14 pasado el río por partida no separan V/D (1.10 contra 1.05; 0 → 51%, 1+ → 57%): el riesgo es cruzar con nivel arriba, no cruzar.
- 2026-11-07 · Opus: Sylas con > 68 minions de línea al 10: 74% (60–85); ≤ 68: 32% (20–46), q = 0.01. Aguanta en cada tercio de oro @14 y solo en mid. En el total no separa (67.2 contra 67.1).
- 2026-11-07 · Opus: Yone: ninguna de 18 métricas del early separa V/D (q ≥ 0.72). Ekko: XP/CS/oro @14 y kills <14 (q ≤ 0.03), casi todo reflejo del oro.
- 2026-11-07 noche · Opus: morir antes del 6 no baja el WR: 0 → 50% (42–58), 1+ → 59% (51–66); cuesta ~−430 de oro @14. Sin sangre (0 muertes y 0 kills <6): 45%. Las 1v1 <6 tampoco separan (54 contra 57%).
- 2026-11-07 noche · Opus: nivel al 3 no separa (55/54/56%); abajo al 6 → 44% (30–60), arriba 69% (51–82); 86% de las partidas abajo al 6 tuvieron muerte <6. Pista.
- 2026-11-07 noche · Opus: el % de partidas con muerte <6 sí varía por rival (permutación p = 0.04): Sylas 9/10, Fizz 5/6, Syndra 5/6, Ekko 4/5. n chica.
- 2026-11-07 noche · Opus: Sylas con 69+ minions al 10: 47% de las partidas antes de las últimas 20 (n=88) y 2 de 4 en las últimas 20. Ahora lo mide `revision.py`.
- 2026-11-07 noche · Opus: control ward antes del 14 no baja los ganks (0.85 contra 0.92 muertes por gank <14) ni sube el WR (49/49%) en 1,431 jugadores de línea ajenos; a igual oro tampoco. Tú: 8 de 261 partidas con alguno.
- 2026-11-07 · DeepSeek: "abajo al 6 → 44%" no es solo reflejo de morir: sin muerte <6 son 2/5 = 40% (n=5). Refuerza la pista "no salir del 6 con nivel abajo".
- 2026-11-07 · DeepSeek: el 74/32 de Sylas aguanta el filtro de `revision.py` (92 vs 90 Sylas: entran una partida de 12:49 y una jungle; >68 sigue 74%, ≤68 pasa 32→33%).
- 2026-11-07 noche · Opus: `companion.py` verificado en vivo y en solo lectura contra el cliente abierto (el lockfile existe; la fase era `InProgress`). El champ select solo se probó con fixtures.
- 2026-11-07 · DeepSeek: RIOT_KEY caducó (401 en `descargar.py 5`): la partida nueva sigue sin poder bajarse; hay que renovarla (`setx RIOT_KEY`).
- 2026-11-08 · Opus: todos los scripts buscaban `LA1_*.json`: con una cuenta de otra región no veían ninguna partida. Ahora `*_*.json`.
- 2026-11-08 · Opus: en un clon nuevo (sin `datos/raw`) las pruebas fallaban: `draft.py` lee `perfil.json` al importarse. El CI habría salido rojo desde el primer push; ahora usa `scripts/fixtures/datos`.
- 2026-11-08 · Opus: las referencias fijas de `revision.py` se reproducen con los datos (62%; 2.11 contra 2.12; río V 1.10 contra D 1.04) y ninguna ✅/❌ cambia en `revision.py 20`.
- 2026-11-08 · Opus: punta a punta con JUGKING#1345 (Challenger LAN, 20 partidas, `DATOS_DIR` aparte, sin config): descargar, analizar, draft y revision salen 0; `datos/raw` intacto; datos de prueba borrados.
- 2026-11-08 · DeepSeek: glob `*_*.json` seguro hoy (`perfil.json` sin `_`, `timeline-log.txt` no es .json, `timeline/` es dir quedan fuera); riesgo residual solo si cae un `.json` con `_` que no sea partida (menor).
- 2026-11-08 · Opus: `revision.py 5`: en las últimas 5 llegaste al 14 con oro < 0 en las 5 (media −786, CS −11) y aun así 3 V; 2 de ellas fuera del pool (Locke, Rakan). n=5, pista.
- 2026-11-08 · Opus: la Live Client Data API (127.0.0.1:2999, sin auth) responde durante la partida con oro actual, nivel, ítems, CS y eventos (kills); ~20 KB por foto, ~1 MB por partida a 30 s.
- 2026-11-08 · DeepSeek: los 4 `.pyc` rastreados en `scripts/__pycache__/` aún traen la ruta completa `C:\Users\…` (en el `co_filename` del bytecode); la limpieza de datos personales solo cubrió texto. Misma acción pendiente: `git rm -r --cached scripts/__pycache__`.
- 2026-11-08 · DeepSeek: el resumen del Turno 3 no trae datos personales, pero `PIZARRON.md:132` y `notas-equipo.md:912` aún muestran el nombre de usuario en la ruta (no del todo `C:\Users\…`). Cosmético, para el próximo cleanup.

- 2026-11-08 · Opus: con oro < 0 al 14 (n=154), XP @14 ≥ la mediana (−746) → 56% (45–66), debajo 38% (28–49); nivel ≥ rival al min 6 → 48% (40–57), abajo 38% (21–57). Intervalos cruzados: pista.
- 2026-11-08 · Opus: tus últimas 5 llegan al 14 con oro < 0 (las 5), pero con XP −586 (mejor que la mediana) y nivel parejo al 6: el oro se va por otro lado (CS −11).

- 2026-11-08 · DeepSeek (vía `test_ds_nivel6.py`): `aviso_nivel` tronaba con `"level": null` (TypeError). Arreglado: cuenta como 0 y muestra «?».
- 2026-11-08 · Opus: una respuesta cortada del cliente (`http.client.IncompleteRead`) no es `OSError` ni `ValueError`: tumbaba `companion.py`. Y un reinicio del cliente a media partida partía la grabación y repetía el aviso. Arreglados.
- 2026-11-08 · DeepSeek (vía `test_ds_nivel6.py`): `aviso_nivel` también tronaba con `gameTime: null`. Arreglado.
- 2026-11-08 · Opus: el aviso de draft no salta con ninguno de tus 99 rivales de mid/top: el único counter duro de tu pool (Ekko 0-4 contra Viktor) ya no sale recomendado por el encogido M=10.
- 2026-11-08 · Opus: el flujo completo del companion (draft en champ select, 3 fotos en un archivo, 1 aviso, descarga + revisión una vez) pasa sin cliente; solo toca 127.0.0.1.
- 2026-11-08 · Opus: meter el `get` de la fase dentro del `try` de `companion.main` (sugerencia de DeepSeek) cuelga las pruebas: el `except Exception` se traga el `StopIteration` con que cortan el bucle. Queda fuera; `lcu()` ya atrapa todo.
- 2026-11-08 · Opus: score (`score.py`, 284 partidas): 49.6 de media (típico de tu rol); V 51.1 contra D 47.9; ajenos 52.1 contra 47.9. Tu componente más bajo es el KP (−0.33 contra tu rol, también en V); en D lo que más cae es la línea (−0.50) y las muertes (−0.42). Sin tendencia: últimas 20 49.2 contra 49.7.
- 2026-11-08 · Opus: Mordekaiser es tu mejor WR (68%) con el score más bajo (47.5): gana sin destacar en las stats (pista, n=22).
- 2026-11-08 · Opus: tu build con Yone mid (40): Rey Arruinado → Arcoescudo → Filo, Grebas, Cadencia Letal, Q>E>W. Con Mordekaiser top (22): Agrietador → Rylai → Apariencia Espiritual, Conquistador. Falta la de los top (key caducada).
- 2026-11-08 · DeepSeek: score.py reproduce el análisis (284 = 302 − 18 remakes, todas mapId 11); la corrección por rol no sesga con un rol raro (support sale de ~550 ajenos de todas las partidas). Menor: el control «otros» incluye a cada ajeno en su propia base (~0.2% de encogimiento), solo en la línea de control.
- 2026-11-08 · DeepSeek (vía `test_ds_builds.py`): un legendario vendido seguía contando en el core de la build. Arreglado (solo legendarios; las botas vendidas siguen contando). Tus builds no cambian.
- 2026-11-08 · Opus: superas en score a tu rival de línea en 44% de las partidas (38–49, n=284): 51% (43–59) en V y 35% (27–43) en D. Ganas sin ganar el duelo (cuadra con KP −0.33). Monitor.
- 2026-11-08 · DeepSeek: el upgrade Manamune→Muramaná / Báculo→Serafín es ITEM_DESTROYED (44 y 40 en los timelines), no ITEM_SOLD, y las formas evolucionadas nunca se compran: el core muestra la forma base (cosmético). Menor sin arreglar: `get()` con 4×429 seguidos deja `data` sin asignar (UnboundLocalError).
- 2026-11-08 · Opus: arreglado ese 429: el último se propaga sin guardarse en caché, e `informe()` lo toma como «sin datos» de los mejores (el pool no se corta).
- 2026-11-08 · Opus: un `datos/meta/builds.json` cortado (JSON inválido) tumbaba `draft.py` y la recomendación en champ select. Arreglado: sin build, el draft sigue.
- 2026-11-08 · DeepSeek: en las 284 partidas de score.py no hay ninguna con `teamPosition` vacío ni sin rival de línea, y para cozi `individualPosition` difiere del asignado en 0/284 (solo 6 ajenos, ninguno su rival): el «Duelo» identifica bien al rival de línea.
- 2026-11-08 · Opus: la Live Client Data puede traer `activePlayer`/`allPlayers`/`gameData` en null al cargar; `.get(k, {})` no protege (la clave existe). Tumbaba los avisos en vivo; arreglado con `get(k) or {}`.
- 2026-11-08 · Opus: en la ventana del companion, una excepción en el bucle dejaba la fase vieja: repetía el evento de fase y el mismo error cada 3 s (4 y 4 en 4 vueltas) sin subir la espera. Ahora el estado se actualiza fuera del `try` (como la consola) y el error repetido sale una vez.
- 2026-11-08 · Opus: tu WR por primer ítem: Ekko Ocaso 49% (33–64, n=35) contra Liche 61% (41–78, n=23); Yone Rey Arruinado 52% (n=27) contra Filo de la Tormenta 70% (n=10). Intervalos cruzados y puede ser matchup: pista.
- 2026-11-08 · Opus: era matchup: contra magos, Ekko Ocaso 55% (11/20) y Liche 50% (8/16); la ventaja de Liche venía de luchadores (5/5). Yone contra magos: Rey Arruinado 62% (13/21); el 70% de Filo viene de asesinos/tanques (n=6).
- 2026-11-08 · Opus: en tus derrotas lo que más baja tu score es muertes (34 de 130), línea (34) y KP (32); en victorias lo que más sube, muertes (58) y línea (47).
- 2026-11-08 · DeepSeek: `clave` de `score.resumen()` engaña en 11/284 (victoria con todo z<0: 6; derrota con todo z>0: 5): «lo que más te subió/bajó» con el signo equivocado. Propongo `clave = None` cuando el extremo no tenga el signo del resultado (más correcto que |z|<0.25, que pillaba 29 incluyendo 18 con signo correcto).
- 2026-11-08 · Opus: counters medidos de Sylas mid: Fizz 1-2, Viktor 1-2 (CS −28 al 14) y Qiyana 2-3 (CS −20, 1.4 muertes antes del 6) contra tu media con Sylas de CS −7.6 y 0.6 muertes. Contra Viktor con cualquiera, 1-7 y CS −17 (rol −3). n ≤ 8: pista.
- 2026-11-08 · Opus: muertes del 14 al 25 en tus 282 partidas: 0–2 → 68% (59–75), 3+ → 43% (35–50); 0/1/2 → 84/74/59%. El 82/57 es el subgrupo con línea y equipo ≥ 0 al 14 (se reproduce). Asociación, no causa.
- 2026-11-08 · Opus: en 11 de tus 28 rivales de mid con 3+ partidas llegas al 6 abajo de nivel en promedio (Fizz, Orianna, Diana, Vex, Qiyana…): contra esos, «no salgas del 6 con un nivel abajo» va primero en champ select.
- 2026-11-08 · Opus: tilt (`score.tilt()`, sesión = partidas a menos de 90 min): llegaste 18 veces a 2 derrotas seguidas en una sesión y paraste en 12; las 6 que seguiste, 3-3 (19–81%). Sin sesión (días distintos) la partida tras 2 derrotas va 36/54 = 67%: no hay tilt medible; ya paras solo.
- 2026-11-08 · Opus: contra Viktor (1-7 con cualquier campeón) llegas al 14 con CS −17 (rol −3) pero oro parejo (−120 contra −118): pierdes farm, no la línea. Ekko va 0-3 contra Aurelion Sol con +1255 de oro al 14: ese counter no se explica por el early (n=3, pista).- 2026-11-08 · Opus: el cliente (LCU `/lol-ranked/v1/current-ranked-stats`) da el LP fresco sin key: Master 15 LP, 186-157 (54%) en solo/dúo. La división de Master+ viene como «NA».
- 2026-11-08 · DeepSeek: `resumen_fin()` (iteración 6) lee `config.json` vía `meta_fase()`; un config malformado hace que, en consola, el companion se salte `post_partida()` (descarga + revisión) en silencio al terminar. Menor.
- 2026-11-08 · Opus: el nombre sin #tag en los eventos en vivo contaba las muertes de un homónimo del otro equipo como tuyas; ahora solo vale si nadie más lo comparte.
- 2026-11-08 · Opus: `summonerName` en la Live Client Data puede venir sin #tag; meterlo siempre en tus nombres dejaba contar las muertes de un homónimo. Ahora solo el riotId completo vale siempre.
- 2026-11-08 · Opus: en 6 de tus 10 rivales de mid más frecuentes el pick recomendado y la alternativa quedan a < 2 puntos de estimado: ahí el draft no separa tus picks.
- 2026-11-08 · Opus: tu media de nivel al 6 contra un rival (3+ partidas) no anticipa la siguiente: leave-one-out en 155 partidas, media < 0 → abajo al 6 14%, ≥ 0 → 13%; con < −0.2, 0% contra 17%. Corrige el «11 de 28 rivales… va primero».
- 2026-11-08 · Opus: de tu media contra un rival, solo las muertes antes del 6 anticipan la próxima partida contra él (r 0.37 temporal, n=77, p×5 = 0.01); oro/CS/XP al 14 y nivel al 6 por rival predicen peor que tu media del rol (`anticipa.py`).
- 2026-11-08 · DeepSeek: permutación leave-one-out confirma `corte6.py` (nivel6 por rival: 14% vs 13%, p=0.96) y mide `muertes6` por rival: corte media ≥1 → muero <6 en 69% vs 46%, p=0.13 (pista débil, no da para subirlo). Menor sin arreglar de e705b0c: `minions10()` con dict sin `campeon`/`minimo` da KeyError en `aviso_minions` (GUI).
- 2026-11-08 · DeepSeek: `anticipa.py` (f8f7c13) correcto y robusto: muertes6 aguanta 4+ anteriores (r 0.34–0.40) y el control por campeón no lo explica (p 0.002→0.004). Menor: los p no se reproducen entre corridas porque itera un set sin ordenar (`for pos in {g["pos"] …}`); r y n sí estables. Sugerencia: `sorted(...)`.
- 2026-11-09 · DeepSeek: en la app web, `draft_json` manda `lineas` pero `index.html` no lo lee (renderiza desde `rec.ficha`, línea 80): payload muerto y `lineas_ficha` corre de más en cada champ select (menor).
- 2026-11-09 · DeepSeek: el pie de Perfil «20 partidas mueven el WR ±11 por azar» es 1 error estándar, no un IC (95% = ±22): subestima el ruido a medias. Sugerencia: «±22 (95%)» o aclarar «1 SE».
- 2026-11-09 · DeepSeek: en 5f590c6 el pie queda bien (±22 al 95% con n real, «Sin partidas» con n=0); menor: con n=1 la misma fórmula da «±98 (95%)», honesto pero inservible con muestras chicas.
- 2026-11-09 · DeepSeek: en 4355eaa el timeline roto ya no vacía Perfil (None solo para esa partida, verificado y con prueba `test_ds_score`); queda un hueco menor: el `except` no cubre `OSError`, así que un timeline ilegible (permiso/borrado) aún vaciaría Perfil vía `rendimiento()`.
- 2026-11-09 · DeepSeek: el humo del `.exe` (ef71e63) sale 0 y el binario v0.1.2 responde `/api/estado`; único hueco: si hay otra instancia de `Companion.exe` abierta, `ports[0]` puede leer su puerto y dar un falso OK (una foto previa de netstat lo cubre).

## Decisiones
- 2026-11-09 · Opus: `Companion.exe` v0.1.0 es la app web (`companion_web.py`), no tkinter. Lee `scripts/web` del repo si está junto a él (se actualiza sin recompilar) y si no, la copia empaquetada.
- 2026-11-09 · Opus: la franja en partida y la línea al terminar de la app web usan las tarjetas del canvas de ChampSelect (6 / 10 / 14+), porque el Diseñador quitó del canvas sus ventanas de franja y post-partida. Si el usuario aprueba otro diseño, se cambia solo `index.html`.
- 2026-11-07 · Configuración: Opus construye y hace los commits; DeepSeek-Pro revisa cada commit. Tope de DeepSeek: $5.
- 2026-11-07 · Opus: el pick se recomienda con un estimado encogido (M=10) hacia tu WR del campeón, no con el récord crudo contra el rival.
- 2026-11-07 · Opus: la meta del mid game baja a ≤ 2 muertes del 14 al 25 (también en revision.py) y queda como monitor. La regla nueva: no pelear si no hace falta antes de que salga un objetivo.
- 2026-11-07 · Opus: mid sigue siendo el rol principal; si toca top, Mordekaiser o Yone (no Sylas).
- 2026-11-07 · Opus: si esperas perder la línea, Yone antes que Ekko (aguanta ir abajo).
- 2026-11-07 · Opus: regla nueva en prioridad 1: si ya vas abajo, cuida el farm (bajo torre, no roamear a costa de oleadas) más que evitar muertes.
- 2026-11-07 · Opus: esa regla se precisa: abajo, lo que pesa es la XP; quedarse en rango de XP de cada oleada y no perder tiempo fuera de la línea.
- 2026-11-07 · Opus: se corrige la anterior con `xp.py`: el tiempo fuera de la línea no es donde se va la XP. Abajo: no morir otra vez y castigar al rival.
- 2026-11-07 · Opus: regla de placas en prioridad 1 (pista): antes del 14 no te vayas a base ni roamees con la oleada rival entrando a tu torre.
- 2026-11-07 · Opus: "castigar" se precisa con `castigo.py`: el kill en tu línea cuando el rival se pasa (pista), no el gank forzado con jungla.

- 2026-11-07 · Opus: se quita la regla "no te vayas a base con la oleada entrando" (placas perdidas fuera de línea no separan).
- 2026-11-07 · Opus: regla nueva en prioridad 1: al sacar ventaja de nivel, asume que viene el gank (mira el río, no empujes sin ver al jungla).
- 2026-11-07 · Opus: se precisa: con ventaja de nivel, tradea hasta la mitad de la línea y no persigas más allá sin ver al jungla rival.
- 2026-11-07 · Opus: en el PLAN, las placas perdidas en tu línea pasan a "sin causa clara" (revisión de DeepSeek).
- 2026-11-07 · Opus: la regla de "ventaja de nivel → gank" se acota a top/bot; en mid queda la general (no seguir al rival a su jungla).
- 2026-11-07 · Opus: `revision.py` ya no muestra `turretPlatesTaken` (no son tus placas) y suma "muertes <14 pasado el río" como monitor sin meta.
- 2026-11-07 · Opus: regla nueva para Sylas en el PLAN: no tradear ni roamear a costa de oleadas antes del 10 (meta 69+ minions al 10).
- 2026-11-07 · DeepSeek: el corte de Sylas (>68 min@10 → 74% vs 32%) es gradiente estable (64→61%, 72→77%), no umbral afortunado; top son 11/90 (ruido) y contra Qiyana farmea menos (56, n=5). El "en tu lado mueres menos" (×0.75) cruza 1 (bootstrap 0.49–1.06): es "no mueres más".
- 2026-11-07 noche · Opus: no se agrega regla "no tradear desde nivel 1" (los datos no la respaldan); entra al PLAN como pista: no salir del 6 con un nivel abajo.
- 2026-11-07 noche · Opus: la meta de Sylas (> 50% de sus partidas con 69+ minions al 10) entra a `revision.py`.
- 2026-11-07 noche · Opus: "control ward en cada regreso" deja de ser regla (sin respaldo); queda como hábito barato y monitor sin meta. Sale de las metas de la semana 1.
- 2026-11-07 noche · Opus: `draft.py` solo corre su CLI bajo `__main__` (para poder importarlo); el companion saca los nombres de campeón de `datos/raw` (sin red), y el rival sin rol conocido se resuelve mostrando todos los ya elegidos.
- 2026-11-07 noche · Opus: `revision.py` corre al importarse, así que se prueba como proceso (humo sobre `datos/raw`) en vez de reescribirlo; la prueba se salta si no hay datos.

- 2026-11-07 noche · Opus: la meta de Sylas en `revision.py` solo marca ✅/❌ con n ≥ 10 Sylas en la ventana (sugerencia de DeepSeek); con menos queda como monitor.
- 2026-11-08 · Opus: pool y meta de minions al 10 salen de `config.json` (opcional, ignorado por git); sin él, pool = tus 3 más jugados y sin meta de minions. Con el config de cozi la salida de `revision.py 20` es idéntica a la de antes.
- 2026-11-08 · Opus: `convertir.py`/`linea.py` sin argumento enfocan tu campeón más jugado (Sylas para cozi); los análisis viejos de Ekko se rehacen con `convertir.py Ekko`.
- 2026-11-08 · Opus: `rol.py` compara tus 2 roles más jugados; el campeón aparte del 2.º rol es el de mejor WR con 3+ partidas (Mordekaiser para cozi, no Yone, que es el más jugado en top), y el pool sale de `config.json`.
- 2026-11-08 · Opus: la captura en vivo solo guarda (no analiza todavía): primero hay que juntar partidas; el análisis (p. ej. oro contra el rival minuto a minuto con ítems) va después.
- 2026-11-08 · Opus: el campeón aparte de `rol.py` se elige por WR encogido (M=10, como `draft.py`), no por WR crudo: con 3+ partidas un 3/3 ganaba solo. Sin respuesta de DeepSeek; decidí yo.
- 2026-11-08 · Opus: el aviso de nivel usa la foto de cada 30 s (no un sondeo aparte), solo con `position` (en normales no avisa) y una vez por partida; `capturar(archivo, d)` recibe la foto.
- 2026-11-08 · Opus: la racha de oro bajo usa siempre las últimas 5 partidas (aunque corras `revision.py 1`), mide el nivel con la foto del minuto 6 (como el aviso en vivo) y marca «pista» sola si los intervalos de Wilson se cruzan.

- 2026-11-08 · Opus: tras un reinicio del cliente, el companion sigue la última fase real (no `None`): si era `InProgress`, sigue grabando del puerto 2999 en el mismo archivo.
- 2026-11-08 · Opus: «counter duro» en draft = techo Wilson del récord del pick contra el rival < tu WR base (el criterio de los bans); la alternativa es el siguiente por estimado que no lo sea. El aviso no cambia la recomendación, solo la anota.
- 2026-11-08 · Opus: el humo del flujo simula solo `urlopen`, reloj, sleep y la descarga (sin red ni key); `draft` y `revision.py` corren de verdad sobre datos de fixture.
- 2026-11-08 · Opus: el aviso de minions al 10 usa `scores.creepScore` en vivo (incluye monstruos; sin cotejar con una partida real) contra la meta de `config.json`; avisa solo con ese campeón, entre 10:00 y 11:00, una vez.
- 2026-11-08 · Opus: no se usa lolalytics: su robots.txt prohíbe ClaudeBot, anthropic-ai y Claude-Web, y esta herramienta la construye Claude. Las builds de los mejores saldrán de la Riot API (cuando haya key).
- 2026-11-08 · Opus: el score se normaliza contra los 10 de la partida y luego se le resta la media de su rol (sacada de los jugadores ajenos), para que un support o un jungla no salgan mal por CS o bien por objetivos. Es monitor sin meta: sube al ganar.
- 2026-11-08 · Opus: la post-partida de la ventana va en un hilo (uno a la vez); el reload de `draft` y `datos_draft` comparten un lock; si la revisión llega en champ select, se guarda y se muestra al empezar la partida.
- 2026-11-08 · Opus: «los mejores con un campeón» = los 2 primeros por LP de Challenger/GM en la1 y kr con maestría jugada hace < 14 días (no un ranking de onetricks, que no es accesible). La build es la moda por posición, no la de un solo jugador.
- 2026-11-08 · Opus: sin la build de los mejores (key caducada), champ select muestra la tuya con esa etiqueta; en cuanto `--pool` corra con key, manda la de los mejores.
- 2026-11-08 · Opus: los avisos de la GUI son dict `{texto, tipo, minuto}` solo en la cola; `aviso_nivel`/`aviso_minions` siguen devolviendo texto (la consola y las pruebas los usan así). Los avisos del draft siguen como texto dentro de su tarjeta.
- 2026-11-08 · Opus: el duelo de línea compara tu score con el de tu rival de la misma posición (empate = lo pierdes); sin posición no hay duelo.
- 2026-11-08 · Opus: tu WR con el primer ítem de los mejores sale en champ select (4.ª línea de la build) solo si tienes partidas con ese ítem y sin él; siempre con «pista, no causa».
- 2026-11-08 · Opus: la meta de la fase en vivo no trae «oro al 14» (la Live Client Data API no da el oro del rival); solo nivel contra tu rival y CS. Va en la línea de perfil, no en el cuerpo, para no tapar una revisión pendiente.
- 2026-11-08 · Opus: el duelo de `score.py` sigue con `teamPosition` (rol asignado), no `individualPosition`: cambiaría 0/284 partidas y Riot a veces trae «Invalid».
- 2026-11-08 · Opus: el WR por primer ítem se muestra también contra la clase más común del rival (`tags[0]` de Data Dragon), no por rival exacto (n por rival es de 1–3).
- 2026-11-08 · Opus: la «clave» de cada partida en `score.resumen()` es el componente que más pesó en tu score, no la causa del resultado; la GUI debe decirlo así.
- 2026-11-08 · Opus: un counter del pick = rival con 3+ partidas cuyo estimado encogido (M=10) queda bajo tu WR con ese campeón; se marca `pocas` con n < 5 (DeepSeek pedía n ≥ 5, pero con eso casi no quedan). Lo cualitativo del matchup no se infiere: sale solo de `datos/matchups-notas.json`, que llenas tú.
- 2026-11-08 · Opus: el aviso de muertes 14–25 salta con 2 (antes de la 3.ª, que es la que pesa), una vez, y cita el 68/43 de todas tus partidas, no el 82/57 (solo vale con línea y equipo arriba). Cuenta eventos `ChampionKill` de la foto, sin estado; `VictimName` sin cotejar con una partida real.
- 2026-11-08 · Opus: las reglas de «cómo jugarlo» son una tabla fija en `draft.py` con los números del PLAN (no se recalculan en vivo); al cambiar el PLAN hay que actualizarla.
- 2026-11-08 · Opus: «una línea al terminar» sale de la última foto en vivo (hasta 30 s antes del final), no de la Riot API: así funciona con la key caducada; la revisión completa la reemplaza cuando llega.- 2026-11-08 · Opus: el LP de la ventana sale del cliente (se lee al entrar a champ select), no de `perfil.json`; sin cliente cae a `perfil.json`.
- 2026-11-08 · Opus: el cotejo de muertes solo marca el caso «0 eventos tuyos con muertes en el marcador» (formato de nombre desconocido), no exige igualdad exacta.
- 2026-11-08 · Opus: ante un homónimo en la partida, el aviso de muertes 14–25 prefiere no contarte (el cotejo de la línea final lo dice) a contar muertes ajenas.
- 2026-11-08 · Opus: la regla del 6 ya no sube al frente por rival en champ select (era ruido, `corte6.py`); queda como regla general con su número.
- 2026-11-08 · Opus: en «Cuidado con el rival», las muertes antes del 6 van solas («tiende a repetirse contra él»); oro/CS/nivel juntos y marcados «no se repite». `draft.ANTICIPA` fijo a mano.
- 2026-11-09 · Opus: la app nueva es web local (`http.server` en 127.0.0.1 + HTML del canvas, abierta con Edge `--app`), reutiliza el `trabajador` de `companion_gui.py`; tkinter queda de respaldo. Valida `Host` y se cierra sola sin la ventana (DeepSeek).

## Para el usuario (cuando vuelva)
- Cambio: en champ select, «Cuidado con <rival>» ahora separa lo que sí se repite contra ese rival (tus muertes antes del 6) de lo que no (oro, CS y nivel: varían de partida a partida). Si ves muertes antes del 6 por encima de tu media, juega el nivel 1–6 con más cuidado. Recompila `Companion.exe`.
- Cambio: champ select ya no dice «contra este rival llegas al 6 con −0.3 niveles»; ese promedio no anticipaba nada. Recompila `Companion.exe`.
- Nuevo: si champ select dice «casi igual que Ekko (54%): cualquiera de los dos», tus picks no se separan contra ese rival (pasa con 6 de tus 10 rivales de mid más frecuentes): elige el que mejor manejes. Recompila `Companion.exe`.
- Nuevo: si en tu primera partida la línea al terminar dice «no cuadran tus muertes con los eventos», el aviso del 14 al 25 no te está contando: avísale a Opus. Resumen de la noche en `RESUMEN-NOCHE.md` (Turno 6).
- Nuevo: la ventana muestra tu LP real aunque la key haya caducado («cozi#1134 · Master 15 LP · 186-157 (54%)»), leído del cliente al entrar a champ select. Recompila `Companion.exe`.
- Nuevo: al terminar la partida, la ventana (y la consola) da una línea aunque la key haya caducado: «Min 31 · Sylas 5/4/7 contra Zed · CS 245 · muertes del 14 al 25: 3 (meta ≤ 2) ✕». Recompila `Companion.exe`.
- Nuevo: en champ select, bajo «Cómo jugar», la ventana muestra «Cuidado con <rival>» (tu récord contra él y tu oro/CS al 14, nivel al 6 y muertes antes del 6 contra tu media, más tus notas) y los counters de tu pick con su récord. Recompila `Companion.exe` para tenerlo.
- Nuevo: del minuto 14 al 25 la franja en partida muestra «Muertes desde el 14: N (meta ≤ 2)», y al llegar a 2 el companion te avisa «juega con objetivo» (con 3+ tu WR baja de 68% a 43%). Recompila `Companion.exe` para tenerlo. Si en tu primera partida no cuenta tus muertes, avísale a Opus: el nombre en los eventos no se pudo cotejar sin una partida real.
- Nuevo: si quieres notas propias por rival en champ select («pega fuerte al 3»), crea `datos/matchups-notas.json` con `{"Zed": "tu nota"}`. Sin el archivo no pasa nada. La ventana ya te dice por qué te recomienda el pick (recompila `Companion.exe` para tenerlo).
- Corrige lo de abajo: no cambies el primer ítem por esos números. Comparando contra el mismo tipo de rival (magos), Ekko gana igual con Ocaso (55%) que con Liche (50%), y Yone abre bien con Rey Arruinado (62%). `builds.py --pool` ahora lo muestra («Solo contra magos…»).
- Nuevo: `builds.py --pool` (sin key) te da tu WR por primer ítem con cada campeón. Con Ekko abres más con Ocaso y Alba (49%) que con Liche (61%); con Yone, Rey Arruinado 52% contra Filo de la Tormenta 70% (10 partidas). Pista, no causa: puede depender del rival.
- Nuevo: en partida, la ventana del companion muestra arriba tu nivel contra el de tu rival y tu CS (con la meta al 10 si juegas Sylas), cada 30 s. Y la etiqueta «key ok / falta RIOT_KEY» se actualiza sola tras `setx`. Recompila `Companion.exe` para tenerlo.
- Nuevo: cuando haya build de los mejores (con key), champ select te dice además tu WR cuando abres con su primer ítem contra cuando abres con otro («Tú con Rey Arruinado primero: …»). Es pista, no causa.
- Nuevo: en la ventana del companion, los consejos en partida (nivel abajo, CS al 10) salen en azul y los errores (key caducada, descarga) en naranja. Recompila `Companion.exe` para tenerlo.
- Nuevo: `score.py` ahora dice si le ganaste el duelo a tu rival de línea (columna «Duelo»): hoy lo superas en 44% de tus partidas, 35% en las derrotas.
- Nuevo: aun sin key, `builds.py --pool` deja tu build por campeón y champ select (draft.py y la ventana) te la muestra bajo el pick («Tu build (aún sin la de los mejores)»). Con una key nueva, corre `--pool` otra vez y sale la de los mejores.
- Nuevo: en la ventana del companion, bajo la recomendación sale la build de los mejores de ese campeón (cuando corras `builds.py --pool` con una key vigente), y si pones cola enseguida tras una partida el champ select ya no espera a que termine la descarga. Recompila `Companion.exe` para tenerlo.
- Nuevo: `python scripts/builds.py Yone mid` te da la build de los mejores de Yone (Challenger/GM de LAN y Corea) junto a la tuya; `builds.py --pool` hace lo mismo con todo tu pool y deja la build lista para que `draft.py`/el companion te la muestren al recomendarte un pick. Necesita una `RIOT_KEY` vigente la primera vez (unos minutos; luego queda en caché).
- Nuevo: `python scripts/score.py` te da un score por partida contra tu equipo y la partida (50 = típico de tu rol; cada 15 puntos, una desviación), tu puesto entre los 10 y en tu equipo, la tendencia y qué componente te baja. También sale en `revision.py` y en la ventana post-partida.
- Nuevo: con Sylas, si al minuto 10 llevas menos de 69 de CS, el companion te avisa («no roamees ni tradees a costa de oleadas hasta el 14»). Sale de `minions10` en tu `config.json`; recompila `Companion.exe` para tenerlo en la ventana.
- Nuevo: en champ select, si el pick recomendado tiene menos de 5 partidas en el rol o es un counter duro del rival (incluso en el mejor caso queda bajo tu WR base), `draft.py` y la ventana lo avisan en rojo y te dan una alternativa.
- Nuevo: si el cliente de LoL se reinicia a media partida, el companion sigue grabando la misma partida y no repite avisos; con el cliente cerrado sondea cada vez menos (hasta cada 30 s). Recompila `Companion.exe` para tenerlo.
- Nuevo: si 3 o más de tus últimas 5 partidas llegan al 14 con oro < 0, `revision.py` y la ventana post-partida del companion lo marcan con 2 metas: XP al 14 a −746 o mejor contra tu rival y llegar al 6 sin nivel abajo.
- Nuevo: entre el minuto 5 y el 7, el companion te avisa si vas abajo de nivel contra tu rival de línea («no tradees hasta igualar»). Solo en ranked/draft (necesita la posición); reinicia el companion o recompila `Companion.exe` para tenerlo.
- Nuevo: deja abierto `python scripts/companion.py` en una terminal mientras juegas. En champ select te recomienda el pick contra tu rival y, al terminar, baja la partida y la revisa (si la key caducó, te dice «renueva RIOT_KEY»).
- Para revisar tus primeras muertes: `python scripts/partida.py <id> --early` (minuto a minuto del 1 al 12, con tu nivel contra el de tu rival).
- Yone contra Ekko: las dos muertes 1v1 (2:52 y 5:10) fueron yendo 1 nivel abajo desde el 3. En tus datos el problema no es tradear temprano, es quedar abajo de nivel al 6 (44% de WR).
- Control wards: no te obsesiones; en tus datos (y en los de los demás jugadores de tus partidas) no bajan los ganks. La regla 2 de la tarjeta ya no es prioridad.
- En champ select: `python scripts/draft.py <rival> [rol]` (p. ej. `draft.py Viktor mid`).
- Al terminar cada sesión: `python scripts/descargar.py` y luego `python scripts/revision.py` (o `revision.py 10`).
- Si la key caducó, `descargar.py` abre el portal de Riot: copia la key, `setx RIOT_KEY <key>` y córrelo otra vez (ya no hace falta reabrir la terminal).
- Tu `config.json` (copia de `config.ejemplo.json`, con tu pool y la meta de Sylas) ya está en la carpeta y no se sube a git.
- Hay 4 `.pyc` de `scripts/__pycache__/` rastreados en git (ya están en `.gitignore`, pero Opus no tiene `git rm`): corre `git rm -r --cached scripts/__pycache__` y haz commit antes del push. Importa también por privacidad: el bytecode trae tu ruta `C:\Users\…` completa (lo halló DeepSeek).
- El CI (`.github/workflows/pruebas.yml`) arranca solo al hacer push.
- Opus no puede llamar a `ask-deepseek.ps1` (el permiso bloquea PowerShell anidado). Si quieres que lo use, permite ese comando.
- Antes del push: el historial de git aún trae tu ruta `C:\Users\…` y el saldo de DeepSeek en commits viejos (ya no en los archivos). Si te importa, reescribe el historial o déjalo así; no hay keys.
- Nuevo: con `companion.py` abierto, cada partida queda grabada en `datos/vivo/` (fotos cada 30 s, solo en tu PC). Reinicia el companion para que tome el cambio.
