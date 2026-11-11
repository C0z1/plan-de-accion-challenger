# Anchos de la franja por fase (D-c)

DeepSeek (Sonnet de reemplazo), 2026-11-11. Fuente: las 16 capturas de `datos/vivo/*.jsonl` y `scripts/fixtures/vivo/*.jsonl`, repetidas con `replay.repetir` (con precios, como `--precios`); caracteres = largo del texto unido con « · ». Fase por minuto de juego; «muerto» = `meta.muerto`.

## Franja más larga por fase (todas las capturas)

| Archivo | Minuto | Fase | Caracteres | Texto |
|---|---|---|---|---|
| datos/vivo/20261110-054403.jsonl | 02:12 | 0-6 | 56 | Kills 5 vs 4 · Cuidado Miss Fortune 1/1/3 · Tu KDA 0/1/3 |
| datos/vivo/20261110-052844.jsonl | 13:09 | 6-14 | 53 | Kills 49 vs 27 · Cuidado Shaco 8/14/9 · Tu KDA 3/3/29 |
| datos/vivo/20261109-175517.jsonl | 18:58 | 14-25 | 64 | Muertes 14–25: 2/2 · ▼ Equipo -2100 · ! Dragón 0:51 · Barón 1:02 |
| datos/vivo/20261109-225043.jsonl | 26:40 | 25+ | 45 | ▼ Equipo -10150 · Anciano 4:39 · ! Barón 0:31 |
| datos/vivo/20261109-175517.jsonl | 19:28 | muerto | 36 | ▼ Muertes 14–25: 3/2 · ! Dragón 0:21 |

Las dos primeras filas son ARAM (modo KIWI, formato «Kills… · Tu KDA», sin tope de 4 piezas). Solo en CLASSIC (Grieta) el máximo es:

| Archivo | Minuto | Fase | Caracteres | Texto |
|---|---|---|---|---|
| datos/vivo/20261109-175517.jsonl | 04:22 | 0-6 | 46 | Nv 4 vs 4 Yunara · CS 20 vs 20 · ! Dragón 0:38 |
| datos/vivo/20261109-175517.jsonl | 12:25 | 6-14 | 40 | CS 100 vs 90 · Oro +1000 · ! Dragón 0:09 |

Las filas 14-25, 25+ y muerto no cambian (ya eran CLASSIC).

## Aviso corto más largo

| Archivo | Minuto | Caracteres | Texto |
|---|---|---|---|
| datos/vivo/20261109-175517.jsonl | 16:57 | 31 | 2 muertes desde el 14 · tu tope |

El aviso se suma a la franja como quinta pieza por 12 s: 64 + 3 (« · ») + 31 = 98 caracteres en el peor caso medido; con un aviso de 48 (el tope) serían 115.

## Notas
- Solo 2 capturas son partidas completas (`20261109-175517`, 70 fotos, y la fixture `partida_completa`, 70 fotos); las otras 14 tienen 1 foto, así que 25+ sale de una sola foto (26:40).
- A 11 pt Segoe UI Semibold (~7 px por carácter, estimado, sin medir) 98 caracteres son ~690 px. La franja arranca en x = 22 % del ancho; a 1366 px eso es ~300 px, y llegaría a ~990 px. Sin verificar en pantalla: lo mide `salud.py` S5 en la prueba real.
