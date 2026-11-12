# Plan: franja «pastilla» 380×72 (Racha 0.17.0) · Fable, 2026-11-12

Basado en el lienzo «Base LOL» (Overlay_Vino, Idea_Overlay_Regreso, EnPartida_Vino). Siguen las prohibiciones de `PLAN-ENVIVO.md` §5 y los límites de Riot de `COMPETENCIA.md` §4.

Hallazgos que condicionan el plan:
- La Live Client Data no trae XP (propia ni del rival): el «anillo de XP» del lienzo no se puede dibujar con datos reales.
- `salud.py` S5 falla hoy con alto > 5 % del juego; 72/1080 = 6,7 %: subir el umbral.
- §5 dice «sin dependencias nuevas»; Pillow no va hoy en `HTC.spec`.
- Las fuentes de la app son `.woff2`; Mulish no está instalada en Windows.
- Con dos medallones + anillo de CS + número quedan ~75 px para el chip: máximo 10 caracteres.
- `overlay.partes` lo usan `salud.py:218`, `replay.py:73` y 10 archivos de prueba.

## 1. Tecnología
**tkinter como ventana anfitriona + Pillow dibujando a imagen + `UpdateLayeredWindow` (alfa por píxel).**
- Descartados: Canvas de tkinter solo (sin antialiasing, alfa por píxel ni recorte circular), segunda ventana Edge (sin transparencia ni click-through fiable, ~100 MB), GDI+ por ctypes (una firma mal puesta mata HTC en partida).
- Se conserva: `root.after` en el hilo principal, título «Racha franja», `atravesable()`, `visible()`, `colocar()`, `rect_juego()`, firma de `correr()`. Se quitan `-alpha` de Tk y los `Label`.
- Se pinta solo cuando cambia el estado (~2–5 ms); tick de 1 s, 33 ms solo durante una animación (≤ 1,5 s). CPU < 1 %.
- Pantalla completa exclusiva: sigue sin verse (S7).
- Requiere permiso: Pillow en el `.exe` (~8–10 MB).
- Sin verificar: `UpdateLayeredWindow` sobre Tk (fase 0). Plan B: ventana Win32 propia por ctypes con el mismo pintor.

## 2. Estados y reglas
`overlay.estado(meta, ahora, aj, regla, aviso) -> dict | None`, `t = meta["t"]`. Huecos: A (medallón), B (anillo + número + etiqueta), C (chip). Prioridad: AVISO > (fase 2: ORO14 > IGUALASTE) > base por minuto. Estado base apagado en Ajustes: `None`.

**LINEA** (Grieta, `t < 840`, `franja_linea`):
- A: retrato con anillo `min(nivel,6)/6` (progreso a la regla del nivel 6, no XP) e insignia de nivel; con rival, `d = nivel − nivel_rival`: «−1» rojo, «=» gris, «+1» salvia; medallón rival rojo si `d < 0`.
- B (`t < 600` y `cs_meta`): minion en anillo `cs/ritmo`, `ritmo = round(cs_meta · max(0, t − 75)/525)`; número CS, «ritmo N»; salvia si `cs ≥ ritmo`, oro si ≥ 85 %, rojo si menos.
- B si no, con `rival_cs`: `cs − rival_cs` con signo, «CS vs Ahri»; rojo si ≤ −10, salvia si ≥ 0. Sin ninguno: CS solo.
- C (≤ 10 caracteres): `d < 0` y `t ≥ 600` «Tu plan» rojo; `d < 0` «Abajo» rojo; B bajo «Bajo ritmo» oro; si no «✓ Vas bien».
- Sin rival de línea: solo tu medallón; B contra el ritmo; C solo por CS; sin `cs_meta`, sin chip.

**PELEAS** (`840 ≤ t < 1500`, `franja_regla`, `muertes14` no None; `tope = regla.tope` o 2):
- A: retrato con anillo partido en `tope` tramos (máx. 5); cada muerte apaga uno; «1/2», «muertes».
- B: participación `(K+A)/kills del equipo` en anillo, «58%», «en kills»; «—» con 0 kills.
- C: `< tope` «✓ Vas bien»; `= tope` «En tu tope» oro; `> tope` «Sobre tu tope» rojo.

