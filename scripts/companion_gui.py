"""Companion con ventana (tkinter): lo mismo que companion.py (solo lectura del cliente) pero dibujado.
Uso:
  python scripts/companion_gui.py           sondea el cliente cada 3 s
  python scripts/companion_gui.py --demo    pinta champ select y post-partida con datos de ejemplo (sin cliente)
  Companion.exe                             lo mismo, empaquetado (va en la raíz del repo; ver README)"""
import contextlib, importlib, io, json, os, pathlib, queue, runpy, sys, threading, time, traceback
# PyInstaller solo empaqueta lo que ve importado: estos los usan los scripts que el .exe carga del disco
import argparse, base64, collections, datetime, math, random, ssl, statistics, subprocess, webbrowser  # noqa: F401
import urllib.error, urllib.parse, urllib.request  # noqa: F401
try: import winreg  # noqa: F401
except ImportError: winreg = None

if getattr(sys, "frozen", False):  # el .exe trae solo Python: carga los scripts del repo junto a él (se actualizan sin recompilar)
    _exe = pathlib.Path(sys.executable).resolve().parent  # instalado: scripts/ junto al exe; build en dist/HTC/: el repo dos arriba
    REPO = next((p for p in (_exe, *_exe.parents) if (p / "scripts").is_dir()), _exe)
    sys.path.insert(0, str(REPO / "scripts"))
else:
    REPO = pathlib.Path(__file__).resolve().parent.parent
for _s in ("stdout", "stderr"):  # el .exe no tiene consola: los scripts hacen sys.stdout.reconfigure
    if getattr(sys, _s) is None: setattr(sys, _s, io.TextIOWrapper(io.BytesIO(), encoding="utf-8"))

import companion  # noqa: E402

RAW = pathlib.Path(os.environ.get("DATOS_DIR") or REPO / "datos" / "raw")
FIN = ("PreEndOfGame", "EndOfGame")
FASES = {None: "Cliente cerrado", "None": "Sin actividad", "Lobby": "En lobby", "Matchmaking": "Buscando partida",
         "ReadyCheck": "Partida encontrada", "ChampSelect": "Champ select", "InProgress": "En partida",
         "PreEndOfGame": "Fin de partida", "EndOfGame": "Fin de partida"}
REGLAS = ["Oro ≥ 0 contra tu rival al minuto 14.", "Ganks: minuto 3 y del 8 al 13 (pico en el 10).",
          "Con poca vida y su flash + ignite arriba: base."]  # TARJETA.md, las 3 que más pesan en línea


# ---------- lógica (sin tkinter) ----------

def script(nombre, *args):
    """Corre scripts/<nombre> en este proceso (el .exe no tiene python.exe para un subproceso): (código, salida)."""
    buf, argv = io.TextIOWrapper(io.BytesIO(), encoding="utf-8"), sys.argv
    sys.argv = [nombre, *args]
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            runpy.run_path(str(REPO / "scripts" / nombre), run_name="__main__"); code = 0
    except SystemExit as e: code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except Exception: code = 1; buf.write(traceback.format_exc())
    finally: sys.argv = argv
    buf.flush(); return code, buf.buffer.getvalue().decode("utf-8", "replace")


def parsear_revision(salida):
    """Primera fila de «Partida por partida» de revision.py: dict con las metas de la partida más reciente."""
    filas = [l for l in salida.split("## Partida por partida")[-1].splitlines() if l.startswith("| ") and not l.startswith("| Fecha")]
    if not filas: return None
    _, camp, vd, oro, cs, m14, m25, cw, *sc = [c.strip() for c in filas[0].strip().strip("|").split("|")]
    racha = salida.split("## Racha de oro bajo al 14")[1].split("## ")[0].strip().splitlines() if "## Racha de oro bajo al 14" in salida else []
    return dict(champ=camp.replace(" (fuera del pool)", ""), pool="fuera del pool" not in camp, win=vd == "V",
                oro=oro, cs=cs, m14=m14, m25=m25, cw=cw, score=sc[0] if sc else "-", racha=[l.removeprefix("- ") for l in racha if l.strip()])


