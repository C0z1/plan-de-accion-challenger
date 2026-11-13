"""Repite una partida grabada (datos/vivo/*.jsonl) por companion.paso_vivo y la pastilla (overlay.estado), sin LoL ni red.
Uso: python scripts/replay.py <archivo.jsonl> [--validar] [--precios]
Cada foto: «mm:ss | franja: … | aviso: …». --validar comprueba invariantes y sale con 1 si alguna falla.
Por defecto no usa Data Dragon (sin pieza de Oro ni aviso de pico) para que la salida sea idéntica en cualquier máquina; --precios lo activa."""
import argparse, contextlib, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import companion, overlay

MAX_PIEZAS = 9  # textos de la pastilla: número y etiqueta ×2, flecha, chip, y al morir el marcador y tu regla
AVISO_CORTO = 48  # plan F1: caracteres del aviso en la franja
LISTA_NEGRA = (  # lo que la franja y los avisos nunca dicen (lista de DeepSeek, avisos-v011.md); se busca como palabra completa
    "cooldown", "enfriamiento", "flash", "destello", "ultimate", "definitiva", "smite", "castigo",  # timers que no se ven
    "respawn", "reaparece", "mmr", "elo", "probabilidad", "campamento",  # reaparición rival, rating, conclusiones, jungla
    "el jungla está", "el jungla va", "troll", "inting", "afk",
    "compra", "cómpralo", "vuelve a base", "backea", "recall")  # la franja dice el dato del ítem, nunca la orden (PLAN-OVERLAY-2)  # posiciones que no ves y juicios de compañeros
VENTANAS = {"aviso_nivel": (5, 7), "aviso_regreso": (10, 14), "aviso_muertes": (14, 24), "aviso_minions": (10, 11)}  # minuto de juego; el pico no tiene ventana
PIEZAS_LINEA = re.compile(r"^(ritmo|CS vs|Nivel |[+-]\d+$)")  # textos de la pastilla que solo existen en la Grieta
BORRAR = {"rawDescription", "rawDisplayName", "rawChampionName", "rawSkinName", "skinID", "skinName", "fullRunes", "runes",
          "abilities", "championStats", "summonerSpells", "teamRelativeColors"}  # pesan y no los usa nada del replay


def cargar(ruta):
    """Fotos en orden; acepta {"foto": …} y descarta fotos repetidas (mismo gameTime) o sin reloj."""
    out, vistos = [], set()
    for l in pathlib.Path(ruta).read_text(encoding="utf-8").splitlines():
        if not l.strip(): continue
        d = json.loads(l); d = d.get("foto", d) if isinstance(d, dict) else d
        t = ((d or {}).get("gameData") or {}).get("gameTime")
        if t is None or t in vistos: continue
        vistos.add(t); out.append(d)
    return out


def anonimizar(fotos):
    """Copia de las fotos con la identidad de cada jugador cambiada por J1.. (tú por Yo#TEST) en todo texto exacto, y sin campos pesados."""
    ap = fotos[0].get("activePlayer") or {}
    mios = {ap.get(k) for k in ("riotId", "summonerName", "riotIdGameName")} - {None, ""}
    mapa, n = {}, 0
    for p in [p for d in fotos for p in d.get("allPlayers") or []]:
        nombres = {p.get(k) for k in ("riotId", "riotIdGameName", "summonerName")} - {None, ""}
        if not nombres or nombres <= set(mapa): continue
        if nombres & mios: g = "Yo"
        else: n += 1; g = f"J{n}"
        for k in ("riotId", "summonerName"):
            if p.get(k): mapa[p[k]] = g + "#TEST"
        if p.get("riotIdGameName"): mapa[p["riotIdGameName"]] = g
        if p.get("riotIdTagLine"): mapa.setdefault(p["riotIdTagLine"], "TEST")
    def rec(x):
        if isinstance(x, dict): return {k: rec(v) for k, v in x.items() if k not in BORRAR}
        if isinstance(x, list): return [rec(v) for v in x]
        return mapa.get(x, x) if isinstance(x, str) else x
    return [rec(d) for d in fotos]


