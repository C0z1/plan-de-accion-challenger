# Plan «Racha se reinventa» (Fable, 2026-11-12)

Basado en `COMPETENCIA.md`, `PLAN-OVERLAY.md`, `diseno-prompt-estela.md`, el lienzo «Base LOL» (Estela) y `scripts/web/index.html`. Fuentes Mulish e Inter ya locales (woff2).

## 1. Tesis
Los demás son tableros de datos de los 10 jugadores con anuncios: mucha información y ninguna decisión. Racha es un ritual personal de una sola meta (Master → Challenger): una regla tuya, una cifra y un momento por pantalla, de tu historial, y cambia sola con la fase del cliente. Premium de instrumento, no de casino: oscuro, silencioso, una sola luz (la estela) que se mueve solo cuando algo tuyo avanza, y quieta en partida. Marca propia (4 barras → estela), sin arte de Riot salvo Data Dragon. Local, sin Overwolf, sin anuncios, sin scouting de ocultos.

## 2. Ideas de reinvención (prioridad)
| # | Idea | Valor para subir | Tam. | Riesgo | Cómo |
|---|---|---|---|---|---|
| 1 | Estela en toda la app | Una cifra por vista, se lee en 2 s | M | Rendimiento si se copia el lienzo tal cual | Solo CSS/SVG en `index.html`, mismas clases |
| 2 | Inicio como ritual de sesión (racha, regla de hoy, sesión; descanso tras 2 derrotas) | El más alto: tu dato de tilt al centro | M | Textos como dato + regla | `inicio()` con `score.tilt`, `regla_hoy`, `racha_oro14` |
| 3 | Recap «tu partida en una estela» (oro por minuto + 3 momentos) | Revisar en 20 s lo que costó | M | Hoy solo llegan textos de momentos | `postpartida.estela()`; SVG en `envivo()` |
| 4 | Transición entre fases del cliente | Hace evidente la ventana que cambia sola | S | `tick()` repinta con innerHTML | `startViewTransition` solo al cambiar de vista |
| 5 | Viaje a Challenger (LP por sesión, distancia al corte LAN) | Objetivo visible por sesión | M | Solo ladder oficial, nunca MMR | `datos/lp.jsonl`; corte por backend (league-v4) |
| 6 | Modo enfoque / ventana compacta | Menos ruido en selección; 2.º monitor | S | Bajo | Clase `enfoque` + CSS < 600 px |
| 7 | Tarjetas compartibles (recap, racha, hito) | Canal de crecimiento sin anuncios | S–M | Privacidad (Riot ID); portapapeles en `--app` | Canvas 2D + «Copiar imagen» |
Pospuesto: sonido (2 sonidos opcionales en 0.21); «coach que aprende» ya existe: hacerlo visible con una línea en el ritual. Chat con LLM: no.

## 3. Sistema de diseño «Estela»
- Se reutiliza: variables de `:root`, nombres de clase, curva `cubic-bezier(.22,1,.36,1)`, `ic()/ICON`, `.quieto`.
- Tokens: `--bg:#1E0E16`; `--e1:#A33A63 --e2:#F28DB0 --e3:#F8C3D6 --e4:#A8D8C0`; `--estela` (degradado de los 4); `--oro:#F2C46B` (recap y racha de oro); salvia = cumples, rojo = fallas, siempre con ✓/✕. Vidrio `rgba(68,32,58,.86)→rgba(42,20,32,.86)` con filo `inset 0 1px 0 rgba(255,255,255,.10)`; sombras `--s1`, `--s2`. Radios: tarjeta 20, control 12, píldora 999, aside 40. Espacios 8/12/16/22/30/48.
- Tipografía Mulish: cifra héroe 72/800 tabular con degradado (una por vista); ritual 40/900; h1 28; h2 20; cuerpo 16; etiqueta 12/800 .14em mayúsculas en `--e3`. Inter 14/1.5 en secundarios; mínimo 12.
- Movimiento: `--sal` (.22,1,.36,1) entradas, `--pasa` (.45,0,.25,1) cometa. 120 ms hover, 200 ms interruptor, 320 ms vista, 800 ms entrada escalonada 60 ms (máx. 6), 1,2 s cifra, 3,2 s cometa, 26/32 s aurora. Máximo 2 bucles infinitos visibles por vista, 0 en partida.
- Componentes: fondo con 2 auroras + grano SVG en data-URI al 7 %; tarjeta de vidrio con filo superior; nav activa con estela vertical y cometa; `.btn.principal` con estela y reflejo cada 5 s (uno por vista); carga con cometa (sin spinners); vacío con el logo al 35 % + frase + acción; racha con las 4 barras del logo; pulsado `scale(.97)`, tarjeta `translateY(-2px)`; la cifra se anima solo si cambió.
- Correcciones obligatorias: sin `backdrop-filter` ni `mix-blend-mode`; animaciones del lienzo y de producción que tocan `background-position`, `r`, `filter`, `left`, `width` o `box-shadow` pasan a `transform`/`opacity`; reducir movimiento con una sola regla `*,*::before,*::after{animation:none!important;transition:none!important}` (hoy no cubre `::after`); entradas solo cuando cambia la vista (no en cada `tick`); en partida y con `document.hidden`, la página queda `quieto`.

