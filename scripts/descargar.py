"""Descarga partidas de Solo/Duo de Riot API a datos/raw/.
Uso: RIOT_KEY=... [RIOT_ID="Nombre#TAG"] [RIOT_REGION=la1] python scripts/descargar.py [N]
(por defecto cozi#1134 en la1; RIOT_REGION es la plataforma: na1, la1, la2, br1, euw1, eun1, tr1, ru, me1, kr, jp1, oc1, sg2, tw2, vn2)"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse, pathlib, webbrowser


def key_de_usuario():  # variable de usuario de Windows (setx), por si la terminal se abrió antes de cambiarla
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, "RIOT_KEY")[0]
    except (ImportError, OSError):
        return None


KEY = os.environ.get("RIOT_KEY") or key_de_usuario() or sys.exit("Falta RIOT_KEY en el entorno")  # nunca commitear la key
NAME, _, TAG = os.environ.get("RIOT_ID", "cozi#1134").rpartition("#")
PLATAFORMA = os.environ.get("RIOT_REGION", "la1").lower()
RUTA = {"na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas", "euw1": "europe", "eun1": "europe",
        "tr1": "europe", "ru": "europe", "me1": "europe", "kr": "asia", "jp1": "asia", "oc1": "sea", "sg2": "sea",
        "tw2": "sea", "vn2": "sea"}.get(PLATAFORMA) or sys.exit(f"RIOT_REGION desconocida: {PLATAFORMA}")
CUENTA = "asia" if RUTA == "sea" else RUTA  # account-v1 no existe en sea
if not NAME or not TAG: sys.exit('RIOT_ID debe ser "Nombre#TAG"')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
RAW.mkdir(parents=True, exist_ok=True)


def get(url):
    fallos = 0
    while True:
        req = urllib.request.Request(url, headers={"X-Riot-Token": KEY, "User-Agent": "plan-challenger"})  # Riot 403 al UA de urllib
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limit de dev key: esperar lo que pida Riot
                time.sleep(int(e.headers.get("Retry-After", 10)))
                continue
            if e.code in (401, 403):  # companion.py lee el código 2
                print(f"\nRiot respondió {e.code}: renueva RIOT_KEY (la dev key caduca en ~24 h). "
                      "Copia la key nueva del portal (setx RIOT_KEY <key>) y córrelo otra vez.", file=sys.stderr)
                webbrowser.open("https://developer.riotgames.com")
                sys.exit(2)
            if e.code < 500 or fallos >= 3: raise
        except (urllib.error.URLError, TimeoutError):
            if fallos >= 3: raise
        fallos += 1
        time.sleep(5 * fallos)  # 5xx o red: reintentar


def guardar(f, data):  # a .tmp y luego renombrar: un corte no deja JSON a medias
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(f)


acc = get(f"https://{CUENTA}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(NAME)}/{urllib.parse.quote(TAG)}")
puuid = acc["puuid"]
league = get(f"https://{PLATAFORMA}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")
(RAW / "perfil.json").write_text(json.dumps({"account": acc, "league": league}, indent=1))

ids = []
for start in range(0, N, 100):
    ids += get(f"https://{RUTA}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
               f"?queue=420&start={start}&count={min(100, N - start)}")

TL = RAW / "timeline"
TL.mkdir(exist_ok=True)
pendientes = []
for i, mid in enumerate(ids):
    base = f"https://{RUTA}.api.riotgames.com/lol/match/v5/matches/{mid}"
    faltan = [(f, url) for f, url in ((RAW / f"{mid}.json", base), (TL / f"{mid}.json", base + "/timeline")) if not f.exists()]
    try:
        datos = [(f, get(url)) for f, url in faltan]  # bajar las dos antes de guardar: nunca partida sin timeline
    except urllib.error.HTTPError as e:
        if e.code != 404: raise
        pendientes.append(mid)  # Riot aún no procesa la partida recién terminada: queda para la próxima corrida
        continue
    for f, data in datos:
        guardar(f, data)
    print(f"{i + 1}/{len(ids)}", end="\r")
if pendientes: print(f"\nRiot dio 404 en {len(pendientes)} (aún sin procesar, se bajan la próxima vez): {' '.join(pendientes)}", file=sys.stderr)
print(f"\nlisto: {len(ids) - len(pendientes)} de {len(ids)} partidas")
sys.exit(3 if pendientes else 0)  # companion.py: 3 = quedó alguna pendiente
