# HTC (How to Climb)

Aplicación local de código abierto para jugadores de League of Legends que quieren subir de rango con sus propios datos. Descarga tus partidas de Solo/Duo, calcula estadísticas y reglas accionables, y te las muestra en una ventana mientras juegas. Todo en Python estándar, sin dependencias.

## Para quién

Para un jugador individual que quiere revisar sus propias partidas y seguir reglas concretas para subir su win rate. No es un servicio ni una herramienta de análisis de terceros: corre en tu equipo, con tu cuenta y con tu propia key de desarrollador de Riot.

## Qué muestra

La ventana local tiene nueve vistas:

- **Inicio** — estado del cliente y punto de entrada a la app.
- **Draft** — recomendación de pick y matchup contra tu rival de línea.
- **Selección** — tu plan con el campeón elegido y qué estás cumpliendo.
- **En vivo** — tu rival de línea (nivel, KDA, CS, ítems) y los objetivos de la partida.
- **Perfil** — tu rendimiento: score, win rate y tendencia.
- **Partidas** — historial de tus últimas partidas con score.
- **Campeones** — tu pool y su desempeño en la temporada.
- **Errores** — errores repetidos, con el minuto para buscarlos en el replay.
- **Ajustes** — partidas descargadas y arranque con Windows.

## Instalar y correr

**Windows (app empaquetada):** ejecuta el instalador `HTC-Setup-*.exe`; se instala por usuario, sin permisos de administrador. También puedes correr `dist/HTC/HTC.exe` sin instalar.

**Desde el código** (necesita Python 3, solo librería estándar):

```bash
python scripts/companion_web.py          # abre la ventana local con el cliente abierto
python scripts/companion_web.py --demo   # demo sin cliente: recorre las fases
```

Para descargar y analizar tus partidas hace falta una `RIOT_KEY` de desarrollador (ver abajo). El detalle de los scripts de análisis está en [`docs/USO.md`](docs/USO.md).

## Qué APIs usa y cómo

HTC solo consulta, en lectura, tres fuentes:

- **Riot API (REST)** con la key de desarrollador **del propio usuario** (`RIOT_KEY`): `match-v5` (partidas y timelines), `account-v1` (resolver el PUUID) y `league-v4` (rango). Solo baja partidas de la cuenta que tú indicas.
- **LCU (League Client Update API)**: API local del cliente en `127.0.0.1`, **solo lectura**, para la fase de la partida, la sesión de champ select y tu rango actual.
- **Live Client Data API**: API local en `127.0.0.1:2999` (sin autenticación), **solo lectura**, para los datos de la partida en curso (nivel, oro, ítems, CS, eventos).

No automatiza ninguna acción del cliente: no elige, no banea, no acepta colas y no envía comandos al cliente (solo peticiones de lectura). Usa únicamente datos propios y públicos, y no da ventaja injusta: toda la información ya la tiene el jugador en pantalla.

## Privacidad

Todo es local: los datos quedan en tu equipo. No se suben a git ni se comparten — `datos/raw/` (partidas crudas), `config.json` (tu configuración) y `.env` están en `.gitignore`.

## Licencia

MIT. Ver `LICENSE`.

## Notas del proyecto

Documentación interna del caso de estudio y del trabajo del repositorio:

- `PIZARRON.md` — estado vivo del trabajo y hallazgos.
- `CLAUDE.md` — instrucciones de trabajo del repositorio.
- `PLAN.md` — plan de acción del caso de estudio.
- `BITACORA.md` — bitácora de sesiones.
- `RESUMEN-NOCHE.md` — resumen del turno nocturno.
- `riot.txt` — verificación para Riot.

## Aviso legal

HTC isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
