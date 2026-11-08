"""Companion del cliente de LoL (solo lectura: nunca hace POST/PATCH ni actúa por el jugador).
Uso:
  python scripts/companion.py                        sondea el cliente cada 3 s
  python scripts/companion.py --fixture scripts/fixtures/champselect   una pasada con JSON de ejemplo
- ChampSelect: identifica tu posición y a tu rival (o a todos los rivales ya elegidos si no se sabe su rol)
  y corre draft.py; imprime una vez por cada cambio de rivales.
- EndOfGame/PreEndOfGame: espera 60 s y corre descargar.py 5 y revision.py 1 (si la key caducó, lo avisa).
Lockfile: C:\\Riot Games\\League of Legends\\lockfile (o la variable LOL_LOCKFILE)."""
import argparse, base64, json, os, pathlib, ssl, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
DIR = pathlib.Path(__file__).resolve().parent
LOCK = pathlib.Path(os.environ.get("LOL_LOCKFILE", r"C:\Riot Games\League of Legends\lockfile"))
POS = {"top": "TOP", "jungle": "JUNGLE", "middle": "MIDDLE", "bottom": "BOTTOM", "utility": "UTILITY"}
SSL = ssl.create_default_context(); SSL.check_hostname = False; SSL.verify_mode = ssl.CERT_NONE  # cert propio del cliente, solo 127.0.0.1


def lcu(path):
    """GET a la API local del cliente; None si el cliente está cerrado."""
    try:
        _, _, port, pw, proto = LOCK.read_text().split(":")
        auth = base64.b64encode(f"riot:{pw}".encode()).decode()
        req = urllib.request.Request(f"{proto}://127.0.0.1:{port}{path}", headers={"Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, context=SSL, timeout=5) as r: return json.load(r)
    except (OSError, ValueError): return None  # sin lockfile, cliente cerrándose o 404 fuera de champ select


def rivales(s):
    """(tu posición de Riot, [championId de tus rivales]) de una sesión de /lol-champ-select/v1/session."""
    me = next((p for p in s.get("myTeam", []) if p.get("cellId") == s.get("localPlayerCellId")), {})
    pos = POS.get(me.get("assignedPosition", ""), "MIDDLE")  # sin rol asignado (normales): mid, como draft.py
    elegidos = [p for p in s.get("theirTeam", []) if p.get("championId")]
    mismo = [p["championId"] for p in elegidos if POS.get(p.get("assignedPosition", "")) == pos]
    if any(p.get("assignedPosition") for p in s.get("theirTeam", [])): return pos, mismo  # con roles: espera a tu rival, no al jungla
    return pos, sorted(p["championId"] for p in elegidos)


def nombres():
    """championId -> championName sacado de tus partidas en datos/raw (sin red)."""
    m = {}
    for f in (pathlib.Path(os.environ.get("DATOS_DIR") or DIR.parent / "datos" / "raw")).glob("*_*.json"):
        for p in json.loads(f.read_text())["info"]["participants"]: m[p["championId"]] = p["championName"]
    return m


def recomendar(pos, ids, m):
    import draft  # carga tus partidas: solo al entrar a champ select
    if len(ids) > 1: print(f"(rol del rival desconocido: van los {len(ids)} rivales elegidos)")
    for i in ids:
        if i not in m: print(f"\nRival id {i}: no aparece en tus partidas.\n"); continue
        print(f"\n=== {m[i]} ({pos}) ==="); draft.draft(m[i], pos)


def post_partida():
    print("Partida terminada: espero 60 s a que Riot la publique…"); time.sleep(60)
    r = subprocess.run([sys.executable, str(DIR / "descargar.py"), "5"])
    if r.returncode == 2: print("\n*** renueva RIOT_KEY y corre: python scripts/descargar.py 5 && python scripts/revision.py 1 ***\n"); return
    if r.returncode == 3: print("Riot aún no publica la partida (404): en unos minutos corre python scripts/descargar.py 5 && python scripts/revision.py 1"); return
    if r.returncode: print(f"descargar.py falló ({r.returncode}); la partida queda pendiente."); return
    subprocess.run([sys.executable, str(DIR / "revision.py"), "1"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", metavar="CARPETA", help="una pasada con gameflow-phase.json y session.json de esa carpeta (sin cliente)")
    a = ap.parse_args(argv)
    get = lcu
    if a.fixture:
        d = pathlib.Path(a.fixture)
        get = lambda path: json.loads((d / ("session.json" if "champ-select" in path else "gameflow-phase.json")).read_text())
    m, visto, fase_ant = None, None, None
    while True:
        fase = get("/lol-gameflow/v1/gameflow-phase")
        if fase is None and fase_ant != "cerrado": print("Cliente cerrado: espero…")
        elif fase != fase_ant: print(f"Fase: {fase}")
        if fase == "ChampSelect" and (s := get("/lol-champ-select/v1/session")):
            pos, ids = rivales(s)
            if ids and (pos, ids) != visto:
                m = m or nombres(); recomendar(pos, ids, m); visto = (pos, ids)
        elif fase != "ChampSelect": visto = None
        if fase in ("PreEndOfGame", "EndOfGame") and fase_ant not in ("PreEndOfGame", "EndOfGame") and get is lcu: post_partida()
        fase_ant = fase or "cerrado"
        if get is not lcu: return
        time.sleep(3)


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
