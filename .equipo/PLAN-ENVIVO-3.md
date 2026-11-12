# Plan En vivo, ronda 3 (Fable) · v0.14.3 local

Siguen vigentes las prohibiciones de `PLAN-ENVIVO.md` sección 5. El hallazgo 16 ya estaba cerrado en la 0.14.2 (`overlay.py`, commit 10d0d52).

## 1. Decisiones

| Hallazgo | Decisión | Cómo, o por qué no |
|---|---|---|
| 13 muertes del mismo tick | Arreglar | En `unir_eventos`, la clave es el evento completo menos `EventID`. |
| 14 reordena en cada foto | Arreglar | Unir solo si hubo reinicio: `GameStart` con `EventTime > 0`, o menos eventos que `previos`. Si no, `d` intacta. |
| 15 juego colgado | Descartar | Un cuelgue con el mismo `gameTime` no se distingue de una pausa; si el juego deja de responder, `visible()` oculta la franja a los 30 s y S3 lo marca. |
| 16 dibujo a medias | Cerrado | Ya está en el código. |
| 17 `salud.py` `edad_proceso or` | Arreglar | `None` cuenta como viejo, 0 cuenta como recién arrancado. |
| 18 `reconectar` sin fase | Arreglar | `salir`/`reconectar` exigen PRACTICETOOL y fase `InProgress` o `Reconnect`. |
| Franja vacía hasta ~3:30 | Tocar | En `overlay.elegir`, si no quedó ninguna pieza, se muestra el próximo objetivo (dragón o barón). |

## 2. DeepSeek
- **DS-1** (`test_ds_eventos_pausa.py`, 6 casos): dos kills del mismo tick; sin reinicio la lista queda idéntica y en orden; reinicio detectado solo por menos eventos; doble reconexión sin duplicados; `GameStart@0` + reinicio con `DragonKill`; otra partida intacta.
- **DS-2**:
  - `test_ds_franja_vida.py`, 4 casos: franja vacía muestra el dragón; con rival no se agrega; con objetivos apagados `[]`; muerto/ARAM sin cambio.
  - `test_ds_salud.py`, 3 casos de S8: `edad_proceso` 0 da AVISO; `None` da FALLA; 200 da FALLA.
- **DS-3**: revisión del diff (sección «Ronda 3», ≤ 20 renglones) y `deepseek-al-llegar.md` actualizado.

## 3. Opus
A1 `unir_eventos` (13 y 14) · A2 franja vacía · A3 salud 17 · A4 candado de fase en `dev_practica` (18) + 2 casos · A5 suite, hallazgo 15 aceptado, 0.14.3 local · A6 prueba real 3 en `datos/salud/prueba-3.md` · A7 cerrar lo de DS-3.

## 4. Prueba real 3 (Herramienta de práctica, sin input al juego)
| Paso | Qué hace Opus | Cuenta como OK |
|---|---|---|
| R0 | `reconectar` y `salir` con el cliente en None/Lobby | Se niegan las dos órdenes y la fase no cambia |
| R1 | Abrir la práctica con salud corriendo | Sin franja en la carga; franja ≤ 20 s después de `gameTime` > 0; S5 OK |
| R2 | Timer del dragón a los 60, 150 y 240 s | Coincide con 300 − `gameTime`, ±2 s |
| R3 | Eventos de la Live API vs. último `.jsonl` a los ~4 min | Mismos eventos y mismo orden |
| R4 | Cerrar el juego y reconectar, 2 veces | `GameStart@0` y `MinionsSpawning` 1 vez cada uno; 1 solo `.jsonl`; la franja se oculta ≤ 30 s y vuelve ≤ 20 s |
| R5 | 5 pasadas de salud | Todas OK; CPU < 1 % |

No cubre los hallazgos 13 y 15: el 13 queda cubierto solo por las pruebas sintéticas.

## 5. Solo el usuario
1. Partida normal con `salud.py --cada 60 --foto`: si se reconecta, que dragones y muertes 14–25 sigan contados.
2. FPS con Ctrl+F, franja prendida y apagada: más de 5 FPS de diferencia, avisar.
3. Rival de línea real correcto.
4. Permiso para push y release de la 0.14.3.

**Riesgo:** la guarda de A1 se apoya en una sola observación en práctica (el `GameStart` con tiempo > 0 tras reconectar).
