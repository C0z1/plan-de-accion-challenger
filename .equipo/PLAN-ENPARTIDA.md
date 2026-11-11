# Plan en partida (franja + avisos + En vivo), v0.11 a v0.13

Hecho por Fable (planificador) el 2026-11-10, revisado por Opus. Complementa `PLAN-APP.md`.

## Diagnóstico (comprobado con la partida grabada `datos/vivo/20261109-175517.jsonl`, 71 fotos, 34 min)

1. Los avisos no se ven jugando: solo salen en la ventana de Racha; la franja no los muestra. `ESTADO["aviso"]` guarda uno y el nuevo pisa al anterior.
2. Casi no hay avisos: en esa partida saltó uno solo (muertes, min 16:57, 30 palabras). En partida se lee algo de 8 palabras o menos.
3. Las reglas en partida son del autor: el tope «≤ 2 muertes» y la pieza de la franja son fijos, la meta de CS exige `config.json`, las 3 reglas de En vivo están en el JS. `draft._numeros` y `vistas.reglas_perfil` ya calculan las del usuario, pero no llegan a la partida.
4. No se puede medir si ayuda (el ping solo trae 3 booleanos).
5. Corpus de prueba mínimo: 1 partida completa.
6. Tono: órdenes tácticas («no pelees…») rozan «drawing conclusions for you during gameplay». En partida: hecho visible + tu regla pactada antes; la conclusión, después.

## Funciones (valor por hora)

| # | Qué | Esfuerzo |
|---|---|---|
| F1 | Aviso corto en la franja (≤ 48 caracteres, 12 s, 1 a la vez, ≥ 90 s entre avisos, ≤ 6 por partida; el largo queda en En vivo) | S |
| F2 | `companion.paso_vivo` (lo «por foto» del trabajador como función pura) + `scripts/replay.py` con `--validar` y prueba dorada | S–M |
| F3 | Regla de hoy personal en partida (la que más te cuesta, con tus cifras; «consejo» sin cifra con < 10 partidas) | M |
| F4 | Momento muerto: al morir, la franja deja solo tu regla y el próximo objetivo (necesita sondeo de 10 s) | S–M |
| F5 | Contadores de avisos en el ping opt-in y «¿sirvió?» al terminar | S |
| F6 | Prioridad por fase y tope de 4 piezas + 1 aviso; redibujar solo si cambia | S |
| F7 | Tecla para ocultar (GetAsyncKeyState) — EN ESPERA hasta saber cómo lo toma Vanguard; hoy basta el interruptor | S |
| F8 | Historial de avisos de la partida en En vivo | S |
| F9 | Meta de CS al 10 automática por campeón (mediana de tus victorias, 8+ partidas), sin `config.json` | M |
| F10 | Objetivos mejor contados (tipo de dragón, punto de alma; cotejar barón/Anciano con el parche) | S |
| F11 | Revisión local sin key desde las fotos en vivo, al instante | M |
| F12 | Regla puesta por tu coach + informe (semilla de ingresos B2B) | M |

Descartado: build adaptativa, timers de campamentos o de hechizos/ultimates rivales, probabilidad de victoria, clips, sonido.

## Franja

- Máx. 4 piezas + 1 aviso; ≤ 22 caracteres por pieza; orden fijo: regla, línea, objetivos, aviso. Nada parpadea.
- Prioridad por fase: 0–6 (Nv, CS/meta, regla de línea, Dragón si ≤ 90 s) · 6–14 (regla, Oro ±, CS, Dragón, Nv si vas abajo) · 14–25 (regla, Dragón, Barón desde 3 min antes, Oro del equipo) · 25+ (Barón, Dragón/alma, Oro del equipo) · muerto (regla, próximo objetivo, aviso).
- Glifos además del color: ▼ abajo, ! urgente, ✓/✕ al cerrar una regla.
- Nunca: cooldowns rivales, campamentos, posiciones, isDead/respawn de rivales, probabilidad de victoria/MMR, órdenes sobre lo que no ves, juicios de compañeros, anuncios, cifras inventadas.

## Técnico

- Sondeo a 10 s en memoria, disco cada 30 s (medido: < 1 ms por foto). Vigilar el peso de `/api/estado` al subir la cadencia.
- Presupuesto: CPU reposo < 1 %, en partida < 1 % de un núcleo, FPS sin diferencia medible (medir en partida real, A6).
- Fixtures: la partida de 71 fotos ANONIMIZADA (Riot ID de 9 personas ajenas → J1..J10).
- Hallazgos del replay: las muertes del marcador cuadran con los eventos (7/7); los timers de dragón cuadraron con los 5 DragonKill.

## De pago vs gratis

Gratis siempre: todo lo de la partida (franja, avisos, regla de hoy, En vivo, 3 momentos, runas). De pago después y solo si alguien lo pide: historial largo de cumplimiento de reglas, informe para coach, reglas puestas por el coach y panel de academia (F12).

## Hoja de ruta

- v0.11 «El aviso se ve»: F2, F1, F6, F8, F5, A6. Acepta si `replay.py --validar` pasa en la partida grabada, el aviso de muertes sale en la franja con ≤ 48 caracteres, nunca más de 4 piezas + 1 aviso, FPS medidos, textos sin órdenes tácticas.
- v0.12 «Tu regla, no la mía»: F3, F9, sondeo 10 s + F4, F10. Acepta si con datos de otra cuenta salen sus reglas (nunca números del autor) y sin `config.json`.
- v0.13 «Cierra el ciclo»: F11, «¿sirvió?», botón para donar una partida anonimizada como prueba, prototipo F12.
