"""Companion con UI web local (diseño del canvas): el mismo trabajador que companion_gui.py (solo lectura del cliente),
servido en 127.0.0.1 y abierto como app de Edge (o en el navegador por defecto).
Uso:
  python scripts/companion_web.py            sondea el cliente cada 3 s
  python scripts/companion_web.py --demo     champ select con datos de ejemplo (sin cliente)
  python scripts/companion_web.py --no-abrir no abre ventana (para pruebas)
  python scripts/companion_web.py --fondo    en segundo plano (arranca con Windows): abre la ventana sola al abrir el cliente de LoL
Sin --fondo, el servidor se cierra solo si la ventana deja de preguntar 60 s. Si ya hay un HTC abierto, abre su ventana y sale."""
import html, http.server, json, pathlib, queue, re, shutil, subprocess, sys, threading, time, urllib.parse, urllib.request, webbrowser

import companion_gui as gui  # noqa: E402  (trae REPO, sys.path del .exe y el trabajador)
from companion_gui import companion

WEB = gui.REPO / "scripts" / "web"
if not WEB.exists(): WEB = pathlib.Path(getattr(sys, "_MEIPASS", "")) / "web"  # el .exe lejos del repo usa la copia empaquetada
IMG = gui.REPO / "datos" / "meta" / "ddragon" / "img"
LOCK = threading.Lock()
ESTADO = {"fase": "inicio", "perfil": gui.perfil(), "draft": None, "meta": None, "fin": None, "revision": None,
          "aviso": None, "espera": None, "rango": None, "cuenta": None, "crono": None, "ajustes": gui.ajustes(), "descarga": None, "nueva": None, "previa": None, "ultima": None, "sin_marco": False, "nube": None, "plataforma": None, "conectado": companion.acceso(gui.REPO) is not None, "icono": None, "region": None, "cliente": None, "rendimiento": None, "pos": None, "autoarranque": None, "v": 0}
VERSION = "0.7.0"  # HTC; también invalida la caché de rendimiento
VIVO = [time.time()]  # último GET de la ventana
URL, FONDO = [None], [False]
PUERTO = gui.REPO / "datos" / "cache" / "htc.port"  # el HTC que ya corre: otro arranque abre su ventana en vez de duplicarse


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
        if FONDO[0] and ESTADO["fase"] in (None, "inicio") and e[1] is not None and time.time() - VIVO[0] > 6:
            abrir(URL[0])  # el cliente acaba de abrir y no hay ventana de HTC (si la hubiera, preguntaría cada 2 s)
        if e[1] == "ChampSelect": s.update(draft=None, fin=None, meta=None, pos=None)
        if e[1] in ("Lobby", "Matchmaking", "ReadyCheck"): s.update(aviso=None, perfil=gui.perfil(ESTADO["rango"], ESTADO["cuenta"]))
    elif tipo == "draft": s = {"draft": {**draft_json(e[1], e[2]), "probable": bool(e[3]) if len(e) > 3 else False}}
    elif tipo == "meta": s = {"meta": {**e[1], "texto": gui.texto_meta(e[1]), "recibido": time.time()}}  # «recibido»: el overlay descuenta los timers
    elif tipo == "fin": s = {"fin": {**e[1], "texto": companion.linea_fin(e[1])}}
    elif tipo == "post_espera": s = {"espera": e[1]}
    elif tipo == "revision":
        s = {"revision": e[1], "fin": None, "espera": None, "perfil": gui.perfil(ESTADO["rango"], ESTADO["cuenta"])}
        threading.Thread(target=refrescar, daemon=True).start()
    elif tipo == "rango": s = {"rango": e[1] or ESTADO["rango"]}; s["perfil"] = gui.perfil(s["rango"], ESTADO["cuenta"])
    elif tipo == "cuenta":  # la cuenta con sesión en el cliente: manda sobre perfil.json (un amigo, u otra cuenta en tu PC)
        gui.CUENTA[0] = e[1]; s = {"cuenta": e[1], "perfil": gui.perfil(ESTADO["rango"], e[1]), "icono": e[2] if len(e) > 2 else None}
        threading.Thread(target=refrescar, daemon=True).start()  # si el historial en disco es de otra cuenta, se oculta
    elif tipo == "cliente": s = {"cliente": e[1]}
    elif tipo == "region": s = {"region": e[1], **({"plataforma": e[2]} if len(e) > 2 else {})}
    elif tipo == "crono": s = {"crono": e[1]}
    elif tipo == "aviso": s = {"aviso": e[1]}
    elif tipo == "pos": s = {"pos": e[1]}  # champ select antes de ver al rival: la ventana Draft
    with LOCK: ESTADO.update(s, v=ESTADO["v"] + 1)


