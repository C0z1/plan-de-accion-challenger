# Plan franja 0.20: «qué buildeo, mi plan y mi match» (Fable, 2026-11-12)

Pedido del usuario: que la franja muestre la mejor información en partida y, de vez en cuando, qué buildear, el plan de partida y el match, sin que Riot lo tome como trampa. Siguen `PLAN-OVERLAY.md` y `COMPETENCIA.md` §4.

## Hallazgos
- El pico del rival ya existe (`aviso_pico`, aviso de 8 s): no se toca.
- La Live Client Data no trae posiciones: no se sabe «en base». Señales de momento muerto: `isDead` y un cambio de tus ítems entre fotos (solo se compra en tienda o muerto).
- `activePlayer.currentGold` existe; `meta_fase` no lo expone, ni tu `position`.
- `builds.guardado_dict` da el core (≤ 3 ítems): con el core completo no hay «próximo ítem».
- `draft` tarda ~3 s en importar: se calcula en el hilo trabajador, una vez por partida, nunca en el overlay.

## 1. Qué se agrega (una cosa nueva a la vez)
Prioridad: AVISO > ORO14 > IGUALASTE > ÍTEM > INICIO (t < 90) > línea / peleas / tarde. ARAM sin cambios.
- **ÍTEM, tu próximo ítem** (ajuste `franja_build`): `companion.proximo(build, tus ítems, oro, Data Dragon)` = primer ítem del core que no tienes y el oro que falta (receta recursiva). Entra con `t ≥ 90` si estás muerto (desde 6 s después de morir, hasta revivir) o si compraste hace < 8 s. Medallón con el ícono del ítem y anillo de progreso, nombre y fuente («tu build» / «build OTPs»), «350 · oro que falta»; con oro suficiente, chip «Alcanza». Nunca «compra».
- **INICIO, tres pantallas por reloj** (ajuste `franja_plan`), de `draft.ficha(rival, pos, champ)`:
  - `t < 30` MATCH: tú vs rival, «3–1 · tu récord», chip «WR 58%» con ≥ 5 partidas; sin partidas contra él, tu WR y «1ª vez».
  - `30 ≤ t < 60` PLAN: «Tu regla · 69+ minions al 10» y tu media.
  - `60 ≤ t < 90` CUIDADO: tu nota escrita del matchup, o tus muertes antes del 6 contra él frente a tu media; si no hay dato, pasa a línea.
- **Objetivos sin timers** (marcador visible con Tab): solo en la expandida (fase 3).

## 2. Límites de Riot
Seguro: stats propias en vivo; lo visible con Tab; historial propio y datos estáticos (récord, WR, reglas, notas, build agregada, precios); regla y nota por reloj fijo.
Prohibido: timers de hechizos/ultis/campamentos enemigos, reaparición del rival, jungla, info no visible, imperativos («compra», «vuelve», «pelea»), predicción de victoria.
Descartado por cercano al límite: aviso «ya juntaste el oro» en el momento (equivale a «vuelve a base»); estimado de victoria del matchup; tu respawn; ítem situacional según la composición rival; timers de objetivos. Reescribir las `meta` en imperativo de `draft.REGLAS_CHAMP`. Lista negra de `replay`: + «compra», «cómpralo», «vuelve a base», «backea», «recall».

## 3. Diseño
Mismos huecos (a, b, chip). `pintar`: medallón con `{"item": id}`; texto en dos renglones con `e.get("texto")` (alarma solo en aviso). `marcar`: marcas `muerte` y `compra`. Expandida 380×110 solo muerto: después de probar fases 1 y 2.

## 4. Entrega
- **Fase 1 (0.20.0) ÍTEM**: `meta_fase` + `pos`, `oro_actual`; `companion.proximo()`, `plan_partida()`; trabajador calcula el plan una vez por partida; evento `partida`; overlay; ajuste `franja_build`; lista negra.
- **Fase 2 (0.20.1) INICIO**: `estado(plan=…)`; `draft.py` sin imperativos; ajuste `franja_plan`.
- **Fase 3 (opcional)**: expandida al morir con objetivos y regla.
- Pruebas: `proximo()` (sin build, core completo, componente intermedio, dos copias, oro de sobra, id ausente); `marcar` (muerte 5,9/6,1 s, compra 7,9/8,1 s, antes de 90 s, partida nueva); prioridades; política; `pintar` (nombre largo, sin ícono, < 20 ms).
- Prueba real (`datos/salud/prueba-7.md`): Practice Tool comprando y muriendo; inicio de partida; S3–S6 OK, CPU < 1 %; luego una normal.

## 5. Riesgos y decisiones
Retraso de la foto tras comprar; sin build o sin posición no hay ÍTEM ni INICIO; build de 3 ítems; cambio de línea.
Decisiones (aplicadas las recomendadas mientras el usuario no diga otra cosa): 1) la build de la franja es la misma que Selección (OTPs top y, si no hay, la tuya, etiquetada); 2) la expandida se decide después de jugar con las fases 1 y 2.
