"""Companion con UI web local (diseño del canvas): el mismo trabajador que companion_gui.py (solo lectura del cliente),
servido en 127.0.0.1 y abierto como app de Edge (o en el navegador por defecto).
Uso:
  python scripts/companion_web.py            sondea el cliente cada 3 s
  python scripts/companion_web.py --demo     champ select con datos de ejemplo (sin cliente)
  python scripts/companion_web.py --no-abrir no abre ventana (para pruebas)
  python scripts/companion_web.py --fondo    en segundo plano (arranca con Windows): abre la ventana sola al abrir el cliente de LoL
Sin --fondo, desde el código, el servidor se cierra solo si la ventana deja de preguntar 60 s (el .exe instalado sigue en segundo plano). Si ya hay un HTC abierto, abre su ventana y sale."""
import ventana  # noqa: E402
import html, http.server, json, os, pathlib, queue, re, shutil, subprocess, sys, threading, time, urllib.parse, urllib.request, webbrowser

import companion_gui as gui  # noqa: E402  (trae REPO, sys.path del .exe y el trabajador)
from companion_gui import companion

WEB = gui.REPO / "scripts" / "web"
if not WEB.exists(): WEB = pathlib.Path(getattr(sys, "_MEIPASS", "")) / "web"  # el .exe lejos del repo usa la copia empaquetada
IMG = gui.REPO / "datos" / "meta" / "ddragon" / "img"
LOCK = threading.Lock()
ESTADO = {"fase": "inicio", "perfil": gui.perfil(), "draft": None, "meta": None, "fin": None, "revision": None,
          "aviso": None, "avisos": [], "espera": None, "rango": None, "cuenta": None, "crono": None, "tablero": None, "comentario": None, "mover_franja": False, "al_dia": None, "ajustes": gui.ajustes(), "descarga": None, "nueva": None, "previa": None, "ultima": None, "nube": None, "plataforma": None, "conectado": companion.acceso(gui.REPO) is not None, "icono": None, "region": None, "cliente": None, "rendimiento": None, "pos": None, "autoarranque": None, "admin": None, "grupo": None, "pantalla_completa": None, "coach": gui.coach(), "reporte": None, "invitacion": None, "v": 0}
VERSION = "0.21.2"  # HTC; también invalida la caché de rendimiento
ESTADO["version"] = VERSION  # la página se recarga si cambia (Racha se actualizó con la ventana abierta)
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


SIRVIO = {"si": 0, "no": 0, "no_vi": 0}  # «¿te sirvieron los avisos?» (v0.13): contadores para el ping opt-in, sin identidad
AVISO_ENTRE, AVISO_MAX = 90, 6  # F1: separación mínima entre avisos en la franja y tope por partida


def franja_libre(previos, ahora):
    """¿Puede salir otro aviso en la franja? Como mucho AVISO_MAX por partida y AVISO_ENTRE s desde el último que salió."""
    salidos = [a["franja"] for a in previos if a.get("franja")]
    return len(salidos) < AVISO_MAX and (not salidos or ahora - max(salidos) >= AVISO_ENTRE)