def rendimiento(raw=None):
    """Ventana 2 (Perfil): score.resumen(20) y score.tilt(); None si no hay partidas en disco."""
    import score
    try: r = {"resumen": score.resumen(20, raw), "tilt": score.tilt(raw)}
    except (OSError, ValueError, KeyError, StopIteration): return None
    if raw is None:  # las ventanas nuevas (vistas.py) leen datos/raw de draft.py; con otra carpeta no aplican
        try:
            import vistas; r["vistas"] = vistas.todo(r["resumen"])
        except Exception: r["vistas"] = None  # sin partidas suficientes draft.py truena al importar: las ventanas dicen «sin datos»
    return r


CACHE = gui.REPO / "datos" / "cache" / "rendimiento.json"


def firma(raw):
    """(n, mtime máx, bytes) de las partidas y timelines, y la fecha de score.py: si cambia algo, la caché ya no vale."""
    fs = [f.stat() for f in pathlib.Path(raw).rglob("*.json")]
    codigo = [(gui.REPO / "scripts" / f).stat().st_mtime_ns if (gui.REPO / "scripts" / f).exists() else 0 for f in ("score.py", "draft.py", "vistas.py")]
    return [len(fs), max((s.st_mtime_ns for s in fs), default=0), sum(s.st_size for s in fs), *codigo]


def rendimiento_rapido(raw=None, cache=None):
    """rendimiento() desde la caché en disco si las partidas no cambiaron (abre al instante); si no, lo calcula y la reescribe."""
    import score, os
    pedido, raw = raw, pathlib.Path(raw or os.environ.get("DATOS_DIR") or gui.REPO / "datos" / "raw"); cache = pathlib.Path(cache or CACHE)
    try: f = firma(raw)
    except OSError: return rendimiento(pedido)
    try:
        c = json.loads(cache.read_text(encoding="utf-8"))
        if c.get("firma") == f and c.get("version") == VERSION: return c["datos"]
    except (OSError, ValueError, KeyError, AttributeError): pass
    r = rendimiento(pedido)  # pedido, no la ruta resuelta: con None, rendimiento() agrega las vistas
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
    r = None if gui.ajeno(gui.CUENTA[0]) else rendimiento_rapido()  # historial de otra cuenta: no mostrarlo como tuyo
    with LOCK: ESTADO.update(rendimiento=r, v=ESTADO["v"] + 1)
    if r is not None: tus_builds(); vistas_previas(r)
    sync_nube()


def nube_publica():
    """Lo que la página puede ver de tu sesión (sin el token)."""
    import nube
    s = nube.sesion()
    return {k: s.get(k) for k in ("email", "nombre", "sync")} if s else None


def sync_nube():
    """Sube a tu cuenta en la nube tu Riot ID, tus ajustes y el resumen de tus partidas (si iniciaste sesión)."""
    import nube
    if not nube.sesion(): return
    with LOCK: e = dict(ESTADO)
    nube.sincronizar(None if gui.ajeno(gui.CUENTA[0]) else e.get("rendimiento"), e.get("cuenta"), e.get("plataforma"), e.get("ajustes"))
    with LOCK: ESTADO.update(nube=nube_publica(), v=ESTADO["v"] + 1)


def vistas_previas(r):
    """Fuera del champ select y de la partida, Selección y En vivo no quedan vacías: Selección = tu mejor pick contra tu
    rival más frecuente (lo mismo que verías en champ select); En vivo = la última foto de tu última partida grabada."""
    previa = ultima = None
    try:
        V = (r or {}).get("vistas") or {}
        pos = V.get("pos"); fr = ((V.get("draft") or {}).get(pos) or {}).get("frecuentes") or []
        if pos and fr:
            previa = dict(draft_json(pos, gui.recomendaciones(pos, [fr[0]["rival"]])), previa=True)
    except Exception: previa = None  # sin partidas suficientes draft.py truena: Selección muestra Draft como antes
    try:
        fs = sorted(companion.VIVO.glob("*.jsonl"))
        if fs:
            lineas = fs[-1].read_text(encoding="utf-8").strip().splitlines()
            d = json.loads(lineas[-1]); d = d.get("foto", d)
            if (m := companion.meta_fase(d)): ultima = {**m, "texto": gui.texto_meta(m), "recibido": None, "archivo": fs[-1].stem}
    except (OSError, ValueError, KeyError, IndexError, AttributeError): ultima = None
    with LOCK: ESTADO.update(previa=previa, ultima=ultima, v=ESTADO["v"] + 1)


