"""Chequeo de salud de Racha (plan En vivo, .equipo/PLAN-ENVIVO.md): mide, registra y nunca arregla solo.
  python scripts/salud.py                 una pasada; sale con 1 si hay FALLA
  python scripts/salud.py --cada 60       en bucle (60 s en partida; fuera de partida, cada 300 s)
  python scripts/salud.py --vistas        además abre las 9 vistas en Edge sin ventana (S10)
  python scripts/salud.py --foto          en FALLA, guarda una captura del monitor del juego
Log: datos/salud/salud.jsonl (una línea por pasada) y datos/salud/fallo-<ts>.json en cada FALLA."""
import json, os, pathlib, subprocess, sys, time, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import companion

REPO = pathlib.Path(__file__).resolve().parent.parent
SALUD = REPO / "datos" / "salud"  # el log va al repo aunque se mida la app instalada
APPS = (REPO, pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "HTC")  # Racha desde el código o el .exe instalado
VISTAS = ("inicio", "draft", "companion", "envivo", "perfil", "partidas", "campeones", "errores", "ajustes")
ZONAS = {"minimapa": (0.80, 0.70, 1, 1), "marcador": (0.78, 0, 1, 0.06), "hud": (0.28, 0.85, 0.72, 1), "chat": (0, 0.60, 0.25, 1)}  # (x0, y0, x1, y1) en fracciones del juego
ARRANQUE = 180  # s tras abrir Racha en que la CPU alta es el precálculo de tus partidas (AVISO, no FALLA)
PRIVADO = ("rendimiento", "cuenta", "nube", "grupo", "coach", "invitacion")  # nunca al log


# ---------- evaluar (pura) ----------