def evento(e):
    """Aplica un evento de la cola (los mismos que App.evento de companion_gui) al estado."""
    tipo, s = e[0], {}
    if tipo == "fase":
        s = {"fase": e[1]}
        if FONDO[0] and ESTADO["fase"] in (None, "inicio") and e[1] is not None and not ventana.viva() and time.time() - VIVO[0] > 6:
            abrir(URL[0])  # el cliente acaba de abrir y no hay ventana de Racha
        if ESTADO["fase"] in ("InProgress", "Reconnect") and e[1] not in ("InProgress", "Reconnect"):  # hallazgo 24: «Tu última partida» = la que acaba de terminar
            threading.Thread(target=vistas_previas, args=(ESTADO.get("rendimiento"),), daemon=True).start()
        if e[1] == "ChampSelect": s.update(tablero=None, comentario=None, draft=None, fin=None, meta=None, pos=None, avisos=[]); USADO.add("champ_select")
        if e[1] in ("ChampSelect", "InProgress"): s["pantalla_completa"] = companion.pantalla_completa()  # la franja no se vería
        if e[1] == "InProgress" and ESTADO["ajustes"].get("overlay", True): USADO.add("overlay")
        if e[1] in ("Lobby", "Matchmaking", "ReadyCheck"): s.update(aviso=None, perfil=gui.perfil(ESTADO["rango"], ESTADO["cuenta"]))
    elif tipo == "draft": s = {"draft": {**draft_json(e[1], e[2]), "probable": bool(e[3]) if len(e) > 3 else False}}
    elif tipo == "meta":  # el mismo gameTime que la foto anterior: juego en pausa (práctica, custom): los timers se congelan
        antes = (ESTADO.get("meta") or {}).get("t")
        pausa = e[1].get("t") is not None and antes is not None and abs(e[1]["t"] - antes) <= companion.TEMBLOR
        s = {"meta": {**e[1], "texto": gui.texto_meta(e[1]), "recibido": time.time(), "pausa": pausa}}  # «recibido»: el overlay descuenta los timers
    elif tipo == "fin":  # el tope de tu coach (F12) también en la línea final; y el ping sale aunque no llegue la revisión de Riot
        tope = ((((ESTADO.get("rendimiento") or {}).get("vistas") or {}).get("regla_hoy")) or {}).get("tope", 2)
        s = {"fin": {**e[1], "texto": companion.linea_fin(e[1], tope)}}
        threading.Thread(target=ping, daemon=True).start()
    elif tipo == "post_espera": s = {"espera": e[1]}
    elif tipo == "revision":
        s = {"revision": e[1], "fin": None, "espera": None, "perfil": gui.perfil(ESTADO["rango"], ESTADO["cuenta"])}
        USADO.add("revision"); threading.Thread(target=refrescar, daemon=True).start(); threading.Thread(target=ping, daemon=True).start()
    elif tipo == "rango": s = {"rango": e[1] or ESTADO["rango"]}; s["perfil"] = gui.perfil(s["rango"], ESTADO["cuenta"])
    elif tipo == "cuenta":  # la cuenta con sesión en el cliente: manda sobre perfil.json (un amigo, u otra cuenta en tu PC)
        gui.CUENTA[0] = e[1]
        if gui.usar_cuenta(e[1], e[3] if len(e) > 3 else None):  # otra cuenta: su propia carpeta; se bajan sus últimas 20 del cliente
            s.update(descarga=None, previa=None, ultima=None, rendimiento=None)
            if not any(gui.RAW.glob("*_*.json")): threading.Thread(target=descargar_todo, daemon=True).start()
        s.update(cuenta=e[1], perfil=gui.perfil(ESTADO["rango"], e[1]), icono=e[2] if len(e) > 2 else None)
        threading.Thread(target=refrescar, daemon=True).start()  # si el historial en disco es de otra cuenta, se oculta
    elif tipo == "cliente": s = {"cliente": e[1]}
    elif tipo == "region": s = {"region": e[1], **({"plataforma": e[2]} if len(e) > 2 else {})}
    elif tipo == "crono": s = {"crono": e[1]}
    elif tipo == "tablero": s = {"tablero": e[1]}
    elif tipo == "comentario": s = {"comentario": e[1]}
    elif tipo == "aviso":  # F8: los consejos de la partida se guardan todos (el nuevo ya no borra al anterior)
        s = {"aviso": e[1]}
        if e[1].get("tipo") == "consejo":
            if e[1].get("corto") and franja_libre(ESTADO.get("avisos") or [], time.time()):  # F1: a la franja, sin saturarla
                s["aviso"] = {**e[1], "franja": time.time()}
            s["avisos"] = (ESTADO.get("avisos") or []) + [s["aviso"]]
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
            import semanal; r["semana"] = semanal.plan(r["resumen"], r["vistas"])  # «Tu semana» en Perfil
        except Exception: r["vistas"] = None  # sin partidas suficientes draft.py truena al importar: las ventanas dicen «sin datos»
    return r


CACHE = gui.REPO / "datos" / "cache" / "rendimiento.json"


def firma(raw):
    """(n, mtime máx, bytes) de las partidas y timelines, y la fecha de score.py: si cambia algo, la caché ya no vale."""
    fs = [f.stat() for f in pathlib.Path(raw).rglob("*.json")]
    codigo = [(gui.REPO / "scripts" / f).stat().st_mtime_ns if (gui.REPO / "scripts" / f).exists() else 0 for f in ("score.py", "draft.py", "vistas.py", "semanal.py", "postpartida.py")]
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


def aplicar_coach(r, c=None):
    """F12: con una regla de tu coach, ESA es tu regla de hoy (franja y En vivo) y se arma el informe para mandarle.
    Se aplica después de la caché (cambiar de coach no exige recalcular nada). Devuelve r."""
    c = gui.coach() if c is None else c
    V = (r or {}).get("vistas")
    if not c or not isinstance(V, dict): return r
    ps = [p for p in ((r.get("resumen") or {}).get("partidas") or [])[:20] if p.get("muertes14_25") is not None]
    ok = sum(p["muertes14_25"] <= c["tope"] for p in ps)
    V["regla_hoy"] = {"metrica": "muertes", "tope": c["tope"], "coach": True, "texto": f"Regla de tu coach: {c['texto']}",
                      "numero": f"La cumpliste en {ok} de tus últimas {len(ps)} partidas (≤ {c['tope']} muertes del 14 al 25)." if ps else "Aún no hay partidas con este dato.",
                      "ok": ok, "n": len(ps)}
    V["informe_coach"] = "\n".join([f"Racha · informe para tu coach ({time.strftime('%Y-%m-%d')})", f"Regla: {c['texto']} (≤ {c['tope']} muertes del 14 al 25)",
                                     f"Cumplida en {ok} de {len(ps)} partidas", ""] +
                                    [f"{p.get('fecha', '?')} · {p.get('campeon', '?')} vs {p.get('rival') or '?'} · {'victoria' if p.get('win') else 'derrota'} · "
                                     f"muertes 14–25: {p['muertes14_25']} {'cumplida' if p['muertes14_25'] <= c['tope'] else 'fallada'}" for p in ps])
    return r


