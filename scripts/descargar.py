"""Descarga partidas de Solo/Duo de Riot API a datos/raw/.
Uso: RIOT_KEY=... [RIOT_ID="Nombre#TAG"] [RIOT_REGION=la1] python scripts/descargar.py [N]
(sin RIOT_ID usa la cuenta con sesión en el cliente de LoL; RIOT_REGION por defecto la1; RIOT_REGION es la plataforma: na1, la1, la2, br1, euw1, eun1, tr1, ru, me1, kr, jp1, oc1, sg2, tw2, vn2)"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse, pathlib, webbrowser


def key_de_usuario():  # variable de usuario de Windows (setx), por si la terminal se abrió antes de cambiarla
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            return winreg.QueryValueEx(k, "RIOT_KEY")[0]
    except (ImportError, OSError):
        return None


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import companion  # noqa: E402  (lcu y acceso al backend; solo lectura)

KEY = os.environ.get("RIOT_KEY") or (None if os.environ.get("RACHA_SOLO_BACKEND") else key_de_usuario())  # nunca commitear la key
PROXY = None if KEY else companion.acceso()  # sin key propia: el backend de Racha con tu código de acceso
if not KEY and not PROXY: sys.exit("Falta RIOT_KEY o tu código de acceso de Racha (Ajustes → Cuenta)")
def riot_id():
    """RIOT_ID del entorno o, si no está, la cuenta con sesión en el cliente de LoL (LCU, solo lectura)."""
    if os.environ.get("RIOT_ID"): return os.environ["RIOT_ID"]
    s = companion.lcu("/lol-summoner/v1/current-summoner") or {}
    if s.get("gameName") and s.get("tagLine"): return f"{s['gameName']}#{s['tagLine']}"
    return (guardada() or {}).get("riot_id")  # cliente cerrado: la cuenta que guardaste en Ajustes


def guardada():
    """La cuenta guardada en Ajustes (datos/cache/cuenta.json), o None."""
    import json
    try: return json.loads((pathlib.Path(__file__).resolve().parent.parent / "datos" / "cache" / "cuenta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError): return None


NAME, _, TAG = (riot_id() or sys.exit('Falta tu cuenta: abre el cliente de LoL o escribe tu Riot ID en Ajustes')).rpartition("#")
def plataforma():
    """RIOT_REGION, o la del cliente de LoL (platformId de tu historial, solo lectura), o la1."""
    if os.environ.get("RIOT_REGION"): return os.environ["RIOT_REGION"]
    h = companion.lcu("/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=0") or {}
    return str(h.get("platformId") or (guardada() or {}).get("region") or "la1")


PLATAFORMA = plataforma().lower()
RUTA = {"na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas", "euw1": "europe", "eun1": "europe",
        "tr1": "europe", "ru": "europe", "me1": "europe", "kr": "asia", "jp1": "asia", "oc1": "sea", "sg2": "sea",
        "tw2": "sea", "vn2": "sea"}.get(PLATAFORMA) or sys.exit(f"RIOT_REGION desconocida: {PLATAFORMA}")
CUENTA = "asia" if RUTA == "sea" else RUTA  # account-v1 no existe en sea
if not NAME or not TAG: sys.exit('RIOT_ID debe ser "Nombre#TAG"')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
RAW.mkdir(parents=True, exist_ok=True)


def get(url):
    global KEY, PROXY
    fallos = 0
    while True:
        if PROXY:  # https://<host>.api.riotgames.com/<path> → <api>/v1/riot/<host>/<path>, con tu código en vez de la key
            host, _, path = url[len("https://"):].partition(".api.riotgames.com")
            cred = {"Authorization": "Bearer " + PROXY[1]} if len(PROXY[1]) == 64 else {"X-Racha-Token": PROXY[1]}  # sesión de Google o código
            req = urllib.request.Request(f"{PROXY[0]}/v1/riot/{host}{path}", headers={**cred, "User-Agent": "racha"})
        else:
            req = urllib.request.Request(url, headers={"X-Riot-Token": KEY, "User-Agent": "plan-challenger"})  # Riot 403 al UA de urllib
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limit de dev key: esperar lo que pida Riot
                time.sleep(int(e.headers.get("Retry-After", 10)))
                continue
            if PROXY and e.code in (401, 503):  # código inválido o la key del servidor caducó: no abrir el portal de Riot
                print("\nTu código de acceso no sirve (revísalo en Ajustes)." if e.code == 401 else
                      "\nEl servidor de Racha no puede hablar con Riot ahora: avísale a quien te dio el código.", file=sys.stderr)
                sys.exit(2)
            if KEY and e.code in (401, 403) and (alt := companion.acceso()):  # tu key caducó pero tienes código: al backend
                KEY, PROXY = None, alt; continue
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
