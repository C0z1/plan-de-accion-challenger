# Política de overlays, Vanguard y Practice Tool

DeepSeek (Sonnet de reemplazo), 2026-11-11. Sin red: solo lo que ya hay en el repo y en `C:\Users\felix\noche-challenger\politica-lcu.md` (que cita a Riot textualmente). Cada afirmación lleva fuente o «sin verificar». No es asesoría legal.

## Overlays

- Riot lista como aprobado «Game overlays that provide static data that is available prior to the game». Fuente: https://developer.riotgames.com/docs/lol (citado en `politica-lcu.md` §4).
- Riot prohíbe «Products may not provide any game-session-specific information that would be previously unknown to the player» y «Apps that dictate player decisions». Misma fuente. La franja solo muestra lo que se ve con Tab (Live Client Data) y avisos cortos sin órdenes: eso es decisión de diseño de `PLAN-ENVIVO.md` §5, no una aprobación de Riot. Si el timer de dragón que se descuenta con el reloj local cuenta como «previamente desconocido»: sin verificar (se deduce de eventos que el jugador ya vio).
- «Drawing conclusions for you during gameplay» está en la lista de lo que cruza la línea (https://support.riotgames.com/en-us/riot/events/third-party-applications, citado en `politica-lcu.md` §1). Avisos como «2 muertes desde el 14 · tu tope» son un dato y tu propia regla; si Riot los lee como conclusión: sin verificar.
- Que overlays de terceros como Blitz o Mobalytics operen aprobados: sin verificar (no hay cita en el repo).
- La franja es una ventana siempre-encima que no inyecta, no lee memoria ni manda entradas (`scripts/overlay.py`, docstring y `atravesable`). Que eso baste ante Vanguard: sin verificar.

## Vanguard

- El repo no cita ninguna fuente de Riot sobre Vanguard. Solo dice que la tecla para ocultar (F7) está «EN ESPERA hasta saber cómo lo toma Vanguard» (`.equipo/PLAN-ENPARTIDA.md`) y fija las reglas «no leer memoria, no mandar entradas ni mover la ventana del juego, no hooks de teclado, no editar `game.cfg`» (`PLAN-ENVIVO.md` §5).
- Que Vanguard bloquee o tolere una ventana tkinter topmost y transparente a clics: sin verificar. La primera prueba real (P1) será la única evidencia.
- Que `GetAsyncKeyState` o un hook de teclado disparen Vanguard: sin verificar (por eso F7 sigue en espera).
- Leer `Config/game.cfg` (lo hace `companion.pantalla_completa()`, solo lectura) como riesgo: sin verificar; el plan prohíbe editarlo, no leerlo.

## Practice Tool

- La captura `datos/vivo/20261109-173828.jsonl` trae `gameMode` `PRACTICETOOL`, mapa 11 y 1 jugador (comprobado en el archivo): la Live Client Data responde en Practice Tool.
- Que Riot permita crear el lobby de Practice Tool por LCU (`scripts/dev_practica.py`): sin verificar. Contexto: la LCU «is not officially supported for use with third party applications» y pide declarar los endpoints (https://developer.riotgames.com/league-client-apis.html, `politica-lcu.md` §2-3). El plan limita la escritura a un script de desarrollo no distribuido, solo Practice Tool, y nunca colas, aceptar partida ni pick/ban (`PLAN-ENVIVO.md` §5).
- Que una partida de Practice Tool no tenga riesgo para la cuenta con software de terceros corriendo: sin verificar.

## Resumen
Lo que Riot permite o prohíbe aquí viene de citas ya guardadas. Vanguard y Practice Tool no tienen fuente en el repo: tratarlos como riesgo desconocido hasta que lo confirme Riot o la prueba real.