@contextlib.contextmanager
def sin_precios():
    """Sin Data Dragon (ni oro ni ítems completos): la salida no depende de la caché de la máquina; restaura al salir."""
    p, l = companion.precios, companion.LEGENDARIOS
    companion.precios, companion.LEGENDARIOS = (lambda: {}), set()
    try: yield
    finally: companion.precios, companion.LEGENDARIOS = p, l


def reloj(t): return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def repetir(fotos, aj=None):
    """[{t, d, meta, franja:[(texto,color)], avisos:[(clave,texto,minuto)]}] por foto; el reloj local = gameTime (edad 0)."""
    estado, out = {"avisado": set()}, []
    for d in fotos:
        t = d["gameData"]["gameTime"]
        meta, avisos = companion.paso_vivo(d, estado, aj or {})
        if meta: meta = {**meta, "recibido": t}
        out.append({"t": t, "d": d, "meta": meta, "franja": [(x, None) for x in overlay.textos(overlay.estado(meta, t, aj))], "avisos": avisos})
    return out


def texto(r):
    return f"{reloj(r['t'])} | franja: {' · '.join(x[0] for x in r['franja'])} | aviso: {' / '.join(getattr(a[1], 'corto', a[1]) for a in r['avisos'])}"


def _eventos(d): return ((d or {}).get("events") or {}).get("Events") or []


def validar(rs):
    """Lista de fallos (texto); vacía si todo cuadra."""
    f = []
    for r in rs:
        t = reloj(r["t"])
        if len(r["franja"]) > MAX_PIEZAS: f.append(f"{t}: {len(r['franja'])} piezas en la franja (máx. {MAX_PIEZAS})")  # (a)
        if len(r["avisos"]) > 1: f.append(f"{t}: {len(r['avisos'])} avisos a la vez (máx. 1)")
        for clave, txt, _ in r["avisos"]:  # F1: lo que sale en la franja cabe de reojo
            if len(getattr(txt, "corto", "") or "") > AVISO_CORTO or not getattr(txt, "corto", None): f.append(f"{t}: aviso {clave} sin corto de ≤ {AVISO_CORTO} caracteres")
        for clave, _, minuto in r["avisos"]:  # (d)
            lo, hi = VENTANAS.get(clave, (0, 10 ** 6))
            if not lo <= minuto <= hi: f.append(f"{t}: aviso {clave} fuera de su ventana {lo}-{hi} (min {minuto})")
        if r["d"]["gameData"].get("gameMode", "CLASSIC") != "CLASSIC":  # (e)
            f += [f"{t}: pieza de línea «{x[0]}» fuera de CLASSIC" for x in r["franja"] if PIEZAS_LINEA.match(x[0])]
        for txt in [x[0] for x in r["franja"]] + [a[1] for a in r["avisos"]] + [getattr(a[1], "corto", "") or "" for a in r["avisos"]]:  # (f)
            if mal := [w for w in LISTA_NEGRA if re.search(r"\b" + re.escape(w) + r"\b", txt.lower())]: f.append(f"{t}: palabra prohibida {mal} en «{txt}»")
    if rs:  # (c)
        d = rs[-1]["d"]; me, _ = companion.yo_rival(d)
        if me:
            ids = {me.get("riotIdGameName"), me.get("summonerName"), me.get("riotId"), (me.get("riotId") or "").split("#")[0]} - {None, ""}
            ev = sum(1 for e in _eventos(d) if e.get("EventName") == "ChampionKill" and e.get("VictimName") in ids)
            marc = (me.get("scores") or {}).get("deaths")
            if ev != marc: f.append(f"final: el marcador dice {marc} muertes tuyas y los eventos {ev}")
    return f


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("archivo"); ap.add_argument("--validar", action="store_true"); ap.add_argument("--precios", action="store_true")
    a = ap.parse_args(argv)
    with contextlib.nullcontext() if a.precios else sin_precios(): rs = repetir(cargar(a.archivo))
    for r in rs: print(texto(r))
    if a.validar:
        fallos = validar(rs)
        for x in fallos: print("FALLO", x, file=sys.stderr)
        print(f"{len(fallos)} fallo(s)", file=sys.stderr)
        return 1 if fallos else 0
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8"); sys.exit(main())