AJENA = "Esta PC guarda el historial de otra cuenta: para el tuyo, usa Racha en tu PC."


def refrescar():  # lee ~300 JSON (o la caché): en su hilo, para no frenar la cola
    r = None if gui.ajeno(gui.CUENTA[0]) else aplicar_coach(rendimiento_rapido())  # historial de otra cuenta: no mostrarlo como tuyo
    with LOCK:
        if gui.ajeno(gui.CUENTA[0]): r = None; ESTADO["descarga"] = AJENA  # la cuenta pudo llegar mientras se calculaba (hallazgo 20)
        ESTADO.update(rendimiento=r, v=ESTADO["v"] + 1, **({} if r is not None else {"previa": None}))
    vistas_previas(r)  # siempre: «ultima» es la última partida grabada en esta PC, también con cuenta ajena (ronda 4)
    if r is not None and gui.es_base(): tus_builds()  # «Tu build» (datos/meta) es del dueño  # tu build propia relee las timelines: al final (auditoría de rendimiento)
    builds_del_backend(); sync_nube()


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
    nube.sincronizar(None if gui.ajeno(gui.CUENTA[0]) or not gui.es_base() else e.get("rendimiento"), e.get("cuenta"), e.get("plataforma"), e.get("ajustes"))
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
    with LOCK:
        if gui.ajeno(gui.CUENTA[0]): previa = None  # un hilo viejo pudo seguir aquí después de que la cuenta ajena limpió (hallazgo 20)
        ESTADO.update(previa=previa, ultima=ultima, v=ESTADO["v"] + 1)


RELEASES = "https://api.github.com/repos/C0z1/racha.gg/releases/latest"


def version_mayor(a, b):
    """True si la versión a («v0.6.1») es mayor que b («0.6.0»); lo que no se entienda, False."""
    try: return tuple(map(int, a.lstrip("v").split("."))) > tuple(map(int, b.lstrip("v").split(".")))
    except (ValueError, AttributeError): return False


DESCARGAS = "https://github.com/C0z1/racha.gg/releases/download/"
QUIETO = {None, "None", "inicio", "Lobby", "EndOfGame"}  # fases en que se puede cerrar Racha para actualizar
MAX_INSTALADOR = 300 * 2**20  # bytes: el instalador pesa ~30 MB; más que esto no es nuestro


def instalador_de(d):
    """(url, sha256) del instalador del release `d` de GitHub, o None si falta o no viene con su sha256."""
    for a in d.get("assets") or []:
        url, dig = str(a.get("browser_download_url", "")), str(a.get("digest") or "")
        if re.fullmatch(r"Racha-Setup-[\d.]+\.exe", str(a.get("name", ""))) and url.startswith(DESCARGAS) and re.fullmatch(r"sha256:[0-9a-f]{64}", dig):
            return url, dig[7:]
    return None


def bajar_verificado(url, sha, destino):
    """Baja `url` a `destino` y comprueba su sha256; si no cuadra, lo borra y devuelve False (nunca se instala)."""
    import hashlib
    h, n = hashlib.sha256(), 0
    tmp = destino.with_suffix(".part")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "racha"}), timeout=60) as r, open(tmp, "wb") as f:
            while b := r.read(1 << 16):
                n += len(b)
                if n > MAX_INSTALADOR: raise OSError("demasiado grande")
                h.update(b); f.write(b)
        if h.hexdigest() != sha: raise OSError("sha256 distinto")
        os.replace(tmp, destino); return True
    except OSError:
        try: tmp.unlink()
        except OSError: pass
        return False


