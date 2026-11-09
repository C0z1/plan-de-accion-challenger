"""Companion con UI web local (diseño del canvas): el mismo trabajador que companion_gui.py (solo lectura del cliente),
servido en 127.0.0.1 y abierto como app de Edge (o en el navegador por defecto).
Uso:
  python scripts/companion_web.py            sondea el cliente cada 3 s
  python scripts/companion_web.py --demo     champ select con datos de ejemplo (sin cliente)
  python scripts/companion_web.py --no-abrir no abre ventana (para pruebas)
El servidor se cierra solo si la ventana deja de preguntar 60 s."""
import http.server, json, pathlib, queue, re, shutil, subprocess, sys, threading, time, urllib.request, webbrowser

import companion_gui as gui  # noqa: E402  (trae REPO, sys.path del .exe y el trabajador)
from companion_gui import companion

WEB = gui.REPO / "scripts" / "web"
if not WEB.exists(): WEB = pathlib.Path(getattr(sys, "_MEIPASS", "")) / "web"  # el .exe lejos del repo usa la copia empaquetada
IMG = gui.REPO / "datos" / "meta" / "ddragon" / "img"
LOCK = threading.Lock()
ESTADO = {"fase": "inicio", "perfil": gui.perfil(), "draft": None, "meta": None, "fin": None, "revision": None,
          "aviso": None, "espera": None, "rango": None, "rendimiento": None, "v": 0}
VERSION = "0.2.0"  # HTC; también invalida la caché de rendimiento
VIVO = [time.time()]  # último GET de la ventana


def draft_json(pos, recs):
    """Lo que la página necesita de recomendaciones(): sin las listas de partidas (vs/en), con el récord y los renglones de lineas_ficha."""
    out = []
    for r, d in recs:
        if not d: out.append({"rival": r, "conocido": False}); continue
        vs = d.get("vs") or []
        cuidado, counters = gui.lineas_ficha(d.get("ficha"))
        out.append({"rival": r, **{k: v for k, v in d.items() if k not in ("vs", "en")}, "v": sum(g["win"] for g in vs), "n": len(vs),
                    "lineas": {"cuidado": cuidado, "counters": counters}})
    return {"pos": pos, "recs": out}


def evento(e):
    """Aplica un evento de la cola (los mismos que App.evento de companion_gui) al estado."""
    tipo, s = e[0], {}
    if tipo == "fase":
        s = {"fase": e[1]}
        if e[1] == "ChampSelect": s.update(draft=None, fin=None, meta=None)
        if e[1] in ("Lobby", "Matchmaking", "ReadyCheck"): s.update(aviso=None, perfil=gui.perfil(ESTADO["rango"]))
    elif tipo == "draft": s = {"draft": draft_json(e[1], e[2])}
    elif tipo == "meta": s = {"meta": {**e[1], "texto": gui.texto_meta(e[1])}}
    elif tipo == "fin": s = {"fin": {**e[1], "texto": companion.linea_fin(e[1])}}
    elif tipo == "post_espera": s = {"espera": e[1]}
    elif tipo == "revision":
        s = {"revision": e[1], "fin": None, "espera": None, "perfil": gui.perfil(ESTADO["rango"])}
        threading.Thread(target=refrescar, daemon=True).start()
    elif tipo == "rango": s = {"rango": e[1] or ESTADO["rango"]}; s["perfil"] = gui.perfil(s["rango"])
    elif tipo == "aviso": s = {"aviso": e[1]}
    with LOCK: ESTADO.update(s, v=ESTADO["v"] + 1)


def rendimiento(raw=None):
    """Ventana 2 (Perfil): score.resumen(20) y score.tilt(); None si no hay partidas en disco."""
    import score
    try: return {"resumen": score.resumen(20, raw), "tilt": score.tilt(raw)}
    except (OSError, ValueError, KeyError, StopIteration): return None


CACHE = gui.REPO / "datos" / "cache" / "rendimiento.json"


def firma(raw):
    """(n, mtime máx, bytes) de las partidas y timelines, y la fecha de score.py: si cambia algo, la caché ya no vale."""
    import score
    fs = [f.stat() for f in pathlib.Path(raw).rglob("*.json")]
    return [len(fs), max((s.st_mtime_ns for s in fs), default=0), sum(s.st_size for s in fs), pathlib.Path(score.__file__).stat().st_mtime_ns]


