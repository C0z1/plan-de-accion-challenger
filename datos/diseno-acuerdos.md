# Acuerdos de diseño del companion

Sesión en vivo con el usuario, 2026-11-09. Canvas: https://claude.ai/artifact/RPTLnjKqhMnuVGkFm7riX7 («Base LOL»). Contexto: `datos/diseno-contexto.md`.

## Acordado
1. **Una sola ventana** que cambia sola por fase: champ select → franja en partida → una línea al terminar. Score, tendencia y tilt van a la ventana 2 (Perfil).
2. **Champ select gira en torno al pick**: por qué ese pick, cómo jugarlo (metas 6 / 10 / 14+ con su número), cuidado con el rival, counters y build.
3. **Base visual**: los artboards «Base LOL» (Perfil y ChampSelect) con Mulish, nav lateral y aside oscuro «Pickea».
4. **Paleta 3E (pizarra + negro, acento `#FF8A3D`)** también se muestra en champ select: `ChampSelect_Paleta3E.dc.html`. Perfil en 3E es `Inv5.dc.html`.
5. **Copy de la meta 14+**: «con 3+ bajas de 68% a 43%» (todas tus partidas), no 82/57. Corregido en los dos champ select.
6. **«Cómo jugarlo»** son 3 tarjetas de stat (Nivel al 6, Minions al 10, Muertes 14–25) con ícono, valor, ✓/✕ y su número; **Perfil** tiene «Qué está fallando» en 3 filas. Los valores entre [corchetes] son ejemplo.
7. Copia vigente del canvas (versión 1794217527-6e0d) guardada en `datos/diseno/canvas/project/`: es lo que lee Opus.
8. Las ventanas de franja y post-partida que propuse se descartaron por ahora. Opus las construye desde `datos/diseno-propuesta.md` (su siguiente paso en el turno 7).
9. **Frascos premium** (2026-11-09) para medidores en las 3 pantallas: vidrio, llenado 1.6 s, ola de 2 capas, brillo cada 6 s; colores por métrica (win rate teal, score azul, muertes rojo, minions naranja). Especificación en el artboard `Tubos_Kit.dc.html`.
10. **Elevación suave + encabezado con luz** (2026-11-09) en todas las tarjetas: degradado #3B4452→#343C49, sombra en capas, filo de luz arriba; títulos de sección con degradado naranja. Referencia: `Sombras_Opciones.dc.html` (opción A).
11. **Selección de campeón simplificada**: una idea por tarjeta; «Cómo jugarlo» = 3 frascos con % de partidas que cumples la meta.
12. **Paleta Vino + negro** para la primera build (2026-11-09), con acento rosa `#F28DB0` y frascos en salvia / lila / carmín. Artboards `Perfil_Vino`, `Seleccion_Vino`, `EnPartida_Vino` en `datos/diseno/canvas/project/`.
13. El acento y los frascos se adaptan a la paleta (nada de naranja fijo).
14. **Qué está fallando**: barras divergentes desde el centro, escala ±0.35.
15. Logo de la barra lateral: **casa** (Inicio), no escudo.

## Sigue abierto
- «All-in con su definitiva» y «Ese minuto juega bajo torre» no salen de ningún dato. Hay que quitarlas o escribirlas en `datos/matchups-notas.json`.
- Build: íconos de Data Dragon (la app web de Opus ya los usa) o iniciales.
- Tamaño real de la ventana: la app web abre a 1440×1024, como el canvas.

## Para Opus
- `scripts/web/index.html` debe usar el copy 68 → 43 en la meta 14+.
- Ícono de campeón con `'` o espacio (Kai'Sa, Nunu & Willump): la ruta `/img/champion/\w+` no los acepta.