def ultima_partida():
    """KDA, rival y duración de la partida más nueva en datos/raw (los id de partida crecen con el tiempo)."""
    try:
        puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
        f = max(RAW.glob("*_*.json"), key=lambda p: int(p.stem.split("_")[1]))
        info = json.loads(f.read_text())["info"]; ps = info["participants"]
        me = next(p for p in ps if p["puuid"] == puuid)
        opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
        out = dict(kda=f"{me['kills']}/{me['deaths']}/{me['assists']}", min=info["gameDuration"] // 60,
                   rival=opp["championName"] if opp else None)
    except (OSError, ValueError, KeyError, StopIteration): return {}
    try:  # revisión post-partida (postpartida.py): 3 momentos clave y muertes sin objetivo, si hay timeline
        import postpartida
        m, tl = json.loads(f.read_text()), json.loads((RAW / "timeline" / f.name).read_text())
        libres = postpartida.muertes_sin_objetivo(m, tl, puuid)
        out.update(momentos=[x["texto"] for x in postpartida.momentos(m, tl, puuid)],
                   libres=[libres["n"], libres["total"]] if libres["total"] else None)
    except (OSError, ValueError): pass
    return out


AJUSTES_F = REPO / "datos" / "cache" / "ajustes.json"
AJUSTES_DEF = {"overlay": True, "aviso_nivel": True, "aviso_minions": True, "aviso_muertes": True, "aviso_regreso": True, "aviso_pico": True,  # Ajustes_Vino
               "metricas": False,  # métricas anónimas: solo si el amigo las prende (v0.8)
               "grupo": False,  # aparecer en la tabla del grupo (Riot ID y win rate a los demás): solo si lo prende
               "franja_objetivos": True, "franja_linea": True, "franja_regla": True,  # piezas de la franja en partida (A4)
               "franja_pos": "arriba"}  # esquina de la franja: único ajuste que no es booleano
OPCIONES = {"franja_pos": ("arriba", "abajo")}  # lista blanca de los ajustes de texto


def valido(clave, v):
    return v in OPCIONES[clave] if clave in OPCIONES else isinstance(v, bool)


def ajustes():
    """Ajustes guardados (los que faltan, por defecto); un archivo roto no tumba nada."""
    try: d = json.loads(AJUSTES_F.read_text(encoding="utf-8"))
    except (OSError, ValueError): d = {}
    return {k: d[k] if k in d and valido(k, d[k]) else v for k, v in AJUSTES_DEF.items()}


def guardar_ajuste(clave, on):
    """Guarda un ajuste conocido; devuelve todos. Clave desconocida: ValueError (lista blanca)."""
    if clave not in AJUSTES_DEF or not valido(clave, on): raise ValueError(clave)
    a = {**ajustes(), clave: on}
    AJUSTES_F.parent.mkdir(parents=True, exist_ok=True); AJUSTES_F.write_text(json.dumps(a), encoding="utf-8")
    return a


NOMBRES = {}  # championId -> nombre del cliente (companion_web.vigilar_cuenta), para quien no tiene partidas descargadas
CUENTA = [None]  # «gameName#tag» con sesión en el cliente (la pone companion_web.vigilar_cuenta)


def dueno():
    """«gameName#tag» de la cuenta cuyas partidas están en disco (perfil.json), o None."""
    try: a = json.loads((RAW / "perfil.json").read_text())["account"]; return f"{a['gameName']}#{a['tagLine']}"
    except (OSError, ValueError, KeyError, TypeError): return None


def ajeno(cuenta):
    """True si el cliente tiene otra cuenta que la de las partidas en disco: ese historial no es de quien juega."""
    d = dueno()
    return bool(cuenta and d and cuenta.casefold() != d.casefold())


def perfil(r=None, cuenta=None):
    """«gameName#tag · Master 15 LP · 120-100 (55%)». La cuenta con sesión en el cliente manda; el rango r (fresco del
    cliente) gana al de perfil.json, que solo se usa si es de esa misma cuenta."""
    tx = lambda x: " ".join(y for y in (x["tier"].title(), x["division"], f"{x['lp']} LP") if y) + (f" · {x['wins']}-{x['losses']} ({x['wr']}%)" if x["n"] else "")
    if cuenta and ajeno(cuenta): return f"{cuenta} · {tx(r)}" if r else cuenta
    try:
        d = json.loads((RAW / "perfil.json").read_text()); a = d["account"]
        solo = next((e for e in d["league"] if e["queueType"] == "RANKED_SOLO_5x5"), None)
        rango = f"{solo['tier'].title()} {solo.get('rank', '') if solo['tier'] not in ('MASTER', 'GRANDMASTER', 'CHALLENGER') else ''} {solo['leaguePoints']} LP".replace("  ", " ") if solo else "sin rango"
        return f"{a['gameName']}#{a['tagLine']} · {tx(r) if r else rango}"
    except (OSError, ValueError, KeyError, TypeError):
        if cuenta: return f"{cuenta} · {tx(r)}" if r else cuenta  # amigo sin partidas descargadas: su cuenta y rango, del cliente
        return "sin historial todavía"