RELEASES = "https://api.github.com/repos/C0z1/racha.gg/releases/latest"


def version_mayor(a, b):
    """True si la versión a («v0.6.1») es mayor que b («0.6.0»); lo que no se entienda, False."""
    try: return tuple(map(int, a.lstrip("v").split("."))) > tuple(map(int, b.lstrip("v").split(".")))
    except (ValueError, AttributeError): return False


def buscar_version():
    """Al arrancar: ¿hay una versión de Racha más nueva en GitHub Releases? Solo avisa (no instala nada)."""
    try:
        req = urllib.request.Request(RELEASES, headers={"User-Agent": "racha", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r: d = json.load(r)
    except (OSError, ValueError): return
    if version_mayor(d.get("tag_name", ""), VERSION) and str(d.get("html_url", "")).startswith("https://github.com/"):
        with LOCK: ESTADO.update(nueva={"version": d["tag_name"], "url": d["html_url"]}, v=ESTADO["v"] + 1)


def primera_vez():
    """Un amigo con código de acceso y sin partidas: su historial se baja solo al abrir Racha (no tiene que buscar el botón)."""
    import os
    raw = pathlib.Path(os.environ.get("DATOS_DIR") or gui.REPO / "datos" / "raw")
    if not gui.puede_descargar() or any(raw.glob("*_*.json")): return
    if not (companion.lcu("/lol-summoner/v1/current-summoner") or {}).get("gameName"): return  # sin cliente: se reintenta al abrir LoL
    descargar_todo()


DESCARGANDO = threading.Lock()


def descargar_todo(n=100):
    """Baja tus últimas n partidas (descargar.py, con tu key o tu código) y recalcula todo; el avance va a «descarga»."""
    if not DESCARGANDO.acquire(blocking=False):  # ya hay una en curso
        with LOCK: ESTADO.update(descarga="Ya se están bajando tus partidas…", v=ESTADO["v"] + 1)
        return
    try:
        def aviso(t):
            with LOCK: ESTADO.update(descarga=t, v=ESTADO["v"] + 1)
        if not gui.puede_descargar(): return aviso("Falta tu código de acceso (o una RIOT_KEY).")
        if gui.ajeno(gui.CUENTA[0]):  # el historial de esta PC es de otra cuenta: bajarlo pisaría su perfil.json
            return aviso("Esta PC guarda el historial de otra cuenta: para el tuyo, usa Racha en tu PC.")
        aviso("Descargando tus partidas… puede tardar unos minutos la primera vez.")
        code, out = gui.script("descargar.py", str(n))
        if code in (0, 3):
            ult = (out.strip().splitlines() or [""])[-1].strip()
            aviso("Listo: " + (ult[len("listo: "):] if ult.lower().startswith("listo: ") else ult) + " al día."); refrescar()
        else: aviso((out.strip().splitlines() or [f"falló ({code})"])[-1])
    finally: DESCARGANDO.release()


def tus_builds():
    """«Tu build» sin key (builds.guardar_tuyas) si hay partidas más nuevas que builds.json; un fallo no tumba nada."""
    import builds, os
    raw = pathlib.Path(os.environ.get("DATOS_DIR") or gui.REPO / "datos" / "raw"); f = builds.META / "builds.json"
    try:
        nuevo = max((p.stat().st_mtime for p in raw.glob("*_*.json")), default=0)
        if nuevo and (not f.exists() or f.stat().st_mtime < nuevo): builds.guardar_tuyas()
    except Exception: pass


def vigilar_cuenta(q, cada=10):
    """Cada `cada` s lee la cuenta con sesión en el cliente (solo lectura); al cambiar, manda su rango y su «gameName#tag»."""
    ultima, vuelta, m = None, 0, None
    while True:
        s = companion.lcu("/lol-summoner/v1/current-summoner") or {}
        nueva = s.get("gameName") and (c := f"{s['gameName']}#{s.get('tagLine', '')}") != ultima
        if nueva:
            ultima = c; q.put(("rango", companion.rango(companion.lcu("/lol-ranked/v1/current-ranked-stats"))))
            q.put(("cuenta", c, s.get("profileIconId")))
            if ESTADO.get("conectado"): threading.Thread(target=primera_vez, daemon=True).start()  # LoL recién abierto
        if s.get("gameName") and (nueva or vuelta % 6 == 0):  # tus últimas partidas del cliente (sin key): al conectar y cada minuto
            h = companion.lcu("/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=19")
            if h:
                q.put(("region", REGION.get(str(h.get("platformId") or "").upper(), h.get("platformId")), str(h.get("platformId") or "").lower()))
                if not gui.NOMBRES: gui.NOMBRES.update(companion.nombres_lcu())
                m = m or {**gui.NOMBRES, **companion.nombres()}; q.put(("cliente", companion.historial(h, m)))
        vuelta += 1; time.sleep(cada)


def precargar():  # import draft lee tus ~300 partidas (~4 s): al arrancar, para que el primer champ select no lo espere
    try: import draft  # noqa: F401
    except Exception: pass  # sin partidas suficientes truena; el trabajador lo reporta al llegar a champ select


def estado():
    with LOCK: return json.dumps(ESTADO, ensure_ascii=False, default=str)


RANGOS = {"iron", "bronze", "silver", "gold", "platinum", "emerald", "diamond", "master", "grandmaster", "challenger"}
REGION = {"LA1": "LAN", "LA2": "LAS", "NA1": "NA", "BR1": "BR", "EUW1": "EUW", "EUN1": "EUNE", "KR": "KR", "JP1": "JP",
          "OC1": "OCE", "TR1": "TR", "RU": "RU", "ME1": "ME", "SG2": "SEA", "TW2": "TW", "VN2": "VN"}


def imagen(tipo, nombre):
    """PNG de Data Dragon (campeón por nombre o ítem por id), en caché en disco; None si no existe."""
    import builds
    if tipo == "champion":
        d, n = builds.ddragon()[2], builds.norm(nombre)
        # «Nunu & Willump» llega como «NunuWillump»: si no hay exacto, el campeón más largo que sea prefijo («nunu»)
        c = d.get(n) or d.get(max((k for k in d if n.startswith(k)), key=len, default=""))
        if not c: return None
        nombre = c[0]  # «Wukong» → «MonkeyKing»
    if tipo == "rango" and nombre not in RANGOS: return None
    if tipo == "minion" and nombre != "caster": return None
    f = IMG / tipo / f"{nombre}.png"
    if not f.exists():
        if tipo == "minion":  # acuerdo 21: el caster de CommunityDragon en la tarjeta de CS
            url = "https://raw.communitydragon.org/latest/game/assets/characters/sru_orderminionranged/hud/bluerange_circle.png"
        elif tipo == "rango":  # emblema de la liga (CommunityDragon: los mismos archivos que usa el cliente)
            url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-emblem/emblem-{nombre}.png"
        else:
            v = builds.get("https://ddragon.leagueoflegends.com/api/versions.json", ttl=builds.DIA)[0]
            url = f"https://ddragon.leagueoflegends.com/cdn/{v}/img/{tipo}/{nombre}.png"  # champion, item, profileicon
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "racha"}), timeout=15) as r: b = r.read()
        except OSError: return None
        f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(b)
    return f.read_bytes()


RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"


def autoarranque(on=None):
    """¿HTC arranca con Windows (HKCU Run «HTC» = exe --fondo)? Con on, lo pone o lo quita. None fuera del .exe."""
    if not getattr(sys, "frozen", False) or gui.winreg is None: return None
    w = gui.winreg
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER, RUN, 0, w.KEY_READ | w.KEY_SET_VALUE) as k:
            if on is True: w.SetValueEx(k, "HTC", 0, w.REG_SZ, f'"{sys.executable}" --fondo')
            elif on is False:
                try: w.DeleteValue(k, "HTC")
                except FileNotFoundError: pass
            try: return bool(w.QueryValueEx(k, "HTC")[0])
            except FileNotFoundError: return False
    except OSError: return None


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def enviar(self, code, cuerpo, tipo):
        self.send_response(code); self.send_header("Content-Type", tipo); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; img-src 'self'; font-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
        self.end_headers(); self.wfile.write(cuerpo)

    def do_GET(self):
        # contra DNS rebinding: otra web no puede leer el estado aunque resuelva su dominio a 127.0.0.1
        if self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"): return self.enviar(403, b"", "text/plain")
        VIVO[0] = time.time()
        if self.path == "/": return self.enviar(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        if m := re.fullmatch(r"/fonts/(mulish|inter)\.woff2", self.path):  # empaquetadas (OFL): la CSP no deja cargar Google Fonts
            return self.enviar(200, (WEB / "fonts" / f"{m.group(1)}.woff2").read_bytes(), "font/woff2")
        if self.path in ("/icono.png", "/favicon.ico"): return self.enviar(200, (WEB / "icono.png").read_bytes(), "image/png")  # ícono de la ventana de Edge --app
        if self.path.startswith("/oauth?"):  # Google vuelve aquí tras «Continuar con Google» (el navegador del usuario)
            import nube
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            try:
                nube.completar((q.get("code") or [""])[0], (q.get("state") or [""])[0], self.server.server_address[1])
                with LOCK: ESTADO.update(nube=nube_publica(), v=ESTADO["v"] + 1)
                threading.Thread(target=sync_nube, daemon=True).start()
                msg = "Listo: tu cuenta de Racha quedó guardada en la nube. Ya puedes cerrar esta pestaña y volver a Racha."
            except (ValueError, OSError) as e: msg = str(e) if isinstance(e, ValueError) else "No pude hablar con el servidor de Racha."
            pagina = f'<!doctype html><meta charset="utf-8"><title>Racha</title><body style="margin:0;display:grid;place-items:center;height:100vh;background:#24111A;color:#F2F4F7;font:600 18px Segoe UI,sans-serif"><p style="max-width:460px;text-align:center">{html.escape(msg)}</p>'
            return self.enviar(200, pagina.encode(), "text/html; charset=utf-8")
        if self.path == "/api/estado" or self.path.startswith("/api/estado?"):
            if self.path == f"/api/estado?desde={ESTADO['v']}":  # nada cambió desde la última vez: sin cuerpo (auditoría de DeepSeek)
                self.send_response(304); self.send_header("Cache-Control", "no-store"); self.end_headers(); return
            return self.enviar(200, estado().encode(), "application/json; charset=utf-8")
        if m := re.fullmatch(r"/img/(champion|item|profileicon|rango|minion)/(\w{1,40})\.png", self.path):
            if b := imagen(*m.groups()): return self.enviar(200, b, "image/png")
        self.enviar(404, b"", "text/plain")

    def do_POST(self):
        # X-HTC obliga a un preflight CORS que no contestamos: otra web no puede mandar este POST, aunque el Host cuadre
        if self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost") or self.headers.get("X-HTC") != "1":
            try: self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 4096))  # leer antes de rechazar: si no,
            except (ValueError, OSError): pass                                              # Windows corta la conexión
            return self.enviar(403, b"", "text/plain")
        if self.path in ("/api/google", "/api/google/salir", "/api/google/borrar", "/api/google/sync"):
            import nube
            if self.path == "/api/google":
                try: url = nube.iniciar(self.server.server_address[1])
                except (OSError, ValueError): url = None
                if not url: return self.enviar(503, b'{"error":"sin servidor o sin cliente de Google"}', "application/json")
                webbrowser.open(url); return self.enviar(200, b"{}", "application/json")
            if self.path == "/api/google/sync": threading.Thread(target=sync_nube, daemon=True).start()
            else:
                try: nube.borrar_todo() if self.path.endswith("borrar") else nube.salir()
                except (OSError, ValueError): return self.enviar(502, b"", "text/plain")
                with LOCK: ESTADO.update(nube=None, v=ESTADO["v"] + 1)
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/ventana":  # botones y arrastre de la franja propia (la ventana ya no tiene barra de Windows)
            import ventana
            try:
                d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 200)))
                ventana.accion(d["accion"], float(d.get("alto", 0)), float(d.get("dpr", 1)))
            except (ValueError, KeyError, TypeError): return self.enviar(400, b"", "text/plain")
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/descargar":  # «Descargar mis partidas»: con tu key o tu código de acceso, en su hilo
            threading.Thread(target=descargar_todo, daemon=True).start(); return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/acceso":
            try: gui.guardar_acceso(json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 200)))["token"])
            except (ValueError, KeyError, TypeError, OSError): return self.enviar(400, b"", "text/plain")
            with LOCK: ESTADO.update(descarga="Código guardado. Ya puedes descargar tus partidas.", conectado=True, v=ESTADO["v"] + 1)
            threading.Thread(target=primera_vez, daemon=True).start()  # con el cliente abierto, empieza a bajar sola
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/recargar":  # Ajustes_Vino «Recargar»: vuelve a leer tus partidas del disco, con aviso
            def recargar():
                with LOCK: ESTADO.update(descarga="Recalculando tus estadísticas…", v=ESTADO["v"] + 1)
                refrescar()
                with LOCK: ESTADO.update(descarga="Listo: tus estadísticas están al día.", v=ESTADO["v"] + 1)
            threading.Thread(target=recargar, daemon=True).start(); return self.enviar(200, b"{}", "application/json")
        if self.path not in ("/api/autoarranque", "/api/ajuste"): return self.enviar(404, b"", "text/plain")
        try: d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 200))); on = d["on"]
        except (ValueError, KeyError, TypeError): return self.enviar(400, b"", "text/plain")
        if not isinstance(on, bool): return self.enviar(400, b"", "text/plain")
        if self.path == "/api/ajuste":
            try: a = gui.guardar_ajuste(d.get("clave"), on)
            except (ValueError, OSError): return self.enviar(400, b"", "text/plain")
            with LOCK: ESTADO.update(ajustes=a, v=ESTADO["v"] + 1)
            threading.Thread(target=sync_nube, daemon=True).start()  # tus ajustes también van a la nube
            return self.enviar(200, json.dumps(a).encode(), "application/json")
        a = autoarranque(on)
        with LOCK: ESTADO.update(autoarranque=a, v=ESTADO["v"] + 1)
        self.enviar(200, json.dumps({"on": a}).encode(), "application/json")