def evaluar(d, ahora):
    """d: lo que midieron los recolectores. Devuelve [{id, nivel, medido, umbral, detalle}] con nivel OK, AVISO o FALLA."""
    r, e = [], d.get("estado") or {}
    def res(i, nivel, medido=None, umbral=None, detalle=""): r.append(dict(id=i, nivel=nivel, medido=medido, umbral=umbral, detalle=detalle))
    s = e.get("json")
    if e.get("codigo") != 200 or not isinstance(s, dict): res("S1", "FALLA", e.get("codigo"), 200, e.get("error") or "sin respuesta del servidor"); return r
    falta = [k for k in ("fase", "meta", "ajustes", "v") if k not in s]
    lento, pesado = (e.get("ms") or 0) > 1000, (e.get("bytes") or 0) > 200_000
    res("S1", "FALLA" if falta or lento or pesado else "OK", {"ms": e.get("ms"), "kb": round((e.get("bytes") or 0) / 1024, 1)},
        {"ms": 1000, "kb": 200}, f"faltan {falta}" if falta else "")
    fase, lcu = s.get("fase"), d.get("fase_lcu", "?")
    if lcu != "?":
        res("S2", "OK" if fase == lcu else "FALLA", fase, lcu, "" if fase == lcu else "Racha y el cliente no coinciden")
    v = d.get("vivo")  # [gameTime, gameTime 2 s después] o None
    # con el cliente cerrado (lcu None) solo se juega si el juego responde: si no, LoL está cerrado del todo
    jugando = lcu == "InProgress" or (lcu in (None, "?") and fase in (None, "InProgress") and bool(v) and v[0] is not None)
    if jugando:
        if not v or v[0] is None: res("S3", "AVISO" if d.get("cargando") else "FALLA", None, "2999 responde", "la Live API no responde")
        elif v[1] is not None and v[1] <= v[0] and v[0] > 0: res("S3", "FALLA", v, "gameTime avanza", "el reloj del juego no avanza (¿pausa o juego colgado?)")
        else: res("S3", "OK", v)
        m = s.get("meta") or {}
        edad = ahora - m["recibido"] if m.get("recibido") else None
        if v and v[0] and v[0] > 30:  # S4: con el juego respondiendo, la foto de Racha debe estar al día
            res("S4", "FALLA" if edad is None or edad > 25 else "OK", None if edad is None else round(edad, 1), 25, "Racha no recibe fotos nuevas" if edad is None or edad > 25 else "")
    f, juego = d.get("franja"), d.get("juego")  # ventanas: {rect, visible, topmost, transparente, noactivate, sobre_juego, colgada}
    debe = d.get("franja_debe")
    if jugando and debe:
        if not f or not f.get("visible"): res("S5", "FALLA", None, "franja visible", "la franja debería verse y no está")
        else:
            malo = [k for k in ("topmost", "transparente", "noactivate") if not f.get(k)] + (["colgada"] if f.get("colgada") else [])
            if juego and not f.get("sobre_juego"): malo.append("debajo del juego")
            if juego:
                gx0, gy0, gx1, gy1 = juego; gw, gh = gx1 - gx0, gy1 - gy0; x0, y0, x1, y1 = f["rect"]
                if f.get("monitor") != d.get("monitor_juego"): malo.append("otro monitor")
                if x0 < gx0 or y0 < gy0 or x1 > gx1 or y1 > gy1: malo.append("se sale del juego")
                if gw and (x1 - x0) / gw > 0.60: malo.append(f"ancho {round((x1 - x0) / gw * 100)} %")
                if gh and (y1 - y0) / gh > 0.11: malo.append(f"alto {round((y1 - y0) / gh * 100)} %")
                fx0, fy0, fx1, fy1 = ((x0 - gx0) / gw, (y0 - gy0) / gh, (x1 - gx0) / gw, (y1 - gy0) / gh) if gw and gh else (0, 0, 0, 0)
                malo += [f"pisa {z}" for z, (a, b, c, e2) in ZONAS.items() if fx0 < c and fx1 > a and fy0 < e2 and fy1 > b]
            res("S5", "FALLA" if malo else "OK", f.get("rect"), "encima, dentro del juego, sin zonas prohibidas", ", ".join(malo))
    else:  # fuera de partida, o en partida sin nada que mostrar (foto vieja, overlay apagado): la franja no debe verse
        res("S6", "FALLA" if f and f.get("visible") else "OK", bool(f and f.get("visible")), False, "franja visible sin nada que mostrar (fuera de partida o con la foto vieja)" if f and f.get("visible") else "")
    if d.get("pantalla_completa") is not None:
        pc = d["pantalla_completa"]
        res("S7", "FALLA" if bool(s.get("pantalla_completa")) != pc and fase in ("ChampSelect", "InProgress") else "AVISO" if pc and jugando else "OK",
            pc, False, "LoL en pantalla completa: la franja no se ve" if pc else "")
    if (c := d.get("cpu")) is not None:
        viejo = lambda k: (10 ** 6 if d.get(k) is None else d[k]) >= ARRANQUE  # al arrancar precalcula: esperado; sin dato cuenta como viejo
        alto = c > 1.0 and (d.get("cpu_antes") or 0) > 1.0 and viejo("edad_proceso") and viejo("edad_antes")  # hallazgo 19: la anterior también, pasado el arranque
        res("S8", "FALLA" if alto or (d.get("rss_mb") or 0) > 200 else "AVISO" if c > 1.0 else "OK", {"cpu": round(c, 2), "rss_mb": d.get("rss_mb")}, {"cpu": 1.0, "rss_mb": 200})
    if jugando and v and v[0] and v[0] > 60 and (g := d.get("grabacion")) is not None:  # S9: [edad del .jsonl más nuevo, archivos nuevos en esta partida]
        res("S9", "FALLA" if g[0] is None or g[0] > 45 or g[1] > 1 else "OK", g, [45, 1], "" if g[0] is not None and g[0] <= 45 and g[1] <= 1 else "la grabación se atrasó o se partió")
    for nombre, (ok, ms, txt) in (d.get("vistas") or {}).items():
        res("S10", "OK" if ok else "FALLA", {"vista": nombre, "ms": ms}, {"ms": 8000}, txt)
    return r


