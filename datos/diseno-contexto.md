# Contexto de diseño del companion (sesión en vivo)

Actualizado 2026-11-09 por el Diseñador. Canvas: https://claude.ai/artifact/RPTLnjKqhMnuVGkFm7riX7 («Base LOL», índice v3, 5 artboards). Propuesta de base: `datos/diseno-propuesta.md`; auditoría: `datos/diseno-auditoria.md`.

## Decisiones tomadas (con el usuario)
- **Una sola ventana** que cambia sola por fase: champ select → franja compacta en partida → una línea al terminar. Score, tendencia y tilt van a una **ventana 2** aparte (perfil). Fuente: `datos/notas-equipo.md` línea 1394.
- **Champ select gira en torno al pick recomendado**: por qué ese pick, cómo jugarlo (reglas con número), cuidado con el rival, counters y build.
- **Todo número lleva su referencia** (n, tu media, Wilson). Lo cualitativo no se inventa: sale solo de `datos/matchups-notas.json`, que escribe el usuario.
- **Datos ya construidos por Opus** (dict para la GUI): `draft.ficha()`, `companion.meta_fase()`, `companion.resumen_fin()`, `score.tilt()`, `score.resumen()`, `builds.guardado()`.

## Qué es cada artboard (`project/canvas.json`)
| Artboard | Marco | Qué muestra |
|---|---|---|
| `Perfil.dc.html` «Base LOL» | 1440×1024 en (0,0) | Ventana 2: «Tu rendimiento». Base de la paleta crema `#FFFCF8` con aside oscuro `#282828` y nav lateral. |
| `ChampSelect.dc.html` «Selección de campeón» | 1440×1024 en (1520,0) | Champ select de Sylas contra Ahri (mid). Izquierda: 3 tarjetas (rival, tu pick, cuidado), «Cómo jugarlo» con metas 6 / 10 / 14+, fila de build. Derecha, aside «Pickea»: estimado 58%, la línea de tu WR, y 3 counters con CS al 14. |
| `Navy3.dc.html` «Paleta 3 · Navy + negro» | 1440×1024 en (0,1144) | Variante de Perfil con fondo `#1B2B4B` y acento `#E0A43A`. |
| `Inv1.dc.html` «Paleta 3A · Vino + negro» | 1440×1024 en (1520,1144) | Variante de Perfil con fondo `#4A1D2A` y acento `#E0A43A`. |
| `Inv5.dc.html` «Paleta 3E · Pizarra + negro» | 1440×1024 en (3040,1144) | Variante de Perfil con fondo `#2B323D` y acento `#FF8A3D`. |

Tipografía en el canvas: Mulish (Google Fonts). La propuesta decía Segoe UI. Ninguna pantalla usa aún el cian `#4FD1C5` de la propuesta; ChampSelect usa ámbar `#D08726` con tintes teal.

## Preguntas abiertas (para ti)
1. **Paleta:** ¿Perfil (crema), Navy3, Inv1 (vino) o Inv5 (pizarra)? ¿Probamos el cian de la propuesta o te quedas con el ámbar?
2. **Tamaño:** el canvas está en 1440×1024, pero la ventana real de la propuesta es 420×760 (o ~560 de ancho). ¿Cuál vale?
3. **Texto sin fuente:** «All-in con su definitiva» y «Ese minuto juega bajo torre» (tarjeta Cuidado) no salen de ningún dato. ¿Lo quitamos o lo escribes tú en `datos/matchups-notas.json`?
4. **Cifras de ejemplo:** Ahri 4-1, Sylas 48% en 92 partidas, 58% estimado y el reloj 0:24 son de muestra. ¿Cuáles son tuyas de verdad? (Sí son tuyas: −28 / −26 / −20 de CS con Viktor, Yasuo y Qiyana, y 69+ minions al 10 con 74% contra 32%.)
5. **Build:** ¿iconos de Data Dragon o iniciales ([1] [2] [3] [b] hoy son placeholders)?
6. **Error de copy a corregir:** en «Máximo 2 muertes del 14 al 25» la tarjeta dice «Con 3+ bajas de 82% a 57%». El 82/57 vale solo con línea y equipo arriba al 14. El aviso en vivo cita 68% → 43% (todas tus partidas), y así lo acordamos en Opus. Propongo cambiarlo a 68 → 43.

## Lo próximo
- Cuando digas «mueve esto», publico el cambio al momento en el canvas (cambios chicos, respuesta de una línea).
- Vigilar los comentarios del canvas con `ArtifactComments`.
- Corrección 6 (82 → 68 / 43): la publico si la confirmas.
- Acuerdos finales a `datos/diseno-acuerdos.md`. Aún no existe; se crea con el primer acuerdo.
- Pendiente de Opus: nada bloqueante. Los datos de la ventana ya están en dict. No hubo consulta a DeepSeek en esta sesión.