def abrir(url):
    edge = shutil.which("msedge") or next((str(p) for p in (pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                                                            pathlib.Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")) if p.exists()), None)
    if edge:
        subprocess.Popen([edge, f"--app={url}", "--window-size=1440,1024"])
        import ventana  # sin barra de título de Windows (Ventana_Vino); si no se puede, queda la barra normal
        def listo():
            with LOCK: ESTADO.update(sin_marco=True, v=ESTADO["v"] + 1)
        threading.Thread(target=ventana.sin_marco, kwargs={"al_listo": listo}, daemon=True).start()
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


def otro_htc():
    """URL del HTC que ya corre (responde /api/estado), o None."""
    try:
        url = f"http://127.0.0.1:{int(PUERTO.read_text())}/"
        with urllib.request.urlopen(url + "api/estado", timeout=1) as r: return url if r.status == 200 else None
    except (OSError, ValueError): return None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    unico = not ({"--demo", "--no-abrir"} & set(argv))  # las pruebas y la demo no tocan al HTC real
    if unico and (url := otro_htc()):
        if "--fondo" not in argv: abrir(url)
        return
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); url = f"http://127.0.0.1:{srv.server_port}/"
    URL[0], FONDO[0] = url, "--fondo" in argv
    if FONDO[0]: VIVO[0] = 0  # aún no hay ventana: si el cliente ya está abierto, la primera fase la abre
    ESTADO["autoarranque"] = autoarranque(); ESTADO["nube"] = nube_publica()
    if unico:
        try: PUERTO.parent.mkdir(parents=True, exist_ok=True); PUERTO.write_text(str(srv.server_port))
        except OSError: pass
    q = queue.Queue()
    threading.Thread(target=bombear, args=(q,), daemon=True).start()
    threading.Thread(target=refrescar, daemon=True).start()
    if unico: threading.Thread(target=precargar, daemon=True).start()
    if "--demo" not in argv: threading.Thread(target=vigilar_cuenta, args=(q,), daemon=True).start()
    if unico:  # solo el Racha real: ni la demo ni las pruebas salen a internet ni descargan
        threading.Thread(target=buscar_version, daemon=True).start(); threading.Thread(target=primera_vez, daemon=True).start()
    threading.Thread(target=demo if "--demo" in argv else gui.trabajador, args=(q,), daemon=True).start()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(url, flush=True)
    if not FONDO[0] and "--no-abrir" not in argv: abrir(url)
    seguir = lambda: FONDO[0] or time.time() - VIVO[0] < 60  # la ventana pregunta cada 2 s: si se cerró (y no es --fondo), salimos
    if "--overlay" in argv or not ({"--demo", "--no-abrir", "--sin-overlay"} & set(argv)):
        def leer():
            with LOCK: return dict(ESTADO)
        try: import overlay; overlay.correr(leer, seguir)  # franja en partida; ocupa el hilo principal (tkinter)
        except Exception: pass  # sin tkinter o sin pantalla: HTC sigue sin overlay
    while seguir(): time.sleep(2)
    srv.shutdown()


if __name__ == "__main__":
    main()