def puede_descargar():
    """Tu RIOT_KEY o tu código de acceso al backend de Racha: con cualquiera de los dos se bajan tus partidas."""
    return hay_key() or companion.acceso(REPO) is not None


def guardar_acceso(token):
    """Guarda tu código de acceso (lo da quien administra el backend). Solo letras, números y guiones: ValueError si no."""
    import re
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9-]{6,64}", token): raise ValueError("código inválido")
    f = REPO / "datos" / "cache" / "acceso.json"
    try: d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError): d = {}
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps({**d, "token": token}), encoding="utf-8")


def hay_key():
    if os.environ.get("RIOT_KEY"): return True
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k: return bool(winreg.QueryValueEx(k, "RIOT_KEY")[0])
    except (AttributeError, OSError): return False


def rival_probable(pos, nombres):
    """En ranked Riot oculta el rol de los enemigos: de los ya elegidos, el que más veces fue tu rival en esa posición
    (tus partidas). None si ninguno sale en tus partidas o no hay datos: entonces se muestran todos."""
    try: import draft
    except Exception: return None
    from collections import Counter
    c = Counter(g["opp"] for g in draft.games if g.get("pos") == pos)
    mejor = max((n for n in nombres if n), key=lambda n: c.get(n, 0), default=None)
    return mejor if mejor and c.get(mejor, 0) > 0 else None


def recomendaciones(pos, rivales):
    """[(rival, datos_draft | None)] usando draft.py (lo recarga si hay partidas nuevas)."""
    if ajeno(CUENTA[0]): return [(r, None) for r in rivales]  # tus partidas en disco son de otra cuenta: no recomendar con ellas
    try: import draft
    except (AssertionError, OSError, ValueError, KeyError): return [(r, None) for r in rivales]  # sin partidas ni perfil.json (beta sin key): rival «sin datos», no un error
    with DRAFT: return [(r, dict(draft.datos_draft(r, pos), ficha=draft.ficha(r, pos)) if r else None) for r in rivales]


DRAFT = threading.Lock()  # el reload de draft (hilo post-partida) no debe pisar un datos_draft a medias
POST = []  # el hilo post-partida vivo, si hay


def aviso(texto, tipo="error", minuto=None):
    """Evento de aviso para la cola: {texto, tipo: consejo (en partida) | error, minuto de juego o None} (pedido del Diseñador)."""
    return ("aviso", {"texto": texto, "tipo": tipo, "minuto": minuto})


def post_partida(q):
    """Lanza la descarga y revisión en otro hilo: tarda hasta ~7 min y el sondeo debe ver el próximo champ select."""
    if POST and POST[0].is_alive(): return
    POST[:] = [threading.Thread(target=_post_partida, args=(q,), daemon=True)]; POST[0].start()


def _post_partida(q):
    if not puede_descargar(): return  # beta sin key: la foto en vivo del final ya basta; no avisar de una descarga que no puede ser
    q.put(("post_espera", "Esperando a que Riot publique la partida…")); time.sleep(60)
    for intento in range(4):
        code, _ = script("descargar.py", "5")
        if code != 3: break
        q.put(("post_espera", "Riot aún no publica la partida: reintento en 2 min…")); time.sleep(120)
    if code == 2: q.put(aviso("Key de Riot caducada: copia la nueva del portal (se abrió) y guárdala con setx RIOT_KEY <key>")); return
    if code: q.put(aviso(f"No pude descargar la partida (código {code}); queda pendiente.")); return
    if "draft" in sys.modules:
        with DRAFT: importlib.reload(sys.modules["draft"])  # partidas nuevas para el próximo champ select
    code, out = script("revision.py", "1")
    rev = parsear_revision(out)
    q.put(("revision", {**rev, **ultima_partida()}) if rev else aviso("revision.py no devolvió la partida."))