def resumen(res):
    return "FALLA" if any(x["nivel"] == "FALLA" for x in res) else "AVISO" if any(x["nivel"] == "AVISO" for x in res) else "OK"


# ---------- recolectores (E/S) ----------

def puerto():
    """(puerto, carpeta de la app) del Racha que responde; el htc.port de una sesión vieja no cuenta."""
    for app in APPS:
        try: p = int((app / "datos" / "cache" / "htc.port").read_text().strip())
        except (OSError, ValueError): continue
        if leer_estado(p).get("codigo") == 200: return p, app
    return None, REPO


def leer_estado(p):
    if not p: return {"codigo": None, "error": "sin datos/cache/htc.port: Racha no está corriendo"}
    t = time.time()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/estado", timeout=1) as r: b = r.read(); c = r.status
        return {"codigo": c, "json": json.loads(b), "bytes": len(b), "ms": round((time.time() - t) * 1000)}
    except Exception as e: return {"codigo": None, "error": repr(e)[:200]}


def game_time():
    try:
        with urllib.request.urlopen("https://127.0.0.1:2999/liveclientdata/gamestats", context=companion.SSL, timeout=2) as r: return json.load(r).get("gameTime")
    except Exception: return None


def ventanas():
    """{'franja': {...} | None, 'juego': rect | None, 'monitor_juego': id} por Win32 (solo Windows)."""
    try:
        import ctypes, ctypes.wintypes as w
        u = ctypes.windll.user32
        try: ctypes.windll.shcore.SetProcessDpiAwareness(2)  # píxeles reales, como los ve el juego
        except OSError: pass
    except (AttributeError, OSError): return {}
    orden, out = [], {}
    @ctypes.WINFUNCTYPE(ctypes.c_bool, w.HWND, w.LPARAM)
    def cb(h, _):
        cls, t = ctypes.create_unicode_buffer(64), ctypes.create_unicode_buffer(64)
        u.GetClassNameW(h, cls, 64); u.GetWindowTextW(h, t, 64)
        if t.value == "Racha franja" or cls.value == "RiotWindowClass": orden.append((h, cls.value, t.value))
        return True
    u.EnumWindows(cb, 0)  # de arriba hacia abajo en el orden Z
    rect = lambda h: (lambda r: (u.GetWindowRect(h, ctypes.byref(r)), (r.left, r.top, r.right, r.bottom))[1])(w.RECT())
    monitor = lambda h: u.MonitorFromWindow(h, 2)
    juego = next(((i, h) for i, (h, c, _) in enumerate(orden) if c == "RiotWindowClass" and u.IsWindowVisible(h)), None)
    for i, (h, c, t) in enumerate(orden):
        if t == "Racha franja":
            ex = u.GetWindowLongW(h, -20)
            out["franja"] = dict(rect=rect(h), visible=bool(u.IsWindowVisible(h)), topmost=bool(ex & 0x8), transparente=bool(ex & 0x20),
                                 noactivate=bool(ex & 0x08000000), colgada=bool(u.IsHungAppWindow(h)), sobre_juego=juego is None or i < juego[0],
                                 monitor=monitor(h))
    if juego: out["juego"] = rect(juego[1]); out["monitor_juego"] = monitor(juego[1])
    return out


def dueño(p):
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-NetTCPConnection -LocalPort {p} -State Listen).OwningProcess"],
                           capture_output=True, text=True, timeout=10)
        return int(r.stdout.split()[0])
    except Exception: return None


