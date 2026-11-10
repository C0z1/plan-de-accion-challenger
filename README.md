# HTC · How to Climb

**Tu coach de League of Legends, hecho con tus propias partidas.**

HTC es una app de escritorio para Windows, de código abierto. Descarga tus partidas de Solo/Duo, encuentra qué te hace ganar y qué te hace perder, y te lo muestra en el momento justo: en el champ select, durante la partida y al terminarla. Se abre sola cuando abres LoL.

No te da consejos genéricos. Todo lo que dice sale de tus partidas («con 0 muertes sin objetivo ganas el 81%, con 2 o más, el 27%»).

## Cómo te acompaña en una partida

| Momento | Qué ves |
|---|---|
| Abres LoL | **Inicio**: estado del cliente y un resumen de tu cuenta. |
| Champ select | **Draft**: qué pickear de tu pool contra tu rival de línea y por qué. Cuando él pickea, **Selección**: tu récord contra él, tu WR y «Tu plan con <campeón>», 3 reglas con cuántas veces las cumples. |
| En partida | **En vivo**: tu nivel y CS contra los de tu rival, tus muertes desde el minuto 14, sus ítems y los objetivos (dragón, barón, heraldo, torres) con sus timers. Se actualiza cada 30 s. |
| Al terminar | Tu KDA contra tu rival, si cumpliste la meta de muertes y, con key de Riot, la revisión completa de la partida. |

Además, siempre a mano:

- **Perfil**: score, WR, tendencia, tilt del día y tus 3 puntos más débiles contra lo típico de tu rol.
- **Partidas**: historial con resultado, KDA, score y el factor que más pesó.
- **Campeones**: cómo te va con cada uno esta temporada.
- **Errores**: los errores que repites («Morir sin objetivo», «Pelea perdida sin ti», …), con el minuto para buscarlos en el replay.
- **Ajustes**: partidas descargadas y arranque con Windows.

## Instalar

**Windows:** descarga `HTC-Setup-<versión>.exe` y ejecútalo. Se instala solo para tu usuario, sin permisos de administrador, y puede arrancar con Windows para abrirse sola junto a LoL.

**Desde el código** (Python 3, solo la librería estándar, sin `pip install`):

```bash
git clone https://github.com/C0z1/plan-de-accion-challenger.git
cd plan-de-accion-challenger
python scripts/companion_web.py          # con el cliente de LoL abierto
python scripts/companion_web.py --demo   # sin cliente: recorre las fases con datos de ejemplo
```

## Configurar tu cuenta

HTC usa la Riot API con **tu propia key**. Las partidas se quedan en tu equipo.

1. Consigue una key en [developer.riotgames.com](https://developer.riotgames.com). La de desarrollo caduca cada 24 h.
2. Guárdala junto con tu cuenta como variables de usuario de Windows (no hace falta guardarlas en ningún archivo):
   ```powershell
   setx RIOT_KEY "RGAPI-..."
   setx RIOT_REGION "la1"      # na1, la1, la2, br1, euw1, eun1, tr1, ru, me1, kr, jp1, oc1, sg2, tw2, vn2
   setx RIOT_ID "TuNombre#TAG"  # opcional: sin esto usa la cuenta con sesión en el cliente de LoL
   ```
3. Baja tus partidas (100 por defecto):
   ```bash
   python scripts/descargar.py 100
   ```
4. Opcional: copia `config.ejemplo.json` a `config.json` para fijar tu pool de campeones y tu meta de minions al 10. Si no lo haces, HTC toma como pool tus 3 campeones más jugados.

Sin key, HTC funciona igual en el champ select y en partida con las partidas que ya bajaste. Lo único que no sale es la revisión completa al terminar.

Opciones avanzadas (otra cuenta, carpetas, lockfile del cliente) y los scripts de análisis: [`docs/USO.md`](docs/USO.md).

## Juego limpio y privacidad

HTC solo **lee** datos, de tres fuentes:

- **Riot API** (`match-v5`, `account-v1`, `league-v4`), con tu key y solo para tu cuenta.
- **API local del cliente (LCU)**, en `127.0.0.1`: la fase de la partida, el champ select y tu rango.
- **Live Client Data API**, en `127.0.0.1:2999`: los datos de la partida en curso.

No pickea, no banea, no acepta colas ni envía comandos al cliente. Solo muestra información que ya tienes en pantalla o en tu historial, así que no da ventajas injustas.

Todo se queda en tu equipo. `datos/raw/` (tus partidas), `config.json` y `.env` están en `.gitignore`.

## Contribuir

Los issues y PRs son bienvenidos.

```bash
python -m unittest discover scripts   # sin red, sin key y sin partidas (usa scripts/fixtures)
```

GitHub Actions corre las pruebas en Windows y Ubuntu en cada push. Reglas del código: Python estándar sin dependencias, nada que escriba en el cliente, y ninguna cifra en la app sin un análisis que la respalde.

Estructura:

- `scripts/companion_web.py`: la app (servidor local y ventana).
- `scripts/vistas.py` y `scripts/web/`: las vistas.
- `scripts/companion.py`: lectura del cliente y de la partida en vivo.
- `scripts/descargar.py`: la descarga de partidas.
- `instalador/`: el build y el instalador (PyInstaller + Inno Setup).

## Licencia

[MIT](LICENSE).

## Aviso legal

HTC isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