def texto_meta(mf):
    """«Min 7 · Nv 6 contra 7 (Zed) · CS 52 (meta 69 al 10)» desde companion.meta_fase(); en ARAM, kills y la amenaza."""
    if mf.get("modo") == "ARAM":
        a = (mf.get("amenazas") or [{}])[0]
        return " · ".join([f"Min {mf['minuto']}", f"Kills {mf['kills'][0]}–{mf['kills'][1]}", f"Tu KDA {mf['kda']}"]
                          + ([f"Cuidado con {a['campeon']} {a['kda']}"] if a.get("campeon") else []))
    t = [f"Min {mf['minuto']}", f"Nv {mf['nivel'] or '?'}"]
    if mf["rival"]: t[-1] += f" contra {mf['nivel_rival'] or '?'} ({mf['rival']})"
    t.append(f"CS {mf['cs'] if mf['cs'] is not None else '?'}" + (f" (meta {mf['cs_meta']} al 10)" if mf["cs_meta"] and mf["minuto"] < 11 else ""))
    if mf.get("muertes14") is not None and mf["minuto"] < 25: t.append(f"Muertes desde el 14: {mf['muertes14']} (meta ≤ 2)")
    return " · ".join(t)


def _dif(m, ref, k, nombre, fmt):
    """«CS al 14 −17 (tu media −3)» o None si no hay medida."""
    def f(v):
        s = format(v, fmt)
        return format(0.0, fmt) if float(s) == 0 else s  # sin «−0»
    if m.get(k) is None: return None
    r = f" (tu media {f(ref[k])})" if ref.get(k) is not None else ""
    return f"{nombre} {f(m[k])}{r}".replace("-", "−")


def lineas_ficha(fi):
    """(cuidado, counters): renglones de texto de draft.ficha() para la ventana (pedidos 3 y 4 del Diseñador).
    Solo lo medido; [] si no hay nada que decir."""
    if not fi: return [], []
    c, ref = fi["cuidado"], fi["cuidado"]["ref"]
    cuidado = []
    if c["n"]:
        ant = c.get("anticipa") or ()  # las que anticipan la próxima partida (anticipa.py) van solas; el resto, juntas y marcadas
        difs = [(k in ant, _dif(c, ref, k, n, f)) for k, n, f in [("muertes6", "Muertes antes del 6", ".1f"), ("oro14", "Oro al 14", "+.0f"),
                                                                ("cs14", "CS al 14", "+.0f"), ("nivel6", "Nivel al 6", "+.1f")]]
        resto = " · ".join(d for a, d in difs if d and not a)
        cuidado = ([f"Tú contra {c['rival']} (cualquier campeón): {c['v']}-{c['n'] - c['v']} (Wilson {c['ic'][0]:.0%}–{c['ic'][1]:.0%})"
                    + ("; pocas partidas, pista" if c["pocas"] else "")] + [f"{d}; esta sí tiende a repetirse contra él" for a, d in difs if d and a]
                   + ([f"{resto}; no se repite de una partida a la siguiente"] if resto else []))
    cuidado += [f"Tu nota: {n}" for n in c["notas"]]
    ref = fi["counters"]["ref"]
    counters = [f"{x['rival']} {x['v']}-{x['n'] - x['v']} (Wilson {x['ic'][0]:.0%}–{x['ic'][1]:.0%})"
                + "".join(f" · {d}" for d in [_dif(x, ref, "cs14", "CS al 14", "+.0f"), _dif(x, ref, "oro14", "oro", "+.0f")] if d)
                + ("; pista" if x["pocas"] else "") for x in fi["counters"]["lista"]]
    return cuidado, counters