def cpu_rss(pid, ventana=10):
    """(% de un núcleo en `ventana` s, memoria en MB, segundos desde que arrancó) del proceso pid (Windows)."""
    try:
        import ctypes, ctypes.wintypes as w
        k = ctypes.windll.kernel32; h = k.OpenProcess(0x1000 | 0x0010, False, pid)  # QUERY_LIMITED_INFORMATION | VM_READ
        if not h: return None, None, None
        nacio = [0]
        def tiempos():
            a, b, c, e = (w.FILETIME() for _ in range(4)); k.GetProcessTimes(h, ctypes.byref(a), ctypes.byref(b), ctypes.byref(c), ctypes.byref(e))
            nacio[0] = (a.dwHighDateTime << 32 | a.dwLowDateTime) / 1e7 - 11644473600  # FILETIME (1601) a época Unix
            return sum((x.dwHighDateTime << 32 | x.dwLowDateTime) / 1e7 for x in (c, e))
        t0, c0 = time.time(), tiempos(); time.sleep(ventana); t1, c1 = time.time(), tiempos()
        class PMC(ctypes.Structure): _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD)] + [(n, ctypes.c_size_t) for n in ("Peak", "WorkingSetSize", "a", "b", "c", "d", "e", "f")]
        m = PMC(); m.cb = ctypes.sizeof(m); ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb); k.CloseHandle(h)
        return (c1 - c0) / (t1 - t0) * 100, round(m.WorkingSetSize / 2**20), round(time.time() - nacio[0])
    except Exception: return None, None, None


def grabacion(desde, vivo):
    fs = sorted(vivo.glob("*.jsonl"), key=lambda f: f.stat().st_mtime) if vivo.exists() else []
    if not fs: return [None, 0]
    return [round(time.time() - fs[-1].stat().st_mtime), sum(1 for f in fs if f.stat().st_ctime >= desde)]


def edge():
    for p in (os.environ.get("ProgramFiles(x86)", ""), os.environ.get("ProgramFiles", "")):
        if (f := pathlib.Path(p) / "Microsoft" / "Edge" / "Application" / "msedge.exe").exists(): return str(f)


def vistas(p):
    """S10: cada vista en Edge sin ventana; (ok, ms, detalle)."""
    exe, out = edge(), {}
    if not exe: return {"edge": (False, 0, "no encontré msedge.exe")}
    for v in VISTAS:
        t = time.time()
        try:
            dom = subprocess.run([exe, "--headless=new", "--disable-gpu", "--virtual-time-budget=5000", "--dump-dom", f"http://127.0.0.1:{p}/#{v}"],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20).stdout
        except subprocess.TimeoutExpired: out[v] = (False, 20000, "Edge no respondió en 20 s"); continue
        ms = round((time.time() - t) * 1000)
        import re
        main = re.search(r'<main[^>]*id="main"[^>]*>(.*?)</main>', dom, re.S); texto = re.sub(r"<[^>]+>", " ", main.group(1) if main else "")
        t = " ".join(texto.split())  # solo #main: el <script> de la página también contiene estos textos
        malo = "Esta vista falló" in t and t[:200] or "Sin conexión con el companion" in t and "sin conexión" \
            or len(t) < 50 and f"#main con {len(t)} caracteres" or ms > 8000 and f"{ms} ms"
        out[v] = (not malo, ms, malo or "")
    return out


def foto(rect, ruta):
    x0, y0, x1, y1 = rect
    ps = (f"Add-Type -AssemblyName System.Drawing; $b=New-Object System.Drawing.Bitmap {x1 - x0},{y1 - y0}; "
          f"[System.Drawing.Graphics]::FromImage($b).CopyFromScreen({x0},{y0},0,0,$b.Size); $b.Save('{ruta}')")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=20)


# ---------- una pasada ----------

