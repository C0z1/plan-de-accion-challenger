# Plan: la app y el overlay de Racha (desde la v0.11)

Fecha: 2026-11-10. Autor: Opus, con la investigación de DeepSeek (`~/noche-challenger/competencia.md`) y su plan de negocio (`~/noche-challenger/plan-negocio.md`, pendiente de revisión).

## Qué nos distingue (no perderlo)

1. Coaching con TUS partidas: reglas medidas en ti, errores con minuto, revisión con 3 momentos, tu semana, tu pick de hoy, tú contra el onetrick. Nadie más lo hace.
2. Ligera y limpia: sin Overwolf, sin anuncios, sin cuenta obligatoria para lo básico, código abierto.
3. Social chico: tabla del grupo entre amigos.

Todo lo nuevo debe reforzar el punto 1 dentro de la partida, no copiar a los demás por copiar.

## Principios

- Política de Riot primero: nada de MMR, nada de información oculta (cooldowns enemigos, campamentos que no ves), nada que actúe por ti sin tu clic, nada de anuncios en el juego.
- El cómputo pesado se queda en la PC del jugador (gratis y escala solo); el servidor solo guarda lo mínimo.
- Rendimiento medido: la franja no debe costar FPS; CPU en reposo < 1 % (hoy 0,19 %).
- Cada cosa con su prueba y verificada en pantalla; lo de partida, en una partida real antes de darlo por terminado.

## Fase A — Overlay que sí ayuda (v0.11, $0)

| # | Qué | Dato que usa | Riesgo Riot | Esfuerzo |
|---|---|---|---|---|
| A1 | Oro por línea: tu valor de ítems contra el de tu rival (y del equipo) en la franja y en En vivo | `allPlayers[].items` (lo mismo que ves con Tab) | Bajo | S |
| A2 | Pico de poder del rival: aviso cuando tu rival de línea termina un ítem legendario o llega a 6/11/16 | ítems y nivel visibles | Bajo | S |
| A3 | Tu regla de hoy dentro de la partida (la que más te cuesta, con su número) | reglas de vistas.py | Bajo | S |
| A4 | Franja configurable: qué piezas mostrar y en qué esquina; tecla para ocultarla | ajustes | Nulo | M |
| A5 | Importar runas y hechizos con UN clic en selección (la build de los onetricks o la tuya), nunca automático | LCU escritura `/lol-perks/v1/pages` | Medio: declararlo al registrar la app; nunca auto-pick/ban/aceptar | M |
| A6 | Medir FPS con y sin franja en partida real y dejar el número en el README | partida real | Nulo | S |

Descartado a propósito: timers de campamentos (la API no avisa cuándo se limpian, ni los tuyos), cooldowns de hechizos/ultimates enemigos (prohibido o al límite), grabar video.

## Fase B — Beta con amigos de verdad ($0)

- 10 a 20 amigos con la v0.11; checklist de validación (`~/noche-challenger/validacion-partida-real-v010.md`).
- Métricas opt-in y reportes ya existen: mirar cada semana.
- Criterio para pasar a C: 10+ usuarios activos por semana y retención a 4 semanas de 40 %+.

## Fase C — Lanzamiento público (primer gasto)

- Production key de Riot (texto listo en `~/noche-challenger/docs010/riot-registro.md`).
- Firma del instalador y dominio: solo cuando la fase B lo justifique (montos en `plan-negocio.md`).

## Fase D — Ingresos

- Tier gratis intacto; de pago solo lo transformador (definido con los números de `plan-negocio.md`).

## Proceso de trabajo

- Opus construye; DeepSeek investiga, revisa cada versión (bugs, seguridad), escribe pruebas de borde y docs; un constructor Sonnet en worktree para piezas aisladas.
- Cada versión: pruebas en verde, revisión de DeepSeek, verificación en pantalla, release con el permiso del usuario.
