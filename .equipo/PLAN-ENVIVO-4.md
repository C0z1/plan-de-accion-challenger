# Plan En vivo, ronda 4 (Fable) · v0.14.4 local

Siguen vigentes las prohibiciones de `PLAN-ENVIVO.md` sección 5. Fable simuló en memoria los valores reales: **21a se reproduce; 21b no se reproduce como está descrito.** Resultados de la prueba 3 en `datos/salud/prueba-3.md` (local).

## 1. Decisiones

| Hallazgo | Decisión | Cómo, o por qué |
|---|---|---|
| 19 S8 en falso | Queda bien | `edad_antes` sin dato cuenta como viejo, igual que el 17. |
| 20 cuenta ajena | Arreglar en dos puntos | `refrescar()`: dentro del LOCK, si `gui.ajeno(gui.CUENTA[0])` entonces `r = None`; si `r is None` escribe también `previa=None`. `vistas_previas()`: dentro de su LOCK, si es ajena, `previa = None` (el hilo viejo puede seguir dentro de `vistas_previas` después de que el nuevo limpió). |
| 20 «ultima» | No ocultar | Es la última partida grabada en esta PC, no el historial del dueño; no trae la regla ni porcentajes. |
| 21a `unir_eventos` | Arreglar | `TEMBLOR = 1` (s) en `companion.py`; la guarda pasa a `t(previos) > t(d) + TEMBLOR`. |
| 21b pausa | Verificar primero, endurecer barato | `meta["t"]` ya es `int(gameTime)`: el temblor del 6.º decimal no explica el serrucho. Hipótesis: la 1.ª foto tras cada reconexión se compara con la de antes de matar el juego, sale `pausa=False` y el timer baja 10 s (un diente por reconexión). Si R4 lo confirma, se acepta (máx. 10 s, una vez, solo práctica/custom). Si es continuo, se busca la causa antes de tocar nada. |

**Por qué 1 s.** El temblor medido (7,63e-6 s) es un paso de float32 entre 64 y 128 s; crece con el reloj (4,9e-4 s entre 68 y 136 min). 1 s es 2000 veces eso y 10 veces menos que el sondeo de 10 s. Otra partida empieza cerca de 0 y ya la corta `archivo is None`.

**Endurecimiento de 21b.** `pausa = abs(t − t_anterior) <= TEMBLOR`. Cubre un temblor que cruce un segundo entero. Con el juego corriendo, entre fotos pasan ~10 s: sin falsos positivos.

## 2. DeepSeek (pruebas que fallen hoy)
- **DS-4** (`test_ds_eventos_pausa.py`, +5): (1) previos `t=122.41705322` con GameStart@0 y MinionsSpawning@30, `d` `t=122.41704559` con solo GameStart@122.41704559: quedan los 2 originales en orden; (2) cadena de 2 reconexiones + foto en pausa: siempre 2 eventos; (3) `DragonKill@400` y `d` 4,9e-4 menor con reinicio: se conserva; (4) previos 123.5, `d` 122.4: `d` intacta; (5) previos 1500, `d` 12: intacta.
- **DS-5** (`test_ds_pausa.py`, sobre `evento(('meta', …))`): 122→123 `pausa` True (falla hoy); 122→122 True; 122→132 False; primera foto False; `t` None False; con `pausa` True, `overlay.partes` 7 s después sigue igual.
- **DS-6** (`test_ds_cuenta_ajena.py`): quitar el `expectedFailure` con B2; `vistas_previas` con cuenta que se vuelve ajena dentro de `gui.recomendaciones` deja `previa` None y conserva `ultima`; ajena desde el inicio: `rendimiento` y `previa` None; propia conserva `previa`.
- **DS-7**: revisión del diff (sección «Ronda 4», ≤ 20 renglones) y `deepseek-al-llegar.md` al día.

## 3. Opus
B1 `TEMBLOR` y las dos guardas · B2 hallazgo 20 · B3 `dev_practica.py --espera N` (+1 caso) · B4 suite, `VERSION = "0.14.4"`, commit · B5 prueba real 4 en `datos/salud/prueba-4.md` · B6 cerrar DS-7 y push sin release (autorizado por el usuario el 2026-11-12).

## 4. Prueba real 4 (cuenta del cliente ajena, sin input al juego)
«DOM limpio»: sin `cozi#1134`, `68/103`, `Yasuo`, `undefined`, `NaN` ni `Error:`.

| Paso | Qué hace Opus | Cuenta como OK |
|---|---|---|
| R0 | Racha desde el código, cliente en None/Lobby; `salud.py --vistas`; `/api/estado` | S10 OK en las 9 vistas; `rendimiento` y `previa` null y siguen así 60 s después; DOM limpio; sin franja (S6) |
| R1 | `dev_practica.py 245 --espera 25`; en selección captura las 9 vistas y la franja | ChampSelect; vista por defecto «Draft» con rol y reloj; `#companion` sin «Vista previa contra tu rival más frecuente»; `#envivo` sin «Tu regla de hoy … %»; franja oculta; S2 OK |
| R2 | Carga y entrada | Sin franja en GameStart; franja ≤ 20 s después de `gameTime` > 0; S5 OK |
| R3 | Antes del min 4: 9 vistas y 5 pasadas de salud (R5) | «En vivo» por defecto con campeón, reloj ±12 s y reglas; DOM limpio; dragón = 300 − `gameTime` ±2 s; 5 pasadas OK; CPU < 1 % |
| R4 | Matar el juego y `reconectar` ×2; `meta.t`, `pausa` y franja cada 2 s, 60 s | Franja se oculta ≤ 30 s y vuelve ≤ 20 s; `.jsonl` con GameStart@0 y MinionsSpawning@30 una vez y ningún GameStart > 0; 1 solo `.jsonl`; `pausa` False como mucho en la 1.ª foto de cada reconexión. S3 FALLA por pausa: esperado |
| R6 | `salir`; `/api/estado` y vistas | Franja oculta ≤ 30 s; En vivo con «Al terminar (foto en vivo)»; en Lobby `rendimiento` y `previa` siguen null; sin avisos de error |
| R7 | Segunda práctica (R1–R3) sin reiniciar Racha | Igual; `.jsonl` nuevo desde GameStart@0, sin eventos de la anterior |

No cubre: Selección con rival real, datos propios en las vistas (cuenta ajena), pausa que cruce un segundo entero (solo sintética).

## 5. Solo el usuario
1. Entrar con cozi#1134: Selección con rival real, Perfil, Partidas y Campeones con sus datos.
2. Partida normal con `salud.py --cada 60 --foto`; si reconecta, dragones y muertes 14–25 siguen contados.
3. FPS con Ctrl+F, franja prendida y apagada.
4. Permiso para el release de la 0.14.4.

**Riesgo:** la explicación del serrucho es hipótesis. Si en una partida real los eventos vuelven con `EventTime` temblado, la clave de `unir_eventos` (`str(EventTime)`) duplicaría eventos; en práctica no se vio.