## 4. Fases
- **0.18.0 Estela base**: tokens, fondo, tarjeta, nav, botón principal, cifra héroe, carga, vacíos, correcciones. Revisar antes las 7 pruebas que leen `index.html` como texto. Pruebas `test_ds_estela.py` (keyframes solo transform/opacity/stroke-dashoffset; sin backdrop-filter ni mix-blend-mode; reducir movimiento con `::after`; tokens; `infinite` ≤ 12; sin URL externa; contraste AA calculado contra el peor fondo — ojo `--neutro #9A8290` ~3,9: no usarlo en texto). Medición con `scripts/dev_medir.py`: `--demo --no-abrir`, Edge headless por vista a 1440×1024 y 1100×720 (+ reducir movimiento), primer render de Inicio ≤ 1000 ms, CPU de la ventana real (Inicio ≤ 2 % de un núcleo, quieto/En vivo ≤ 0,3 %), notas 1–10 de movimiento, rendimiento y marca en `datos/salud/estela-0.18.md`; < 8 se arregla antes de publicar.
- **0.19.0 Ritual y recap**: Inicio en tres tiempos y un botón «Empezar a subir» (a Draft); con 2 derrotas seguidas, pantalla «Descanso 15:00» con anillo que se vacía; recap `postpartida.estela(match, timeline, puuid)` y SVG en En vivo; transición entre vistas. Pruebas `test_ds_recap.py`, `test_ds_ritual.py`.
- **0.20.0 Viaje, enfoque y compartir**: `datos/lp.jsonl`, corte LAN por backend (caché 6 h), tarjeta «Viaje»; modo enfoque; tarjetas canvas 1080×1350 con «Copiar imagen» (plan B: guardar PNG). Pruebas `test_ds_lp.py`.
- **0.21** (si sobra): 2 sonidos opcionales; Estela en la fase 2 de la franja; bandeja.

## 5. Riesgos y decisiones
Riesgos: costo real de la aurora en Edge (si Inicio pasa del 2 %, aurora fija); banderas de Edge headless sin probar; portapapeles de imagen en `--app`; corte de Challenger depende del backend; `index.html` crece ~250 líneas; `/api/runas` escribe en el cliente: no presumir «solo lee» sin revisarlo.

Decisiones del usuario:
1. ¿Va Estela con las correcciones (sin backdrop-filter, quieta en partida), aunque no exista el video de referencia que pedía el prompt RISE?
2. ¿Inicio pasa de tablero a ritual (una regla, una racha, un botón; descanso tras 2 derrotas)?
3. Tarjetas y viaje: ¿Riot ID visible u oculto por defecto? ¿Consultar el ladder LAN por el backend para el corte?

## Revisión de DeepSeek (2026-11-12)

1) Diferenciador: ritual de una cifra, descanso anti-tilt, Viaje a Challenger con LP propio. Humo: transiciones, modo enfoque, tarjetas compartibles, "premium" sin métrica.

2) Riesgos técnicos: Aurora puede superar 2% CPU; limitar capas y medir en Edge real. View Transitions con innerHTML puede parpadear; usar solo cambio de vista y fallback. Portapapeles de imagen en --app incierto; implementar guardar PNG. Canvas de tarjeta bajo demanda, sin animar. index.html +250 líneas no preocupa.

3) Riot: Descanso tras 2 derrotas es OK; no lo uses como consejo médico. Ladder oficial por league-v4, nada de MMR; corte dinámico, di "corte actual". Riot ID visible por defecto arriesga privacidad; oculto por defecto y compartir explícito.

4) Huecos: mediciones dinámicas (CPU/memoria con transiciones, document.hidden, partida), pruebas en Edge --app real, fallback portapapeles, accesibilidad foco/teclado, límites API/caché.

5) Orden: fusionar 0.19 Ritual con 0.20 Viaje; posponer tarjetas y enfoque. Falta una regla contextual generada por tu historial (coach visible), no solo regla fija.

## Decisiones del usuario (2026-11-12)
1. Estela con las correcciones: sí, construir (0.18.0).
2. Inicio como ritual con descanso tras 2 derrotas: sí.
3. Tarjetas con Riot ID oculto por defecto; ladder LAN por el backend: sí.