**TARDE** (`t ≥ 1500` o PELEAS apagado): anillo lleno, «5/4/7» «KDA»; B participación; C «Equipo +1 200» (oro en ítems).
**ARAM**: retrato, «12 – 15» «kills», «KDA 3/2/7», sin chip.
**AVISO** (`aviso.franja` y `aviso.corto`; `franja_libre`: 90 s, 6 por partida): muertes → PELEAS en rojo, retrato atenuado, «En tu tope», 5 s; demás → retrato + `corto` en 2 renglones, borde rojo, 8 s.

**Textos del lienzo por política** (dato + tu regla, sin órdenes): «No pelees» → «Abajo»; «Farmea bajo torre» → «Tu plan»; «Juega con objetivo» → «En tu tope»; «ya puedes pelear» → «nivel 8 = 8»; «una más: 43 %» fuera de la franja; «en peleas» → «en kills»; «oro vs Ahri» → «oro en ítems vs Ahri». Se quitan el estado «muerto» (F4) y los timers de Dragón y Barón.

## 3. Diseño
- Medidas (×escala): pastilla 380×72, radio 16, relleno 14, separación 12; medallón 44 (retrato 28, anillo r17 3 px, insignia 16); anillo B r19 3 px con ícono 32; separador 1×36; chip 28 alto, radio 14.
- Colores: fondo #0B0709 al 84 %, borde 1 px #F28DB0 al 35 %; anillos #F8C3D6→#A33A63 (rojo #FF8A8A→#9A2E3A), pista blanco 10 %; chips al 15 %; números #F2F4F7, etiquetas #AE95A0, salvia #A8D8C0, oro #F2C46B, rojo #FF8A8A; borde de aviso 2 px #FF8A8A. Sin sombra exterior.
- Tipografía: Segoe UI Bold (17 números, 13 flecha, 12 chip, 11 etiquetas, 10 insignia).
- Dibujo RGBA a 2× con reducción LANCZOS; retratos circulares en caché; íconos de `datos/meta/ddragon/img`; sin archivo, círculo con la inicial.
- Animaciones: solo finitas por evento (sacudida del aviso ±5 px en 0,5 s y dos pulsos del borde). Se quitan las infinitas y el llenado de anillos. Reducir movimiento de Windows (`SPI_GETCLIENTAREAANIMATION`) las apaga.
- Posición: `colocar()` sin cambios; escala `clamp(alto_juego/1080, 0,75, 2)` en pasos de 0,25; `SetProcessDpiAwareness(2)`.

## 4. Ajustes y borrado
Se quedan `overlay`, `franja_pos`, `franja_linea` («nivel y farm, min 0–14»), `franja_regla` («muertes y peleas, min 14–25»). Se borra `franja_objetivos` (un `ajustes.json` viejo no debe romper). Se borran `partes`, `elegir`, `pieza_aviso`, `MAX_PIEZAS`, `ORDEN`, `reloj`, `AVISO_SEGUNDOS = 12` y los `Label`. `replay.py` valida `estado()`. `meta_fase` gana `participacion`.