def actualizar(version, url, sha, espera=30):
    """Auto-actualización (solo en la versión instalada): baja el instalador, verifica su sha256, espera a que no estés
    en selección ni en partida y lo corre en silencio; el instalador cierra Racha y la vuelve a abrir."""
    import tempfile
    destino = pathlib.Path(tempfile.gettempdir()) / f"Racha-Setup-{version.lstrip('v')}.exe"
    if not bajar_verificado(url, sha, destino):
        with LOCK: ESTADO["nueva"] = {**(ESTADO["nueva"] or {}), "estado": "No se pudo verificar la descarga: actualiza a mano."}; ESTADO["v"] += 1
        return
    with LOCK: ESTADO["nueva"] = {**(ESTADO["nueva"] or {}), "estado": "Lista: se instala sola cuando no estés en partida."}; ESTADO["v"] += 1
    while True:
        with LOCK: fase = ESTADO.get("fase")
        if fase in QUIETO: break
        time.sleep(espera)
    subprocess.Popen([str(destino), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/RACHA=" + ("--fondo" if FONDO[0] and not ventana.viva() else "")])  # con ventana abierta, vuelve con ventana


ACTUALIZANDO = threading.Lock()  # una sola búsqueda/descarga/instalación a la vez (al arrancar, cada 30 min o con el botón)
BUSCAR_CADA = 1800  # s: una versión publicada aparece sin reiniciar Racha


def vigilar_version(cada=BUSCAR_CADA):
    """Busca versión nueva al arrancar y cada `cada` s (pedido del usuario, 2026-11-13: que no tengan que instalar a mano)."""
    while True:
        buscar_version(); time.sleep(cada)


def buscar_version():
    """¿Hay una versión de Racha más nueva en GitHub Releases? Avisa y, en la versión instalada, la baja y la instala sola
    cuando no estés en selección ni en partida. Si ya hay una en curso, no hace nada."""
    if not ACTUALIZANDO.acquire(blocking=False): return
    try:
        _buscar_version()
        with LOCK:
            if not (ESTADO.get("nueva") or {}).get("version"): ESTADO.update(nueva=None, al_dia=time.time(), v=ESTADO["v"] + 1)  # no hay nueva: «Al día»
    finally: ACTUALIZANDO.release()


def _buscar_version():
    try:
        req = urllib.request.Request(RELEASES, headers={"User-Agent": "racha", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r: d = json.load(r)
    except (OSError, ValueError): return
    if not (version_mayor(d.get("tag_name", ""), VERSION) and str(d.get("html_url", "")).startswith("https://github.com/")): return
    inst = instalador_de(d) if getattr(sys, "frozen", False) else None  # desde el código fuente solo se avisa
    with LOCK: ESTADO.update(nueva={"version": d["tag_name"], "url": d["html_url"], "estado": "Bajando la actualización…" if inst else None}, v=ESTADO["v"] + 1)
    if inst: actualizar(d["tag_name"], *inst)


MOVER_S = 90  # el modo mover se apaga solo: una franja que capta clics no puede quedarse así por olvido (DeepSeek)


def apagar_mover(desde):
    with LOCK:
        if ESTADO.get("mover_franja") == desde: ESTADO.update(mover_franja=False, v=ESTADO["v"] + 1)


def guardar_franja(clave, v):
    """La franja guarda su posición al soltarla (modo mover): como un ajuste más, también en la nube."""
    try: a = gui.guardar_ajuste(clave, v)
    except (ValueError, OSError): return
    with LOCK: ESTADO.update(ajustes=a, v=ESTADO["v"] + 1)


def al_dia():
    """Al conectar el cliente: baja de él las partidas que falten en la carpeta de la cuenta activa (sin key; las que ya
    están se saltan). Si entró alguna, recalcula todo."""
    try:
        import cliente_v5
        with DESCARGANDO:
            nuevas, _ = cliente_v5.descargar()
        if nuevas: refrescar()
    except Exception: pass


def primera_vez():
    """Alguien sin partidas: su historial se baja solo al abrir Racha con LoL abierto (con invitación, hasta 100 por el
    servidor; sin ella, las últimas 20 desde su cliente)."""
    import os
    raw = pathlib.Path(os.environ.get("DATOS_DIR") or gui.REPO / "datos" / "raw")
    if any(raw.glob("*_*.json")): return  # sin invitación también: se bajan las del cliente (descargar_todo)
    if not (companion.lcu("/lol-summoner/v1/current-summoner") or {}).get("gameName"): return  # sin cliente: se reintenta al abrir LoL
    descargar_todo()


DESCARGANDO = threading.Lock()


def rango_api(puuid, region):
    """Tu solo/dúo de la Riot API (league-v4 por el backend) en el formato de companion.rango; None sin dato."""
    import re
    if not puuid or not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", str(puuid)): return None
    try: es = companion.backend("GET", f"/v1/riot/{region}/lol/league/v4/entries/by-puuid/{puuid}", base=gui.REPO) or []
    except Exception: return None
    return companion.rango({"queues": [{"queueType": e.get("queueType"), "tier": e.get("tier"), "division": e.get("rank"),
                                        "leaguePoints": e.get("leaguePoints"), "wins": e.get("wins"), "losses": e.get("losses")}
                                       for e in es if isinstance(e, dict)]})


def buscar_cuenta(riot_id, region):
    """Comprueba que el Riot ID existe (Riot API por el backend, o con tu key) y lo guarda; luego baja sus partidas.
    Es el «inicio de sesión» posible hoy: el oficial de Riot (RSO) solo se da a apps con production key aprobada."""
    import urllib.error, urllib.parse
    try: c = gui.validar_cuenta(riot_id, region)  # se guarda solo si existe: un TAG mal escrito no borra tu cuenta buena
    except ValueError: return False, "Escribe tu Riot ID como Nombre#TAG y elige tu región."
    nombre, _, tag = c["riot_id"].rpartition("#")
    ruta = "asia" if gui.RUTAS[c["region"]] == "sea" else gui.RUTAS[c["region"]]
    q = urllib.parse.quote
    try:
        r = companion.backend("GET", f"/v1/riot/{ruta}/riot/account/v1/accounts/by-riot-id/{q(nombre, safe='')}/{q(tag, safe='')}", base=gui.REPO)
    except urllib.error.HTTPError as e:
        if e.code == 404: return False, f"No existe la cuenta {c['riot_id']} en esa región."
        r = None
    except OSError: r = None
    gui.guardar_cuenta(c["riot_id"], c["region"])
    rango = rango_api(r.get("puuid"), c["region"]) if isinstance(r, dict) else None  # tu rango ya, sin esperar la descarga
    with LOCK:
        cuenta = ESTADO.get("cuenta") or c["riot_id"]
        ESTADO.update(cuenta=cuenta, **({"rango": rango, "perfil": gui.perfil(rango, cuenta)} if rango else {}), v=ESTADO["v"] + 1)
    threading.Thread(target=descargar_todo, daemon=True).start()
    hallada = r and r.get("gameName")
    return True, (f"Encontrada: {r['gameName']}#{r.get('tagLine', tag)}. Bajando tus partidas…" if hallada
                  else f"Guardada: {c['riot_id']}. Bajando tus partidas…")


def descargar_todo(n=100):
    """Baja tus últimas n partidas (descargar.py, con tu key o tu código) y recalcula todo; el avance va a «descarga»."""
    if not DESCARGANDO.acquire(blocking=False):  # ya hay una en curso
        with LOCK: ESTADO.update(descarga="Ya se están bajando tus partidas…", v=ESTADO["v"] + 1)
        return
    try:
        def aviso(t):
            with LOCK: ESTADO.update(descarga=t, v=ESTADO["v"] + 1)
        if not gui.puede_descargar() or not gui.es_base():  # sin invitación ni key (u otra cuenta: la key baja la del dueño): las últimas 20 del cliente
            import cliente_v5
            aviso("Bajando tus últimas 20 partidas desde tu cliente de LoL…")
            nuevas, msg = cliente_v5.descargar()
            aviso(msg + (" Con una invitación o tu propia key se bajan hasta 100." if nuevas or "ya estaban" in msg else ""))
            if nuevas: refrescar()
            return
        if gui.ajeno(gui.CUENTA[0]):  # el historial de esta PC es de otra cuenta: bajarlo pisaría su perfil.json
            return aviso(AJENA)
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


BAJADA = [0.0]  # cuándo se bajaron por última vez las builds del backend
USADO, PING = set(), [None]  # qué partes de Racha se usaron hoy · día del último ping


def builds_del_backend(cada=3600):
    """A lo más una vez por hora: las builds de los onetricks del top que subió el admin (sin key) y si eres admin
    (para mostrar «Invitar amigos» en Ajustes). Un fallo no tumba nada."""
    import builds
    if time.time() - BAJADA[0] < cada: return
    BAJADA[0] = time.time()
    try: builds.bajar()
    except Exception: pass
    try: admin = companion.backend("GET", "/v1/admin/invitados", base=gui.REPO)
    except Exception: admin = None  # 403 = no eres admin; sin red, igual
    try: grupo = companion.backend("GET", "/v1/grupo", base=gui.REPO)
    except Exception: grupo = None
    with LOCK: ESTADO.update(admin=admin, grupo=grupo if isinstance(grupo, list) else None, v=ESTADO["v"] + 1)


def ping():
    """Métricas anónimas (solo si las prendiste en Ajustes): una vez al día, al terminar una partida, qué partes usaste.
    Sin Riot ID, sin correo y sin código: el backend solo suma contadores por día, versión y región."""
    hoy = time.strftime("%Y-%m-%d")
    if not gui.ajustes().get("metricas") or PING[0] == hoy: return
    with LOCK: region = ESTADO.get("plataforma")
    with LOCK: avisos = sum(1 for a in ESTADO.get("avisos") or [] if a.get("franja"))  # F5: cuántos salieron en la franja en la última partida
    with LOCK: resp = dict(SIRVIO)  # respuestas a «¿te sirvieron los avisos?» desde el último ping
    try: companion.backend("POST", "/v1/ping", {"version": VERSION, "region": region or "?", "avisos": avisos, **{f"sirvio_{k}": v for k, v in resp.items()},
                                                **{k: k in USADO for k in ("overlay", "champ_select", "revision")}}, gui.REPO)
    except Exception: return
    PING[0] = hoy; USADO.clear()
    with LOCK:
        for k, v in resp.items(): SIRVIO[k] -= v  # lo que se contestó mientras salía el ping queda para el siguiente


def reportar(texto, vista):
    """Manda tu reporte privado (lo lee solo quien administra Racha) con la versión, la pantalla, la fase y el último aviso."""
    with LOCK: fase, aviso = ESTADO.get("fase"), ESTADO.get("descarga")
    cuerpo = {"texto": (texto.strip() + (f"\n\nÚltimo aviso en pantalla: {aviso}" if aviso else ""))[:4000], "version": VERSION, "vista": vista, "fase": fase}
    import urllib.error
    try: ok = companion.backend("POST", "/v1/reporte", cuerpo, gui.REPO) is not None
    except urllib.error.HTTPError as e: ok = "limite" if e.code == 429 else False
    except Exception: ok = False
    msg = ("Gracias: tu reporte llegó." if ok is True else "Ya mandaste varios reportes hoy: mañana puedes mandar más, o abre un issue en GitHub."
           if ok == "limite" else "No se pudo mandar (¿sin internet o sin código/sesión?). Puedes abrir un issue en GitHub.")
    with LOCK: ESTADO.update(reporte=msg, v=ESTADO["v"] + 1)


def invitar(nombre, email):
    """Admin: crea el código de un amigo (y permite su correo de Google). El código solo se muestra esta vez."""
    import urllib.error
    try: r = companion.backend("POST", "/v1/admin/invitados", {"nombre": nombre, "email": email or None}, gui.REPO); err = None
    except urllib.error.HTTPError as e:
        r, err = None, {400: "Nombre o correo inválidos.", 403: "Solo quien administra Racha puede invitar.", 409: "Ya invitaste a alguien con ese nombre."}.get(e.code, f"El servidor respondió {e.code}.")
    except Exception: r, err = None, "Sin conexión con el servidor."
    BAJADA[0] = 0  # la lista de invitados se vuelve a pedir
    with LOCK: ESTADO.update(invitacion=r or {"error": err}, v=ESTADO["v"] + 1)
    builds_del_backend()


def vigilar_cuenta(q, cada=10):
    """Cada `cada` s lee la cuenta con sesión en el cliente (solo lectura); al cambiar, manda su rango y su «gameName#tag»."""
    ultima, vuelta, m = None, 0, None
    while True:
        s = companion.lcu("/lol-summoner/v1/current-summoner") or {}
        nueva = s.get("gameName") and (c := f"{s['gameName']}#{s.get('tagLine', '')}") != ultima
        if nueva:
            ultima = c; q.put(("rango", companion.rango(companion.lcu("/lol-ranked/v1/current-ranked-stats"))))
            q.put(("cuenta", c, s.get("profileIconId"), s.get("puuid")))
            if ESTADO.get("conectado"): threading.Thread(target=primera_vez, daemon=True).start()  # LoL recién abierto
            threading.Thread(target=al_dia, daemon=True).start()  # las que se jugaron con Racha cerrada o sin guardar
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
        self.send_header("Content-Security-Policy", "default-src 'none'; img-src 'self' data:; font-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'")
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
                with LOCK: ESTADO.update(nube=nube_publica(), ajustes=gui.ajustes(), v=ESTADO["v"] + 1)  # ajustes: los restaurados de la nube
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
        if self.path == "/api/actualizar":  # botón «Actualizar» (arriba a la derecha): busca, baja e instala ya (o al salir de partida)
            with LOCK: ESTADO["nueva"] = {**(ESTADO.get("nueva") or {}), "estado": "Buscando la versión nueva…"}; ESTADO["v"] += 1
            threading.Thread(target=buscar_version, daemon=True).start(); return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/abrir":  # un segundo arranque del .exe: la ventana la abre (o trae al frente) este proceso
            abrir(URL[0]); return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/descargar":  # «Descargar mis partidas»: con tu key o tu código de acceso, en su hilo
            threading.Thread(target=descargar_todo, daemon=True).start(); return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/acceso":
            try: gui.guardar_acceso(json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 200)))["token"])
            except (ValueError, KeyError, TypeError, OSError): return self.enviar(400, b"", "text/plain")
            with LOCK: ESTADO.update(descarga="Código guardado. Ya puedes descargar tus partidas.", conectado=True, v=ESTADO["v"] + 1)
            threading.Thread(target=primera_vez, daemon=True).start()  # con el cliente abierto, empieza a bajar sola
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/coach":  # F12: crear un código (si eres coach), usar uno (alumno) o quitarlo
            try: d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 1000))); acc = d.get("accion")
            except (ValueError, TypeError, AttributeError): return self.enviar(400, b"", "text/plain")
            try:
                if acc == "crear": res = {"codigo": gui.codigo_coach(d.get("texto"), int(d.get("tope")))}
                elif acc == "usar": res = {"regla": gui.guardar_coach(d.get("codigo"))}
                elif acc == "quitar": gui.COACH_F.unlink(missing_ok=True); res = {}
                else: return self.enviar(400, b"", "text/plain")
            except (ValueError, TypeError): return self.enviar(400, json.dumps({"error": "Revisa el código o la regla."}).encode(), "application/json")
            if acc != "crear":
                with LOCK: ESTADO.update(coach=gui.coach(), v=ESTADO["v"] + 1)
                threading.Thread(target=refrescar, daemon=True).start()
            return self.enviar(200, json.dumps(res, ensure_ascii=False).encode(), "application/json")
        if self.path == "/api/sirvio":  # una respuesta por partida: sí / no / no los vi
            try: v = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 100))).get("valor")
            except (ValueError, TypeError, AttributeError): v = None
            if v not in SIRVIO: return self.enviar(400, b"", "text/plain")
            with LOCK:
                if (ESTADO.get("fin") or {}).get("sirvio"): return self.enviar(409, b"", "text/plain")
                SIRVIO[v] += 1; ESTADO.update(fin={**(ESTADO.get("fin") or {}), "sirvio": v}, v=ESTADO["v"] + 1)
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/cuenta":  # tu Riot ID y región, para usar Racha sin el cliente de LoL abierto
            try: d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 300)))
            except (ValueError, TypeError): return self.enviar(400, b"", "text/plain")
            ok, msg = buscar_cuenta(str(d.get("riot_id") or ""), str(d.get("region") or ""))
            return self.enviar(200 if ok else 409, json.dumps({"ok": ok, "mensaje": msg}).encode(), "application/json")
        if self.path == "/api/runas":  # A5: importar la página de runas de la build, solo cuando el jugador pulsa el botón
            import builds
            try:
                d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 300)))
                b = builds.guardado_dict(str(d["champ"]), str(d["pos"])) or {}
                pag = None
                if d.get("rival"):  # la página del matchup (muchas partidas Master+), si hay datos
                    import matchups; pag = (matchups.para_ficha(str(d["champ"]), str(d["pos"]), str(d["rival"])) or {}).get("pagina")
            except (ValueError, KeyError, TypeError): return self.enviar(400, b"", "text/plain")
            ok, msg = companion.importar_runas(str(d["champ"]) + (f" vs {d['rival']}" if pag else ""), pag or b.get("pagina_ids"))
            return self.enviar(200 if ok else 409, json.dumps({"ok": ok, "mensaje": msg}).encode(), "application/json")
        if self.path in ("/api/reporte", "/api/invitar"):
            try:
                d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 6000)))
                a, b = str(d.get("texto") or d.get("nombre") or "").strip(), str(d.get("vista") or d.get("email") or "").strip()
            except (ValueError, TypeError, AttributeError): return self.enviar(400, b"", "text/plain")
            if not a: return self.enviar(400, b"", "text/plain")
            threading.Thread(target=reportar if self.path == "/api/reporte" else invitar, args=(a, b), daemon=True).start()
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/recargar":  # Ajustes_Vino «Recargar»: vuelve a leer tus partidas del disco, con aviso
            def recargar():
                with LOCK: ESTADO.update(descarga="Recalculando tus estadísticas…", v=ESTADO["v"] + 1)
                refrescar()
                with LOCK: ESTADO.update(descarga="Listo: tus estadísticas están al día.", v=ESTADO["v"] + 1)
            threading.Thread(target=recargar, daemon=True).start(); return self.enviar(200, b"{}", "application/json")
        if self.path not in ("/api/autoarranque", "/api/ajuste", "/api/mover_franja"): return self.enviar(404, b"", "text/plain")
        try: d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 200))); on = d["on"]
        except (ValueError, KeyError, TypeError): return self.enviar(400, b"", "text/plain")
        if self.path in ("/api/autoarranque", "/api/mover_franja") and not isinstance(on, bool): return self.enviar(400, b"", "text/plain")
        if self.path == "/api/mover_franja":  # Ajustes > Mover la franja: se muestra y se puede arrastrar; se guarda sola al soltar
            with LOCK: ESTADO.update(mover_franja=time.time() if on else False, v=ESTADO["v"] + 1)
            if on: threading.Timer(MOVER_S, apagar_mover, args=(ESTADO["mover_franja"],)).start()
            return self.enviar(200, b"{}", "application/json")
        if self.path == "/api/ajuste":  # guardar_ajuste valida cada clave (booleano, o la lista blanca de franja_pos)
            try: a = gui.guardar_ajuste(d.get("clave"), on)
            except (ValueError, OSError): return self.enviar(400, b"", "text/plain")
            with LOCK: ESTADO.update(ajustes=a, v=ESTADO["v"] + 1)
            def subir(clave=d.get("clave")):  # tus ajustes también van a la nube; la tabla del grupo se pide de nuevo al cambiarla
                sync_nube()
                if clave == "grupo": BAJADA[0] = 0; builds_del_backend()
            threading.Thread(target=subir, daemon=True).start()
            return self.enviar(200, json.dumps(a).encode(), "application/json")
        a = autoarranque(on)
        with LOCK: ESTADO.update(autoarranque=a, v=ESTADO["v"] + 1)
        self.enviar(200, json.dumps({"on": a}).encode(), "application/json")


