# Contexto de diseño del companion (sesión en vivo)

Actualizado 2026-11-09 por el Diseñador (al retomar). Canvas «Base LOL»: https://claude.ai/artifact/RPTLnjKqhMnuVGkFm7riX7 (versión publicada 1794218119-d920). Base: `datos/diseno-propuesta.md`. Acuerdos: `datos/diseno-acuerdos.md`.

## Decisiones tomadas (con el usuario)
- **Una sola ventana** que cambia por fase: champ select → franja en partida → una línea al terminar. Score, tendencia y tilt van a la **ventana 2** (Perfil).
- **Champ select gira en torno al pick**: por qué, cómo jugarlo (metas 6 / 10 / 14+ con número), cuidado con el rival, counters, build.
- **Todo número con su referencia** (n, tu media, Wilson). Lo cualitativo solo de `datos/matchups-notas.json` (lo escribe el usuario).
- **Paleta 3E pizarra + negro** (`#2B323D`, acento `#FF8A3D`), Mulish, nav lateral, aside oscuro «Pickea». En el canvas publicado ya solo quedan los dos artboards en 3E.
- **Copy 14+**: «con 3+ bajas de 68% a 43%» (no 82/57). Ya corregido.
- «Cómo jugarlo» = 3 tarjetas de stat con ícono y ✓/✕; Perfil tiene «Qué está fallando» en filas. [Corchetes] = ejemplo.
- Franja en partida y post-partida: descartadas del canvas; Opus las pinta con las tarjetas de ChampSelect (PIZARRON, nota del 2026-11-09).

## Qué es cada artboard (publicado)
| Artboard | Marco | Qué muestra |
|---|---|---|
| `Inv5.dc.html` «Paleta 3E · Pizarra + negro» | 1440×1024 en (3040,1144) | Perfil (ventana 2): score 49.2, WR 20 partidas, muertes 14–25, «Qué está fallando» (KP, muertes, línea), tilt hoy, tu cuenta (Master 15 LP, WR temporada vs meta 60%), pool. |
| `ChampSelect_Paleta3E.dc.html` «Base LOL · Selección · Paleta 3E» | 1440×1024 en (4560,1144) | Sylas contra Ahri mid: 3 tarjetas (contra Ahri, tu Sylas, cuidado), «Cómo jugarlo» (Nv 6, minions 10, muertes 14–25), build; aside «Pickea» con 58% estimado y counters Viktor/Yasuo/Qiyana. |

Copias locales en `datos/diseno/canvas/project/` (lo que lee Opus) aún tienen además Perfil, ChampSelect, Navy3 e Inv1 (crema/navy/vino), ya fuera del canvas publicado. Inv1, Inv5 y Navy3 locales tienen cambios sin commit.

## Lo que Opus ya construyó (Turno 6–7)
- `draft.ficha()` (por qué, cuidado, counters, reglas), aviso en vivo de muertes 14–25, `score.tilt()`, `resumen_fin()`, LP del cliente.
- App web / Companion.exe v0.1.4 con vista «Partidas», íconos Lucide, «Cómo jugarlo» con tu media real y «Qué está fallando» con los 8 componentes.

## Preguntas abiertas
1. ¿Paleta 3E es la final? (acuerdos aún la listan abierta). ¿Borramos las copias locales crema/navy/vino?
2. «All-in con su definitiva» / «Ese minuto juega bajo torre»: sin dato. ¿Quitar o pasar a `matchups-notas.json`?
3. Build: íconos de Data Dragon (la app ya los usa) o iniciales.
4. Tamaño real de la ventana: 1440×1024 como el canvas o la compacta 420×760 de la propuesta.
5. Cifras de ejemplo (Ahri 4-1, Sylas 48%/92, 58%, 0:24): ¿reemplazar por las tuyas reales?
6. Perfil «Qué está fallando» muestra 3 filas; la app ya pinta los 8 componentes. ¿Alinear el canvas a 8?

## Lo próximo
- Cambios chicos en vivo al canvas a pedido («mueve esto»), respuesta en una línea.
- Vigilar comentarios con `ArtifactComments`.
- Cada acuerdo a `datos/diseno-acuerdos.md`; guardar el artboard acordado en `datos/diseno/canvas/project/`.
- Para Opus (pendiente): ícono de campeón con `'` o espacio (Kai'Sa, Nunu & Willump).