## 5. Entrega
- **Fase 0** (humo, sin release): `dev_franja.py` con Tk + PNG de Pillow por `UpdateLayeredWindow` en Practice Tool: esquinas limpias, click-through, encima tras alt-tab, S5 OK. Si falla, plan B.
- **Fase 1 (0.17.0)**: LINEA, PELEAS, TARDE, ARAM, AVISO; ajustes; salud (S5 ≤ 8 %); pruebas; `HTC.spec` con Pillow. Reescribir las pruebas que usan `partes`.
- **Fase 2**: IGUALASTE (3 s, dos destellos salvia, «✓ De vuelta») y ORO14 (5 s, «+340 oro en ítems vs Ahri», «4 / 5 racha de oro»).
- **Pruebas DeepSeek**: bordes de `estado()` (t 599/600, 839/840, 1499/1500; d −2/0/+1; sin rival; sin `cs_meta`; tope 1/2/3/6; 0 kills; ARAM; ajustes apagados; avisos 4,9/5,1 y 7,9/8,1 s); política sobre todos los fixtures de `scripts/fixtures/vivo`; `pintar()` tamaños y alfa, peor caso de textos, < 20 ms; salud S5; `ajustes.json` viejo.
- **Prueba real** (`datos/salud/prueba-6.md`): Practice Tool con `dev_franja.py` y partida normal con `salud.py --cada 60 --foto`; S3–S6 OK, S8 < 1 %, FPS con y sin franja ≤ 2 % de diferencia; DPI 125/150 y reducir movimiento.

## 6. Riesgos
`UpdateLayeredWindow` sobre Tk (fase 0 y plan B); Pillow en el `.exe`; `franja_pos = "abajo"` puede caer sobre el chat; DPI por monitor; la fórmula de `ritmo` es aproximada; «anillo a nivel 6» y «Tu plan» son interpretaciones a revisar contra `deepseek-politica-overlay.md`.

**Decisiones del usuario antes de construir:** 1) aceptar Pillow; 2) quitar los timers de Dragón y Barón de la franja; 3) mostrar el contador de muertes 14–25 aunque la regla de hoy sea la del nivel.

## Revisión de DeepSeek (2026-11-12)

1) Tecnico: UpdateLayeredWindow espera BGRA premultiplicado, no RGBA recto; convierte antes de enviar o habra halos oscuros. WS_EX_LAYERED sobre un toplevel de Tk puede convivir mal con el repintado de Tk; prueba minimizar/restaurar y alt-tab en fase 0. Si hay duda, usa Plan B directo. DPI: SetProcessDpiAwareness debe ir antes de crear Tk y manejar WM_DPICHANGED al mover entre monitores, no solo al inicio. PyInstaller: Pillow requiere hooks y prueba de freeze; no basta agregar al spec. CPU/FPS: plausible a 1 Hz, pero mide con animacion y alpha premultiplicado.

2) Politica: "Tu plan" y "Abajo" siguen siendo interpretables como coaching; cambialos a comparativos neutros, por ejemplo "Diferencia -1" o "Bajo tu regla". "una mas: 43 %" afuera de la franja no debe existir; eliminalo. "CS vs Ahri" / "oro en items vs Ahri" requiere confirmar si nombrar al rival es aceptable; si hay duda, usa "vs rival". Lo demas objetivo y sin timers va alineado.

3) Ritmo CS: la formula es correcta solo si `cs_meta` es el total esperado al minuto 10; documentalo. No uses el `ritmo` redondeado para el umbral 85 %; calcula `objetivo = cs_meta * max(0, t-75) / 525` y compara contra ese flotante: `cs >= objetivo` salvia, `cs >= 0.85*objetivo` oro, si no rojo. Con metas bajas el redondeo produce saltos.

4) Pruebas: falta validar alpha premultiplicado sobre fondo blanco y negro sin halo. Falta mover la ventana entre monitores con distinto DPI y cambio de escala en caliente. Falta minimizar/restaurar/alt-tab con UpdateLayeredWindow. Falta congelar el exe con Pillow y pintar un frame. Falta probar `franja_pos="abajo"` para ver si tapa chat o HUD; y con reducir movimiento activado. Agrega fixtures de `ajustes.json` viejo con claves `partes` y sin claves nuevas.

5) Cambios antes de construir: implementa conversion a BGRA premultiplicado y prueba alpha en fase 0. Haz el Plan B como candidato principal si Tk no soporta bien WS_EX_LAYERED. Reescribe textos segun politica, elimina "una mas" y revisa "Tu plan". Define `cs_meta` explicitamente y usa umbral flotante. Incluye freeze y DPI por monitor desde fase 0/1.