def pasada(args, mem):
    p, app = puerto(); e = leer_estado(p); s = e.get("json") or {}
    d = {"estado": e, "fase_lcu": companion.lcu("/lol-gameflow/v1/gameflow-phase") if companion.LOCK.exists() else None}
    if isinstance(s, dict) and s.get("fase") != d["fase_lcu"]:  # Racha sondea cada 3 s: un cambio de fase recién ocurrido no es falla
        time.sleep(7); e = leer_estado(p); d["estado"] = e; s = e.get("json") or {}  # se vuelven a leer los dos lados
        d["fase_lcu"] = companion.lcu("/lol-gameflow/v1/gameflow-phase") if companion.LOCK.exists() else None
    jugando = d["fase_lcu"] == "InProgress" or (d["fase_lcu"] is None and s.get("fase") in (None, "InProgress") and game_time() is not None)
    if jugando:
        g1 = game_time(); time.sleep(2); d["vivo"] = [g1, game_time()]
        d["cargando"] = g1 is None and (time.time() - mem.setdefault("partida", time.time())) < 120
        mem.setdefault("partida", time.time())
    else: mem.pop("partida", None)
    d.update(ventanas())
    try:
        import overlay; d["franja_debe"] = overlay.visible(s, time.time()) and bool(overlay.estado(s.get("meta"), time.time(), s.get("ajustes")))
    except Exception: d["franja_debe"] = None
    try: d["pantalla_completa"] = companion.pantalla_completa()
    except Exception: pass
    if p and (pid := mem.get("pid") or dueño(p)):
        mem["pid"] = pid; d["cpu_antes"], d["edad_antes"] = mem.get("cpu"), mem.get("edad"); d["cpu"], d["rss_mb"], d["edad_proceso"] = cpu_rss(pid); mem["cpu"], mem["edad"] = d["cpu"], d["edad_proceso"]
        if d["cpu"] is None: mem.pop("pid", None)  # Racha se reinició: otro proceso, se vuelve a buscar en la próxima pasada
    if jugando: d["grabacion"] = grabacion(mem.get("partida", time.time()) - 60, app / "datos" / "vivo")
    if args.vistas and p and not jugando: d["vistas"] = vistas(p)  # 9 Edge sin ventana: nunca en partida (le quitan FPS al juego)
    res = evaluar(d, time.time())
    for x in res:  # tres fallas seguidas del mismo ID: persistente
        mem[x["id"]] = mem.get(x["id"], 0) + 1 if x["nivel"] == "FALLA" else 0
        if mem[x["id"]] >= 3: x["persistente"] = True
    SALUD.mkdir(parents=True, exist_ok=True); ts = time.strftime("%Y%m%d-%H%M%S")
    linea = {"ts": ts, "resumen": resumen(res), "app": "repo" if app == REPO else "instalada", "fase": s.get("fase"), "fase_lcu": d["fase_lcu"], "res": res}
    with (SALUD / "salud.jsonl").open("a", encoding="utf-8") as h: h.write(json.dumps(linea, ensure_ascii=False) + "\n")
    if linea["resumen"] == "FALLA":
        (SALUD / f"fallo-{ts}.json").write_text(json.dumps({"medido": {k: v for k, v in d.items() if k != "estado"},
            "estado": {k: v for k, v in s.items() if k not in PRIVADO} if isinstance(s, dict) else None, "res": res}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        if args.foto and d.get("juego"): foto(d["juego"], SALUD / f"fallo-{ts}.png")
    return linea, jugando


def main(argv=None):
    import argparse
    a = argparse.ArgumentParser(); a.add_argument("--cada", type=int); a.add_argument("--vistas", action="store_true"); a.add_argument("--foto", action="store_true")
    args = a.parse_args(argv); mem = {}
    while True:
        linea, jugando = pasada(args, mem)
        print(linea["ts"], linea["resumen"], linea["fase"], "·", "; ".join(f"{x['id']} {x['nivel']}" + (f" ({x['detalle']})" if x["detalle"] else "") for x in linea["res"]), flush=True)
        if not args.cada: return 1 if linea["resumen"] == "FALLA" else 0
        time.sleep(args.cada if jugando else max(args.cada, 300))


if __name__ == "__main__": sys.exit(main())
