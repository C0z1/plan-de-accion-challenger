# Prompt RISE · aplicar «Estela» a Racha

Adaptado del formato R/I/S/E que pasó el usuario (2026-11-10). Para el Diseñador (canvas) y Opus (build). [Corchetes] = lo que falta llenar.

**R · Referencias**
- Canvas «Base LOL»: https://claude.ai/artifact/RPTLnjKqhMnuVGkFm7riX7. Fila de ideas: `Idea_Estela_Sistema`, `Idea_Inicio_Estela`, `Idea_Postpartida`, `Overlay_Vino`; pantallas base `*_Vino`.
- Marca: logo de 4 barras (`.equipo/diseno/icono/racha.svg`). Colores de la estela en orden: `#A33A63 → #F28DB0 → #F8C3D6 → #A8D8C0`; fondo `#1E0E16`. Fuentes: Mulish (títulos y cifras), Inter (textos largos).
- Un video de 1 min recorriendo la app actual (HTC/Racha v0.9) diciendo en voz alta qué se siente muerto o plano: [video].
- Capturas reales de partida (cliente, En vivo, post-partida): [archivos].

**I · Instrucciones**
1. Estudia el video: un fotograma cada 0,5 s y lo que digo. Escribe `.equipo/motion-notes.md`: por pantalla y momento (abrir la app, champ select, en partida, al terminar), qué se mueve, a qué velocidad y qué lo dispara (fase del LCU, minuto, aviso).
2. Explícame de vuelta qué entendiste.
3. Haz el concepto en el canvas: cada pestaña (Inicio, Draft, Selección, En vivo, Perfil, Partidas, Campeones, Errores, Ajustes) y el overlay con Estela: aurora + grano de fondo, tarjetas de vidrio con filo de luz, cifras con brillo, pestaña activa con estela, carga con cometa.
4. Para y espera. Opus no escribe código hasta que yo apruebe.

**S · Restricciones**
- Copia cómo se mueve la referencia, nunca sus textos, arte, logo ni código. Nada de arte de Riot salvo íconos de Data Dragon y el caster ya acordado.
- Solo CSS y SVG en línea dentro de `scripts/web/index.html` (la página corre con CSP `default-src 'none'`: sin CDNs, sin Three.js ni GSAP). Animar solo `transform`, `opacity` y `stroke-dashoffset`.
- El overlay va encima del juego: 0 % de CPU en reposo y nada que tape el minimapa ni la tienda.
- Primera vista ligera: Inicio pinta en ≤ 1 s con la caché; el resto entra escalonado.
- Con «Reducir movimiento» (Ajustes o del sistema), todo queda quieto.
- Contraste AA en todo el texto (≥ 4,5:1, también las etiquetas de 12 px).

**E · Evaluación**
- Cuando esté la v1, mando un video de feedback. Respóndeme primero con un plan y no cambies nada hasta que diga «va».
- Prueba la ventana a 1440×1024 y a 1100×720, y el overlay sobre una captura de partida a 1080p.
- Califica de 1 a 10 tres cosas: **movimiento** (¿se siente una racha?), **rendimiento** (CPU y tiempo de carga, medidos) y **marca** (¿es Racha en cada pestaña?). Arregla todo lo que quede por debajo de 8 y después enséñamelo.
