# Plan «Matchups de muchas partidas» (Fable, 2026-11-13)

Pedido del usuario: que Racha diga cosas que no se consiguen fácil, por matchup y de muchas partidas («Zeri gana el nivel 6 a Miss Fortune…»), y que recomiende runas y builds por matchup.

## 1. Veredicto: sí, en versión chica
Hueco real: con un campeón poco jugado Racha no tiene nada. Lolalytics/U.GG dan WR, runas e ítems contra un rival; nadie publica «quién gana el nivel 6 en A vs B» (lo de iTero no se pudo confirmar fuera de su app). Racha gana con: ventanas por nivel con n e intervalo, TU dato al lado, frases cortas en la franja. No competir en cobertura total: tu pool contra sus rivales frecuentes.

## 2. Datos
Única fuente legal y viable: rastreo propio de match-v5 + timeline (datasets públicos viejos; raspar sitios va contra sus términos).
| Key | Límite | Partidas/día | Nota |
|---|---|---|---|
| Desarrollo | 20/s y 100/2 min | ~35.000 teóricas | caduca cada 24 h |
| Personal | 20/s y 100/2 min | ~35.000 por ruteo (~100.000 con americas+europe+asia) | no caduca; «developer or a small private community» |
| Producción | 500/10 s y 30.000/10 min | ~2 millones | prototipo y revisión; no hace falta hoy |
Rastreo por campeón: ladder Master+ de LA1, KR y EUW (`builds.mejores`), maestría en el campeón, últimas 30–50 ranked, timeline solo si jugó ese campeón en el rol. ~100 jugadores por campeón ≈ 3.000–4.000 partidas (1–3 h). Muestra: ±10 pp con n≈100, ±7 pp con n≈200. Mínimos: n≥50 para WR y oro; ≥30 muertes de línea por ventana; parche actual + anterior. Sesgo: lado A = mains → etiqueta «mains Master+» y WR contra el WR base de A. Sin guardar crudos (~1 KB por fila). Corre en la PC del admin con key personal; el backend solo distribuye.

## 3. Métricas
Fila por partida (`datos/meta/matchups-filas.jsonl`): parche, región, A, B, pos, win, gd/xpd/csd en 5/10/14, LEVEL_UP de A y B, muertes de línea antes del 14 (t, víctima, niveles, solo), runa clave + página + fragmentos, primer legendario, core, botas.
Agregado `A|POS|B`: ventanas por nivel de A (1–3, 4–5, 6–8, 9–10, 11+) con Wilson, frase solo si el IC no cruza 50 %; primero a nivel 6; medianas de gd5/10/14, xpd14, csd10; WR si sales abajo al 14; WR del matchup vs base; primer ítem, runa clave y botas del matchup (≥ 20 % de uso, n≥30); `pagina_ids`.
Frases (`matchups.frases(m, max=3)`): «Zeri gana el nivel 6–8 vs Miss Fortune: 58 % de las muertes de línea (n=420)», «MF manda en nivel 1–3: 61 % (n=180)», «Oro al 14: −310 de mediana; aun abajo, Zeri gana 47 %», «Runa más ganadora aquí: Cadencia Letal 54 % (n=160)». Salida `datos/meta/matchups.json`.

## 4. Límites de Riot (developer.riotgames.com/docs/lol; support.riotgames.com/en-us/riot/events/third-party-applications)
Aprobado: datos estáticos previos, estadísticas agregadas (sin jugadores), resaltar decisiones importantes. Prohibido: dictar decisiones, información desconocida de la sesión, sacar conclusiones en partida. En partida: dato previo sin imperativo («Ventana fuerte histórica: nivel 6–8 · 58 % (n=420)»), por reloj fijo o al morir; nunca disparado por el estado del rival. Lista negra: + «pelea», «all-in», «tradea».
Runas: Riot no tiene regla escrita sobre importarlas (LCU no soportado, práctica tolerada; Blitz y Mobalytics lo hacen). Racha ya tiene el botón Importar (solo con clic): corregir el README («solo lee») y que `/api/runas` acepte el rival.

## 5. Fases
- Fase 0 (usuario): pedir Personal API Key. Mientras, dev key de 24 h para probar.
- Fase 1 (0.22.0): `scripts/matchups.py` (`fila`, `agregar`, `frases`, `guardado`, `rastrear`, CLI `--pool`/`--subir`, `bajar`); `draft.ficha` gana `matchup`; la página lo pinta bajo «cuidado» con «mains Master+, parches X–Y».
- Fase 2 (0.22.1): franja (`plan_partida` → `dato`; `inicio` 60–90 s y `extra_muerto`), `/api/runas` con rival, README, lista negra.
- Fase 3: tabla `matchups` y rutas en el backend para amigos sin key; otros roles.
Pruebas DeepSeek (`test_ds_matchups.py`): `fila` (muerte de línea con/sin asistencia, después del 14 ignorada, sin rival, remake, nivel desde LEVEL_UP); `agregar` (ventanas, mínimo n, dos parches, A vs B ≠ B vs A); `frases` (IC cruza 50 % → nada, orden, máx. 3, n en cada una, lista negra, ancho); runas; `guardado` ausente/cortado; regresión de `ficha` e `inicio`.

## 6. Riesgos y decisiones
Riesgos: muestras chicas; sesgo de mains; parche con rework (`--solo-parche`); Riot puede tardar o negar la key personal; cambios en la API de timeline.
Decisiones: 1) pedir Personal API Key (recomendado: sí); 2) runas por matchup con botón Importar y README corregido (recomendado: sí); 3) ventana histórica disparada al llegar tú a ese nivel (recomendado: no en el MVP).

## Revisión de DeepSeek (2026-11-13)

1. Estadística: el sesgo de mains es asimétrico (A es main, B no); filtra ambos main o compara contra base de ambos. n de muertes no es n de partidas; define la unidad de evento y pide n>=50. Wilson: exige cota inferior >50 y corrección por múltiples ventanas, no solo IC que no cruce. Pooling actual+anterior: separa si hubo ajustes a campeón o ítems. Bot 2v2: asigna muerte de línea por víctima ADC en bot, no por killer; incluye kills del support, ignora solo y exige ambos ADC en línea.

2. API: la key personal no caduca pero es revocable y no debe alimentar backend de terceros; los límites son por ruta, no suma simple. match-v5 teamPosition a veces viene vacío; usa rol/lane propio. Timeline LEVEL_UP e ITEM_PURCHASED existen; valida participantId.

3. Política: frases en partida como “gana el nivel 6” al subir de nivel pueden leerse como dictar decisiones; en MVP deja solo ficha en selección con redacción histórica pasiva y sin imperativos. Runas: importar solo con clic explícito, no automatizar.

4. MVP: recorta franja in-game y frases por nivel; deja ficha en selección con WR, oro, runas y build. Sube n mínimos (muertes >=50, partidas >=100) y restringe a ambos ADC main o ajusta por base.


Opus: se aplica (a) WR del matchup contra el WR base de ambos campeones en la muestra; (b) en bot, la muerte de línea se cuenta por la víctima (ADC o support de la línea) con ambos tiradores en bot; (c) frase solo si el piso de Wilson supera 50 % con corrección de Bonferroni por las 5 ventanas; (d) mínimos 100 partidas y 50 muertes por ventana; (e) teamPosition vacío: se descarta la partida; (f) la key personal solo en la PC del admin, el backend distribuye agregados (no la key). En partida: solo dato histórico pasivo por reloj fijo y al morir, nunca disparado por el estado de la partida.
