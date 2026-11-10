# Contexto de diseño del companion (sesión en vivo)

Actualizado 2026-11-10 por el Diseñador (al retomar). Canvas «Base LOL»: https://claude.ai/artifact/RPTLnjKqhMnuVGkFm7riX7 (versión 1794263707-e5fa, idéntica a `.equipo/diseno/canvas/project/`). Acuerdos: `.equipo/diseno-acuerdos.md` (1–20). Sin comentarios abiertos en el canvas.

## Decisiones tomadas (con el usuario)
- **Paleta Vino + negro** para la build: fondo `#24111A`, tarjeta `#36192A`, panel `#0B0709`, acento rosa `#F28DB0`; frascos salvia / lila / carmín. Mulish. Pizarra, crema y navy quedan fuera.
- **Reglas, no números**: cada pantalla habla en reglas con «Cumples N/20» (Perfil 4, Selección 3, En vivo en estado vivo, Home 1).
- Champ select gira en torno al pick; todo número con su referencia; [corchetes] = ejemplo.
- Elevación suave + encabezado con luz en tarjetas; barra lateral con casa (Inicio) y las 9 ventanas.
- Animaciones: frascos, anillos de retrato, ítems con marco vivo y core sutil (56 px, «CORE · 78%»), «Hasta el nivel 6», minion vino, tachas de muertes. Todo quieto con reducir movimiento.
- Ajustes sin key de Riot (va a producción). Minion vectorial propio.

## Qué es cada artboard (todos 1440×1024, fila y = −1144)
| Artboard | Qué muestra |
|---|---|
| `Perfil_Vino` (x 3040) | Tu rendimiento: score, WR, errores «Ver cuáles», «Qué cambiar» (4 reglas), tilt hoy, «Tus campeones ahora» |
| `Seleccion_Vino` (4560) | 3 tarjetas (vs rival, tu WR, Hasta el nivel 6), «Tu plan con Sylas», build con core, estimado + «Si te toca contra…» |
| `EnPartida_Vino` (6080) | Medallones de nivel, CS con minion, muertes con tacha, «Tus reglas en esta partida», fase; panel KDA, build, Tu rival, Objetivos |
| `Draft_Vino` (7600) | Banea, tu pool con anillos, rivales frecuentes en mid |
| `Partidas_Vino` (9120) | Historial con ✓/✕ por regla, MVP/peor del equipo; partida seleccionada con 3 cosas a mejorar |
| `Campeones_Vino` (10640) | Pool con anillos, forma, mejor/peor vs; panel con build, regla, counters |
| `Home_Vino` (12160) | Cliente conectado, Hoy + tilt, tu regla de hoy, rango con frasco a 60%, atajos |
| `Ajustes_Vino` (13680) | Cuenta, apariencia (Vino oscuro/claro, reducir movimiento), avisos on/off |
| `Errores_Vino` (15200) | 3 errores repetidos con botones al replay, «Cómo los cuento» |
| `Minions_Variantes` (6080, y −2288) | Referencia del caster en 4 colores |

Locales viejos (no usar): `Inv1`, `Inv5`, `Navy3`, `Perfil`, `ChampSelect*`; `Tubos_Kit` solo es la especificación del frasco (no está en el canvas).

## Lo que Opus ya construyó
- Turno 6: `draft.ficha()` (por qué, cuidado, counters, reglas), aviso de muertes 14–25, `score.tilt()`, `resumen_fin()`, LP del cliente.
- Turno 9 (HTC v0.3.9): tokens Vino, Selección y «Qué está fallando» simplificados, En vivo con Tu rival y Objetivos (timers ámbar < 60 s, ítems con alt), precarga del draft.

## Preguntas abiertas
1. **Vino claro**: propuesta en acuerdos (acento `#B83A6B`), sin aprobar ni dibujar; contraste AA sin medir.
2. «All-in con su definitiva» / «Ese minuto juega bajo torre»: sin dato. ¿Quitar o pasar a `matchups-notas.json`?
3. ¿Revisar la build HTC v0.3.9 pantalla por pantalla contra los artboards (solo En vivo está auditada, `diseno-auditoria.md` §6)?
4. Pantallas sin construir aún en la app: Draft, Partidas (MVP), Campeones, Errores, Home: ¿cuál priorizamos?
5. Errores con definiciones amplias (16/20): ¿mostrar el n o afinar la definición?

## Lo próximo
- Cambios chicos en vivo al canvas a pedido, respuesta en una línea; vigilar comentarios (watch activo).
- Acuerdos nuevos a `.equipo/diseno-acuerdos.md`; al cerrar, bajar el canvas a `.equipo/diseno/canvas/project/`.