def rendimiento_rapido(raw=None, cache=None):
    """rendimiento() desde la caché en disco si las partidas no cambiaron (abre al instante); si no, lo calcula y la reescribe."""
    import score, os
    raw = pathlib.Path(raw or os.environ.get("DATOS_DIR") or gui.REPO / "datos" / "raw"); cache = pathlib.Path(cache or CACHE)
    try: f = firma(raw)
    except OSError: return rendimiento(raw)
    try:
        c = json.loads(cache.read_text(encoding="utf-8"))
        if c.get("firma") == f and c.get("version") == VERSION: return c["datos"]
    except (OSError, ValueError, KeyError, AttributeError): pass
    r = rendimiento(raw)
    if r is not None:
        try:  # escritura atómica: dos instancias a la vez no dejan un JSON a medias
            cache.parent.mkdir(parents=True, exist_ok=True); tmp = cache.with_suffix(f".{os.getpid()}.tmp")
            tmp.write_text(json.dumps({"version": VERSION, "firma": f, "datos": r}, ensure_ascii=False, default=str), encoding="utf-8")
            os.replace(tmp, cache)
        except OSError: pass
    return json.loads(json.dumps(r, ensure_ascii=False, default=str)) if r is not None else None  # misma forma que desde la caché


def bombear(q):
    while True: evento(q.get())


def refrescar():  # lee ~300 JSON (o la caché): en su hilo, para no frenar la cola
    r = rendimiento_rapido()
    with LOCK: ESTADO.update(rendimiento=r, v=ESTADO["v"] + 1)


def estado():
    with LOCK: return json.dumps(ESTADO, ensure_ascii=False, default=str)


def imagen(tipo, nombre):
    """PNG de Data Dragon (campeón por nombre o ítem por id), en caché en disco; None si no existe."""
    import builds
    if tipo == "champion":
        c = builds.ddragon()[2].get(builds.norm(nombre))
        if not c: return None
        nombre = c[0]  # «Wukong» → «MonkeyKing»
    f = IMG / tipo / f"{nombre}.png"
    if not f.exists():
        v = builds.get("https://ddragon.leagueoflegends.com/api/versions.json", ttl=builds.DIA)[0]
        try:
            with urllib.request.urlopen(f"https://ddragon.leagueoflegends.com/cdn/{v}/img/{tipo}/{nombre}.png", timeout=15) as r: b = r.read()
        except OSError: return None
        f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(b)
    return f.read_bytes()


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def enviar(self, code, cuerpo, tipo):
        self.send_response(code); self.send_header("Content-Type", tipo); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; img-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        self.end_headers(); self.wfile.write(cuerpo)

    def do_GET(self):
        # contra DNS rebinding: otra web no puede leer el estado aunque resuelva su dominio a 127.0.0.1
        if self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"): return self.enviar(403, b"", "text/plain")
        VIVO[0] = time.time()
        if self.path == "/": return self.enviar(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/estado": return self.enviar(200, estado().encode(), "application/json; charset=utf-8")
        if m := re.fullmatch(r"/img/(champion|item)/(\w{1,40})\.png", self.path):
            if b := imagen(*m.groups()): return self.enviar(200, b, "image/png")
        self.enviar(404, b"", "text/plain")


def abrir(url):
    edge = shutil.which("msedge") or next((str(p) for p in (pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                                                            pathlib.Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")) if p.exists()), None)
    if edge: subprocess.Popen([edge, f"--app={url}", "--window-size=1440,1024"])
    else: webbrowser.open(url)


def demo(q):
    """Lo mismo que el --demo de companion_gui: champ select de la fixture con tus datos."""
    fx = gui.REPO / "scripts" / "fixtures" / "champselect" / "session.json"
    pos, ids = companion.rivales(json.loads(fx.read_text())) if fx.exists() else ("MIDDLE", [])
    m = companion.nombres(); rivales = [m.get(i) for i in ids] or ["Zed"]
    q.put(("fase", "ChampSelect")); q.put(("draft", pos, gui.recomendaciones(pos, rivales[:1])))
    vivo = gui.REPO / "scripts" / "fixtures" / "vivo" / "allgamedata.json"  # luego la partida y el fin, de la foto en vivo
    if not vivo.exists() or not (mf := companion.meta_fase(d := json.loads(vivo.read_text(encoding="utf-8")))): return
    time.sleep(8); q.put(("fase", "InProgress")); q.put(("meta", mf))
    time.sleep(8); q.put(("fase", "EndOfGame")); q.put(("fin", companion.resumen_fin(d)))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); url = f"http://127.0.0.1:{srv.server_port}/"
    q = queue.Queue()
    threading.Thread(target=bombear, args=(q,), daemon=True).start()
    threading.Thread(target=refrescar, daemon=True).start()
    threading.Thread(target=demo if "--demo" in argv else gui.trabajador, args=(q,), daemon=True).start()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(url, flush=True)
    if "--no-abrir" not in argv: abrir(url)
    while time.time() - VIVO[0] < 60: time.sleep(2)  # la ventana pregunta cada 2 s: si se cerró, salimos
    srv.shutdown()


if __name__ == "__main__":
    main()