def abrir(url):
    """La ventana de Racha (ventana.py: Edge --app con perfil propio en datos/edge); sin Edge, el navegador."""
    if not ventana.abrir(url, gui.REPO / "datos" / "edge"): webbrowser.open(url)


def pedir_abrir(url):
    """Pide al Racha que ya corre que abra su ventana (él es el dueño del proceso de Edge)."""
    try: urllib.request.urlopen(urllib.request.Request(url + "api/abrir", b"{}", {"X-HTC": "1", "Content-Type": "application/json"}), timeout=5)
    except OSError: pass


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


class Servidor(http.server.ThreadingHTTPServer):
    allow_reuse_address = False  # en Windows SO_REUSEADDR deja tomar un puerto que otro programa está usando


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    unico = not ({"--demo", "--no-abrir"} & set(argv))  # las pruebas y la demo no tocan al HTC real
    if unico and (url := otro_htc()):
        if "--fondo" not in argv: pedir_abrir(url)
        return
    if unico and ventana.limpiar_viejas() and "--fondo" in argv: argv = [a for a in argv if a != "--fondo"]  # venía de 0.14–0.16 con ventana: se reabre
    srv = None
    if unico:  # el puerto de la vez anterior: una ventana que quedó abierta (actualización, reinicio) se reconecta sola
        try: srv = Servidor(("127.0.0.1", int(PUERTO.read_text())), H)
        except (OSError, ValueError): pass
    srv = srv or Servidor(("127.0.0.1", 0), H); url = f"http://127.0.0.1:{srv.server_port}/"
    # la versión instalada sigue en segundo plano al cerrar la ventana: si no, en partida no había franja (lo vio el usuario,
    # 2026-11-12: cerró la ventana en champ select y Racha se apagó). Desde el código, cerrar la ventana sigue cerrando todo.
    URL[0], FONDO[0] = url, "--fondo" in argv or (getattr(sys, "frozen", False) and unico)
    if "--fondo" in argv: VIVO[0] = 0  # aún no hay ventana: si el cliente ya está abierto, la primera fase la abre
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
        threading.Thread(target=vigilar_version, daemon=True).start(); threading.Thread(target=primera_vez, daemon=True).start()
    threading.Thread(target=demo if "--demo" in argv else gui.trabajador, args=(q,), daemon=True).start()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(url, flush=True)
    if "--fondo" not in argv and "--no-abrir" not in argv: abrir(url)
    seguir = lambda: FONDO[0] or time.time() - VIVO[0] < 60  # la ventana pregunta cada 2 s: si se cerró (y no es --fondo), salimos
    if "--overlay" in argv or not ({"--demo", "--no-abrir", "--sin-overlay"} & set(argv)):
        def leer():
            with LOCK: return dict(ESTADO)
        def registrar(txt):  # D7: si la franja truena, que quede rastro (datos/salud/franja.log)
            try:
                f = gui.REPO / "datos" / "salud" / "franja.log"; f.parent.mkdir(parents=True, exist_ok=True)
                with f.open("a", encoding="utf-8") as h: h.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {txt}\n")
            except OSError: pass
        try: import overlay; overlay.correr(leer, seguir, registrar=registrar, icono=imagen, guardar=guardar_franja)  # franja en partida; ocupa el hilo principal (tkinter)
        except Exception as e: registrar(f"sin franja: {e!r}")  # sin tkinter o sin pantalla: HTC sigue sin overlay
    while seguir(): time.sleep(2)
    ventana.cerrar(); srv.shutdown()


if __name__ == "__main__":
    main()
