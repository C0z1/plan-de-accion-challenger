# Replays `--validar --precios` en vivo (D-d, A3)

DeepSeek (Sonnet de reemplazo), 2026-11-11 (ronda 2). Cada captura se repitió con `replay.repetir` + `replay.validar` (equivale a `python scripts/replay.py <archivo> --validar --precios`; comprobado a mano en `20261109-173828.jsonl` y `20261111-145203.jsonl`: «0 fallo(s)»), con el código de Opus de ese momento. Falta repetirlo cuando Opus avise de F2.

**Resultado: 0 fallos en las 18 capturas.**

| Captura | Fotos | Fallos |
|---|---|---|
| datos/vivo/20261109-173828.jsonl (PRACTICETOOL) | 1 | 0 |
| datos/vivo/20261109-175517.jsonl | 70 | 0 |
| datos/vivo/20261109-225043.jsonl | 1 | 0 |
| datos/vivo/20261109-225110.jsonl | 1 | 0 |
| datos/vivo/20261110-044529, -044747, -052844, -052909, -053229, -053417, -054257, -054403, -054519, -055825 (KIWI) | 1 c/u | 0 |
| datos/vivo/20261110-182203.jsonl | 1 | 0 |
| datos/vivo/20261111-144834.jsonl | 6 | 0 |
| datos/vivo/20261111-145203.jsonl (PRACTICETOOL) | 13 (22 líneas, 9 repetidas por gameTime) | 0 |
| scripts/fixtures/vivo/partida_completa.jsonl | 70 | 0 |

Nota: `replay.py:96` solo exige CLASSIC para las piezas de línea, y estas dos capturas de Practice Tool pasan (la de 173828 trae `position` NONE; la otra sin comprobar); con un rival real de línea daría un falso fallo (hallazgo 11 de `deepseek-revision-envivo.md`).