def trabajador(q):
    """El mismo bucle que companion.main, pero manda eventos a la ventana en vez de imprimir."""
    m, visto, fase_ant, real, archivo, ult, avisado, fallos = None, None, "inicio", None, None, 0, set(), 0
    error = foto = None
    while True:
        fase = None  # si lcu() lanza, cuenta como cliente caído
        try:
            fase = companion.lcu("/lol-gameflow/v1/gameflow-phase")
            if fase != fase_ant and fase == "ChampSelect":  # LP fresco del cliente (sin key); ya asentado tras la partida anterior
                q.put(("rango", companion.rango(companion.lcu("/lol-ranked/v1/current-ranked-stats"))))
            if fase != fase_ant: q.put(("fase", fase))
            jugando = (fase or real) == "InProgress"  # cliente reiniciándose a media partida: la partida sigue
            if fase == "ChampSelect" and (s := companion.lcu("/lol-champ-select/v1/session")):
                pos, ids = companion.rivales(s)
                tm = s.get("timer") or {}  # cronómetro de la fase (solo lectura), para el reloj de Draft_Vino
                if isinstance(tm.get("adjustedTimeLeftInPhase"), (int, float)):
                    q.put(("crono", {"fase": tm.get("phase"), "ms": tm["adjustedTimeLeftInPhase"], "t": time.time()}))
                if ids and (pos, ids) != visto:
                    m = m or companion.nombres() or dict(NOMBRES); visto = (pos, ids)
                    nombres = [m.get(i) for i in ids]
                    if len(nombres) > 1 and (p := rival_probable(pos, nombres)): nombres = [p]  # el rival de línea más probable
                    q.put(("draft", pos, recomendaciones(pos, nombres), len(ids) > 1))
                elif not ids and pos and visto != pos: q.put(("pos", pos)); visto = pos  # bans y picks antes del rival
            elif fase != "ChampSelect": visto = None
            if jugando and time.time() - ult >= 30:
                d = companion.vivo(); archivo, ult = companion.capturar(archivo, d), time.time(); foto = d or foto
                if mf := companion.meta_fase(d): q.put(("meta", mf))
                aj = ajustes()  # Ajustes_Vino: cada aviso se puede apagar
                for f in (companion.aviso_nivel, companion.aviso_minions, companion.aviso_muertes, companion.aviso_regreso):
                    if f not in avisado and aj.get(f.__name__, True) and (txt := f(d)):
                        q.put(aviso(txt, "consejo", int((((d or {}).get("gameData") or {}).get("gameTime") or 0) // 60))); avisado.add(f)
                if aj.get("aviso_pico", True) and (r := companion.aviso_pico(d)) and r[0] not in avisado:  # uno por ítem del rival
                    q.put(aviso(r[1], "consejo", int((((d or {}).get("gameData") or {}).get("gameTime") or 0) // 60))); avisado.add(r[0])
            elif not jugando: archivo, avisado = None, set()
            if fase in FIN and real not in FIN:
                if r := companion.resumen_fin(foto): q.put(("fin", r))  # sin key, esto es todo lo que hay al terminar
                foto = None; post_partida(q); m = None
            error = None
        except Exception:
            txt = "Error: " + traceback.format_exc(limit=1).strip().splitlines()[-1]
            if txt != error: q.put(aviso(txt)); error = txt  # el mismo error cada 3 s no inunda la ventana
        # fuera del try (como companion.main): una excepción no deja la fase vieja ni repite el evento de fase cada 3 s
        fase_ant, real, fallos = fase, fase or real, 0 if fase else fallos + 1
        time.sleep(companion.espera(fallos))


# ---------- ventana ----------

BG, PANEL, BORDE, TXT, MUTED, ACENTO, BIEN, MAL, BARRA = "#0E1015", "#171A21", "#232833", "#E8EAF0", "#9AA3B2", "#F2B33D", "#7DB8FF", "#F59E5B", "#5B6475"
F, MONO = "Segoe UI", "Consolas"


class App:
    def __init__(self, root):
        import tkinter as tk
        self.tk, self.root, self.fase, self.pendiente, self.fin, self.rango = tk, root, None, None, None, None
        root.title("Plan Challenger · Companion"); root.configure(bg=BG); root.geometry("420x760"); root.minsize(380, 560)
        cab = tk.Frame(root, bg=BG); cab.pack(fill="x", padx=16, pady=(14, 12))
        tk.Label(cab, text="PC", bg=ACENTO, fg=BG, font=(F, 10, "bold"), width=3, height=1).pack(side="left")
        tt = tk.Frame(cab, bg=BG); tt.pack(side="left", padx=10)
        tk.Label(tt, text="Plan Challenger", bg=BG, fg=TXT, font=(F, 11, "bold")).pack(anchor="w")
        self.sub = tk.Label(tt, text=perfil(), bg=BG, fg=MUTED, font=(F, 8)); self.sub.pack(anchor="w")
        self.pill = tk.Label(cab, text="Iniciando…", bg=BORDE, fg=TXT, font=(F, 9, "bold"), padx=10, pady=3); self.pill.pack(side="right")
        self.sep = tk.Frame(root, bg=BORDE, height=1); self.sep.pack(fill="x")
        self.aviso = tk.Label(root, bg=MAL, fg=BG, font=(F, 9, "bold"), wraplength=380, justify="left", padx=12, pady=8)
        pie = tk.Frame(root, bg=BG); pie.pack(side="bottom", fill="x")
        tk.Frame(pie, bg=BORDE, height=1).pack(fill="x")
        fila = tk.Frame(pie, bg=BG); fila.pack(fill="x", padx=16, pady=8)
        tk.Label(fila, text="Solo lectura · nunca actúa en el cliente", bg=BG, fg=MUTED, font=(F, 8)).pack(side="left")
        self.key = tk.Label(fila, bg=BG, font=(MONO, 8)); self.key.pack(side="right"); self.ver_key()
        self.cuerpo = tk.Frame(root, bg=BG); self.cuerpo.pack(fill="both", expand=True, padx=16, pady=12)
        self.espera("Abre el cliente de LoL: aquí verás tu pick en champ select y la revisión al terminar.")

    # piezas
    def limpiar(self):
        for w in self.cuerpo.winfo_children(): w.destroy()

    def tarjeta(self, borde=BORDE):
        c = self.tk.Frame(self.cuerpo, bg=PANEL, highlightbackground=borde, highlightcolor=borde, highlightthickness=1)
        c.pack(fill="x", pady=(0, 12)); i = self.tk.Frame(c, bg=PANEL); i.pack(fill="x", padx=14, pady=12); return i

    def etiqueta(self, p, texto, color=MUTED):
        self.tk.Label(p, text=texto.upper(), bg=PANEL, fg=color, font=(F, 8, "bold")).pack(anchor="w")

    def par(self, p, izq, der, fi=(F, 20, "bold"), fd=(MONO, 12), cd=MUTED):
        f = self.tk.Frame(p, bg=PANEL); f.pack(fill="x", pady=(6, 0))
        self.tk.Label(f, text=izq, bg=PANEL, fg=TXT, font=fi).pack(side="left")
        self.tk.Label(f, text=der, bg=PANEL, fg=cd, font=fd).pack(side="right")

    def reglas(self, titulo="Reglas para esta partida", lineas=REGLAS, borde=BORDE, color=MUTED):
        t = self.tarjeta(borde); self.etiqueta(t, titulo, color)
        for l in lineas: self.tk.Label(t, text="•  " + l, bg=PANEL, fg=TXT, font=(F, 10), wraplength=340, justify="left").pack(anchor="w", pady=(6, 0))

    # vistas
    def espera(self, texto):
        self.limpiar()
        if self.fin:  # la línea de la última foto en vivo, hasta que llegue la revisión o el próximo champ select
            t = self.tarjeta(ACENTO); self.etiqueta(t, "Al terminar (foto en vivo)", ACENTO)
            self.tk.Label(t, text=self.fin, bg=PANEL, fg=TXT, font=(F, 10, "bold"), wraplength=340, justify="left").pack(anchor="w", pady=(6, 0))
        t = self.tarjeta()
        self.tk.Label(t, text=texto, bg=PANEL, fg=TXT, font=(F, 10), wraplength=340, justify="left").pack(anchor="w")
        self.reglas()

    def vista_draft(self, pos, recs):
        self.limpiar()
        if len(recs) > 1:  # sin rol de los rivales: una fila por rival
            t = self.tarjeta(); self.etiqueta(t, f"Rivales elegidos · {pos} (rol desconocido)")
            for r, d in recs:
                mejor = f"{d['filas'][0]['champ']} {d['filas'][0]['est']:.0%}" if d and d["filas"] else "sin datos"
                self.par(t, r or "?", mejor, fi=(F, 12, "bold"), fd=(MONO, 11), cd=ACENTO)
            self.reglas(); return
        r, d = recs[0]
        t = self.tarjeta(); self.etiqueta(t, f"Tu rival de línea · {pos}")
        if not d or not d["conocido"]:
            self.par(t, r or "?", "sin partidas"); self.tk.Label(t, text="No aparece en tus partidas: va tu WR por campeón.", bg=PANEL, fg=MUTED, font=(F, 9)).pack(anchor="w", pady=(6, 0))
        else:
            import draft
            vs = d["vs"]; k = sum(g["win"] for g in vs)
            self.par(t, d["nombre"], f"{len(vs)} partidas")
            g = self.tk.Frame(t, bg=PANEL); g.pack(fill="x", pady=(8, 0)); g.columnconfigure((0, 1), weight=1, uniform="c")
            for col, (lab, val, color) in enumerate([("Tu WR contra él", f"{k / len(vs):.0%}" if vs else "-", BIEN),
                                                     ("Oro al 14 (media)", draft.gd(vs), MAL if draft.gd(vs).startswith("-") else BIEN)]):
                b = self.tk.Frame(g, bg=BG); b.grid(row=0, column=col, sticky="ew", padx=(0, 4) if col == 0 else (4, 0))
                self.tk.Label(b, text=lab, bg=BG, fg=MUTED, font=(F, 8)).pack(anchor="w", padx=10, pady=(8, 0))
                self.tk.Label(b, text=val.replace("-", "−"), bg=BG, fg=color, font=(MONO, 16, "bold")).pack(anchor="w", padx=10, pady=(0, 8))
        if not d or not d["filas"]: self.reglas(); return
        t = self.tarjeta(ACENTO); self.etiqueta(t, "Recomendación", ACENTO)
        mejor = d["filas"][0]; self.par(t, mejor["champ"], f"{mejor['est']:.0%}", fi=(F, 22, "bold"), fd=(MONO, 22, "bold"), cd=ACENTO)
        for i, f in enumerate(d["filas"][:4]):
            fila = self.tk.Frame(t, bg=PANEL); fila.pack(fill="x", pady=(10, 0))
            self.tk.Label(fila, text=f["champ"], bg=PANEL, fg=TXT, font=(F, 10, "bold")).pack(side="left")
            self.tk.Label(fila, text=f"{f['vd']} · {f['est']:.0%}", bg=PANEL, fg=MUTED, font=(MONO, 10)).pack(side="right")
            c = self.tk.Canvas(t, height=6, bg=BG, highlightthickness=0); c.pack(fill="x", pady=(4, 0))
            c.bind("<Configure>", lambda e, c=c, est=f["est"], col=ACENTO if i == 0 else BARRA:
                   (c.delete("all"), c.create_rectangle(0, 0, e.width * est, 6, fill=col, width=0)))
        por_que = (d.get("ficha") or {}).get("por_que", {}).get("frase", "Tu récord contra el rival, mezclado con tu WR del campeón en el rol.")
        self.tk.Label(t, text=por_que, bg=PANEL, fg=MUTED,
                      font=(F, 8), wraplength=340, justify="left").pack(anchor="w", pady=(10, 0))
        for a in d.get("avisos", []):
            self.tk.Label(t, text=a, bg=PANEL, fg=MAL, font=(F, 9, "bold"), wraplength=340, justify="left").pack(anchor="w", pady=(8, 0))
        if d.get("build"): self.reglas(f"Build · {mejor['champ']}", [l.strip() for l in d["build"]], ACENTO, ACENTO)
        rs = (d.get("ficha") or {}).get("reglas")
        self.reglas(f"Cómo jugar {mejor['champ']}", [f"{r['texto']} ({r['numero']}{'; pista' if r['pista'] else ''})"
                                                    for r in rs]) if rs else self.reglas()
        cuidado, counters = lineas_ficha(d.get("ficha"))
        if cuidado: self.reglas(f"Cuidado con {d['ficha']['rival']}", cuidado, MAL, MAL)
        if counters: self.reglas(f"Counters de {mejor['champ']}", counters)

    def vista_revision(self, r):
        self.limpiar(); t = self.tarjeta()
        self.etiqueta(t, f"{'Victoria' if r['win'] else 'Derrota'}" + (f" · {r['min']} min" if r.get("min") else ""), BIEN if r["win"] else MAL)
        self.par(t, r["champ"] + (f"  vs {r['rival']}" if r.get("rival") else ""), r.get("kda", ""), fi=(F, 15, "bold"), fd=(MONO, 15, "bold"), cd=TXT)
        t = self.tarjeta(); self.etiqueta(t, "Metas del plan")
        num = lambda s: int(s) if s.lstrip("+-").isdigit() else None
        metas = [("Oro contra tu rival al 14", r["oro"], (num(r["oro"]) or 0) >= 0 if num(r["oro"]) is not None else None),
                 ("CS contra tu rival al 14", r["cs"], (num(r["cs"]) or 0) >= 0 if num(r["cs"]) is not None else None),
                 ("Muertes del 14 al 25 (≤ 2)", r["m25"], num(r["m25"]) <= 2 if num(r["m25"]) is not None else None),
                 ("Campeón de tu pool", "sí" if r["pool"] else "no", r["pool"])]
        for lab, val, ok in metas:
            f = self.tk.Frame(t, bg=BG); f.pack(fill="x", pady=(8, 0))
            color = MUTED if ok is None else BIEN if ok else MAL
            self.tk.Label(f, text="–" if ok is None else "✓" if ok else "✕", bg=color, fg=BG, font=(F, 9, "bold"), width=2).pack(side="left", padx=(8, 8), pady=6)
            self.tk.Label(f, text=lab, bg=BG, fg=TXT, font=(F, 10)).pack(side="left")
            self.tk.Label(f, text=val.replace("-", "−"), bg=BG, fg=color, font=(MONO, 10, "bold")).pack(side="right", padx=10)
        if r.get("racha"): self.reglas("Racha de oro bajo al 14", r["racha"], MAL, MAL)
        self.reglas("Detalle", [f"Muertes antes del 14: {r['m14']} · control wards: {r['cw']}.",
                                f"Score {r.get('score', '-')} (50 = típico de tu rol en la partida; ver python scripts/score.py)."], ACENTO, ACENTO)

    def ver_key(self):
        k = hay_key(); self.key.config(text="key ok" if k else "falta RIOT_KEY", fg=MUTED if k else MAL)

    def evento(self, e):
        tipo = e[0]
        if tipo == "fase":
            fase = e[1]; self.ver_key()  # la key se pudo renovar con setx sin reabrir la ventana
            self.pill.config(text=FASES.get(fase, fase or "Cliente cerrado"), bg=ACENTO if fase in ("ChampSelect", "InProgress") else BORDE,
                                          fg=BG if fase in ("ChampSelect", "InProgress") else TXT)
            if fase is None: self.espera("Cliente cerrado: espero a que lo abras.")
            elif fase == "ChampSelect": self.fin = None; self.espera("Champ select: espero a que tu rival de línea elija.")
            elif fase == "InProgress":
                if self.pendiente: self.vista_revision(self.pendiente); self.pendiente = None
                else: self.espera("En partida: guardo una foto en vivo cada 30 s en datos/vivo/.")
            elif fase in ("Lobby", "Matchmaking", "ReadyCheck"): self.aviso.pack_forget(); self.sub.config(text=perfil(self.rango))
            self.fase = fase
        elif tipo == "meta": self.sub.config(text=texto_meta(e[1]))  # Lobby la devuelve a perfil()
        elif tipo == "draft": self.vista_draft(e[1], e[2])
        elif tipo == "fin": self.fin = companion.linea_fin(e[1]); self.espera("Partida terminada: espero a Riot para la revisión completa.")
        elif self.fase in ("ChampSelect", "InProgress") and tipo == "post_espera": pass  # la post-partida va en otro hilo: no tapa el draft
        elif tipo == "post_espera": self.espera(e[1])
        elif tipo == "revision" and self.fase == "ChampSelect": self.pendiente = e[1]  # se ve al empezar la partida
        elif tipo == "rango": self.rango = e[1] or self.rango; self.sub.config(text=perfil(self.rango))  # sin respuesta: queda el último
        elif tipo == "revision": self.fin = None; self.vista_revision(e[1]); self.sub.config(text=perfil(self.rango))
        elif tipo == "aviso":
            a = e[1]; self.aviso.config(text=a["texto"], bg=BIEN if a["tipo"] == "consejo" else MAL); self.aviso.pack(fill="x", after=self.sep)


def main():
    import tkinter as tk
    root = tk.Tk(); app = App(root); q = queue.Queue()
    if "--demo" in sys.argv:
        fx = REPO / "scripts" / "fixtures" / "champselect" / "session.json"
        pos, ids = companion.rivales(json.loads(fx.read_text())) if fx.exists() else ("MIDDLE", [])
        m = companion.nombres(); rivales = [m.get(i) for i in ids] or ["Zed"]
        q.put(("fase", "ChampSelect")); q.put(("draft", pos, recomendaciones(pos, rivales[:1])))
        code, out = script("revision.py", "1"); rev = parsear_revision(out)
        if rev: root.after(6000, lambda: (q.put(("fase", "EndOfGame")), q.put(("revision", {**rev, **ultima_partida()}))))
    else: threading.Thread(target=trabajador, args=(q,), daemon=True).start()

    def bombear():
        while not q.empty(): app.evento(q.get_nowait())
        root.after(200, bombear)
    bombear(); root.mainloop()


if __name__ == "__main__":
    main()
