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

## Sigue abierto
- Paleta final: crema (base), Navy 3, Vino 3A o Pizarra 3E.
- «All-in con su definitiva» y «Ese minuto juega bajo torre» no salen de ningún dato. Hay que quitarlas o escribirlas en `datos/matchups-notas.json`.
- Build: íconos de Data Dragon (la app web de Opus ya los usa) o iniciales.
- Tamaño real de la ventana: la app web abre a 1440×1024, como el canvas.

## Para Opus
- `scripts/web/index.html` debe usar el copy 68 → 43 en la meta 14+.
- Ícono de campeón con `'` o espacio (Kai'Sa, Nunu & Willump): la ruta `/img/champion/\w+` no los acepta.
