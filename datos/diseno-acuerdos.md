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
16. **Reglas, no números**: Perfil «Qué cambiar» (4 reglas), Selección «Tu plan» (3), En vivo «Tus reglas en esta partida» (estado en vivo), Home «Tu regla de hoy»; siempre con «Cumples N/20».
17. **10 pantallas en Vino** (Home, Draft, Selección, En vivo, Perfil, Partidas, Campeones, Errores, Ajustes + referencia de minions) y barra lateral con todas.
18. **Animaciones**: frascos (métricas), anillos (campeones), ítems con marco vivo + core sutil, «Hasta el nivel 6», medallones de nivel, minion vino diminuto (CS), tachas rojas (muertes). Todo quieto con reducir movimiento.
19. **Ajustes sin key de Riot** (producción); paleta Vino oscuro / Vino claro (claro sin diseñar).
20. Minion: dibujo vectorial propio basado en el Ranged Minion de Order (no el modelo de Riot).
21. **Ajustes del 2026-11-10** (pedidos del usuario, canvas v105): «Tus campeones ahora» con fichas V/D en vez de cuadritos; Perfil cambia los 3 frascos verticales por **anillos** con raya de referencia; **Inter** en textos largos/secundarios y Mulish en títulos y cifras; números de «Contra»/«Tu» a 26 px; CS con el **ícono PNG del caster** (CommunityDragon `bluerange_circle.png`, reemplaza el minion vectorial del acuerdo 20); muertes desde el 14 con **calaveras**; en «Tu build» el ítem que estás comprando va **al final**, 56 px, borde punteado rosa grueso con pulso, «Comprando: …».

## Sigue abierto
- «All-in con su definitiva» y «Ese minuto juega bajo torre» no salen de ningún dato. Hay que quitarlas o escribirlas en `datos/matchups-notas.json`.
- Build: íconos de Data Dragon (la app web de Opus ya los usa) o iniciales.
- Tamaño real de la ventana: la app web abre a 1440×1024, como el canvas.

## Vino claro (propuesta del Diseñador, 2026-11-09, para aprobar)
Mismos nombres de variable que Vino oscuro; solo cambian los valores.

| Variable | Oscuro | Claro |
|---|---|---|
| `--bg` | `#24111A` | `#FBF3F6` |
| `--card` | `#36192A` | `#FFFFFF` |
| `--line` | `#5A2D40` | `#E3CBD5` |
| `--text` | `#F2F4F7` | `#2A1420` |
| `--muted` / `--muted2` | `#D2BAC4` / `#AE95A0` | `#6E4C5C` / `#85616F` |
| `--acc` (rosa) | `#F28DB0` | `#B83A6B` |
| `--good` / `--bad` | `#7FB89E` / `#D9606A` | `#2F7A57` / `#B3303C` |
| Texto sobre el acento | `#161A21` | `#FFFFFF` |

- El rosa claro no se usa como texto sobre fondo claro; el acento oscurece.
- ✓/✕ siempre con símbolo, no solo color.
- Frascos: mismos tonos, vidrio blanco y sombra rosada suave. El aside «Pickea» queda oscuro en ambos temas.
- **Contraste AA sin medir** (las herramientas pidieron aprobación): verificar al implementar.

## Para Opus
- `scripts/web/index.html` debe usar el copy 68 → 43 en la meta 14+.
- Ícono de campeón con `'` o espacio (Kai'Sa, Nunu & Willump): la ruta `/img/champion/\w+` no los acepta.
