# Acuerdos de diseño del companion

Sesión en vivo con el usuario, 2026-11-09. Canvas: https://claude.ai/artifact/RPTLnjKqhMnuVGkFm7riX7 («Base LOL»). Contexto: `.equipo/diseno-contexto.md`.

## Acordado
1. **Una sola ventana** que cambia sola por fase: champ select → franja en partida → una línea al terminar. Score, tendencia y tilt van a la ventana 2 (Perfil).
2. **Champ select gira en torno al pick**: por qué ese pick, cómo jugarlo (metas 6 / 10 / 14+ con su número), cuidado con el rival, counters y build.
3. **Base visual**: los artboards «Base LOL» (Perfil y ChampSelect) con Mulish, nav lateral y aside oscuro «Pickea».
4. **Paleta 3E (pizarra + negro, acento `#FF8A3D`)** también se muestra en champ select: `ChampSelect_Paleta3E.dc.html`. Perfil en 3E es `Inv5.dc.html`.
5. **Copy de la meta 14+**: «con 3+ bajas de 68% a 43%» (todas tus partidas), no 82/57. Corregido en los dos champ select.
6. **«Cómo jugarlo»** son 3 tarjetas de stat (Nivel al 6, Minions al 10, Muertes 14–25) con ícono, valor, ✓/✕ y su número; **Perfil** tiene «Qué está fallando» en 3 filas. Los valores entre [corchetes] son ejemplo.
7. Copia vigente del canvas (versión 1794217527-6e0d) guardada en `.equipo/diseno/canvas/project/`: es lo que lee Opus.
8. Las ventanas de franja y post-partida que propuse se descartaron por ahora. Opus las construye desde `.equipo/diseno-propuesta.md` (su siguiente paso en el turno 7).
9. **Frascos premium** (2026-11-09) para medidores en las 3 pantallas: vidrio, llenado 1.6 s, ola de 2 capas, brillo cada 6 s; colores por métrica (win rate teal, score azul, muertes rojo, minions naranja). Especificación en el artboard `Tubos_Kit.dc.html`.
10. **Elevación suave + encabezado con luz** (2026-11-09) en todas las tarjetas: degradado #3B4452→#343C49, sombra en capas, filo de luz arriba; títulos de sección con degradado naranja. Referencia: `Sombras_Opciones.dc.html` (opción A).
11. **Selección de campeón simplificada**: una idea por tarjeta; «Cómo jugarlo» = 3 frascos con % de partidas que cumples la meta.
12. **Paleta Vino + negro** para la primera build (2026-11-09), con acento rosa `#F28DB0` y frascos en salvia / lila / carmín. Artboards `Perfil_Vino`, `Seleccion_Vino`, `EnPartida_Vino` en `.equipo/diseno/canvas/project/`.
13. El acento y los frascos se adaptan a la paleta (nada de naranja fijo).
14. **Qué está fallando**: barras divergentes desde el centro, escala ±0.35.
15. Logo de la barra lateral: **casa** (Inicio), no escudo.
16. **Reglas, no números**: Perfil «Qué cambiar» (4 reglas), Selección «Tu plan» (3), En vivo «Tus reglas en esta partida» (estado en vivo), Home «Tu regla de hoy»; siempre con «Cumples N/20».
17. **10 pantallas en Vino** (Home, Draft, Selección, En vivo, Perfil, Partidas, Campeones, Errores, Ajustes + referencia de minions) y barra lateral con todas.
18. **Animaciones**: frascos (métricas), anillos (campeones), ítems con marco vivo + core sutil, «Hasta el nivel 6», medallones de nivel, minion vino diminuto (CS), tachas rojas (muertes). Todo quieto con reducir movimiento.
19. **Ajustes sin key de Riot** (producción); paleta Vino oscuro / Vino claro (claro sin diseñar).
20. Minion: dibujo vectorial propio basado en el Ranged Minion de Order (no el modelo de Riot).
21. **Ajustes del 2026-11-10** (pedidos del usuario, canvas v105): «Tus campeones ahora» con fichas V/D en vez de cuadritos; Perfil cambia los 3 frascos verticales por **anillos** con raya de referencia; **Inter** en textos largos/secundarios y Mulish en títulos y cifras; números de «Contra»/«Tu» a 26 px; CS con el **ícono PNG del caster** (CommunityDragon `bluerange_circle.png`, reemplaza el minion vectorial del acuerdo 20); muertes desde el 14 con **calaveras**; en «Tu build» el ítem que estás comprando va **al final**, 56 px, borde punteado rosa grueso con pulso, «Comprando: …».
22. **Ícono de la app** (2026-11-10): el caster vino sobre fondo vino con filo rosa; `.equipo/diseno/icono/htc.ico` (+ PNG 256 y SVG). Pasado a Opus en `notas-equipo.md`.
23. **Ventana propia + login con Google** (2026-11-10, propuesta del Diseñador; **no publicada en el canvas en la nube**, sin permiso para la herramienta; archivos locales `Ventana_Vino.dc.html` y `Ajustes_Login_Vino.dc.html` en `.equipo/diseno/canvas/project/`).
   - **Franja superior** (`Ventana_Vino`): 38 px de alto, ancho completo, fondo `#1A1014`, filo inferior 1 px `rgba(255,255,255,.06)`, arrastrable (`-webkit-app-region: drag`; los botones `no-drag`). Ventana total 1440×1024, radio 40; bajo la franja el contenido mide 986 px y solo conserva radio 40 abajo. Nav lateral (101 px) y aside oscuro (radio 40) no cambian.
   - Izquierda: padding 14 px; ícono 20×20 (radio 5, fondo `#36192A`, filo rosa `#F28DB0` 1 px, casa 13 px) + «Racha» Mulish 700 13 px `#F2F4F7`, gap 8.
   - Derecha: 3 botones de 46×38, ícono 10×10 trazo 1.2 px `#D2BAC4`; hover `rgba(255,255,255,.08)` + ícono blanco; pulsado `.14`. **Cerrar**: hover `#E81123` con ícono blanco, pulsado `#B30E1C`. Foco de teclado: contorno 2 px `#F28DB0`. Margen derecho 8 px. Maximizado: quitar radio 40 de la ventana.
   - **Login** (`Ajustes_Login_Vino`): tarjeta «Cuenta» estándar (degradado #44203A→#36192A, radio 16, padding 22/30). Sin sesión: fila con nube (44 px, círculo rosa 14 %), «Guarda tu cuenta en la nube» Mulish 700 17 px y apoyo en Inter 13 px; botón Google **blanco** 40 px de alto, radio 20, padding 12, borde 1 px `#747775`, texto «Continuar con Google» Roboto 500 14 px `#1F1F1F`, logo G oficial 18 px a color, gap 10; hover/foco = capa `rgba(48,48,48,.08)` / `.12`. Variante oscura: fondo `#131314`, borde `#8E918F`, texto `#E3E3E3`, capas `rgba(232,234,237,.08/.12)`. Nunca recolorear la G ni cambiar el texto.
   - Con sesión: avatar 48 px (inicial, fondo `#F28DB0`, texto `#24111A`), nombre 17 px 700 y correo Inter 13 px `#D2BAC4` (valores [entre corchetes] de ejemplo), insignia «✓ Sincronizada» (fondo `rgba(127,184,158,.16)`, texto `#A8D8C0`, 26 px); debajo, filo 1 px y «Tu cuenta está guardada en la nube · última sincronización hace 2 min» Inter 14 px; botones «Sincronizar ahora» (estilo secundario rosa, hover `rgba(242,141,176,.12)`) y **«Cerrar sesión»** (40 px, transparente, borde `--line`, texto `#D2BAC4`; hover fondo `rgba(217,96,106,.16)`, borde `#D9606A`, texto `#FFB4BA`).
   - **Código de acceso**: queda como alternativa plegada (`<details>`) bajo el login, cerrada por defecto, con chevron 18 px que gira al abrir; dentro, campo 40 px y «Guardar».

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

## Logo propio (Diseñador, 2026-11-10)
Reemplaza al minion (personaje de Riot). Carpeta `.equipo/diseno/icono/`.
- Cuatro barras ascendentes = racha de victorias; sin degradados ni personajes (se lee a 16 px).
- Lienzo 256: fondo `#24111A` x=8..248, rx 56. Barras de 38 px, paso 46, base y=206, x=34/80/126/172, alturas 56/92/128/164, rx 9.
- Colores de izquierda a derecha: `#A33A63`, `#F28DB0`, `#F8C3D6`, `#A8D8C0` (verde = victoria).
- `racha-mono.svg`: barras `#24111A`, sin fondo, para fondos claros.
- `racha-wordmark.svg` (640×256): logo + «Racha» Mulish 800, 120 px, `#F28DB0`, x=280. Mulish no va incrustada: la web ya la carga; fuera de la web cae a Segoe UI.
- Raster: `hacer-racha.py` (Pillow) genera `racha-{16,24,32,48,64,128,256}.png` y `racha.ico`.
