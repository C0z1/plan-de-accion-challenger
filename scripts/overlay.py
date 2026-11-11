"""Overlay en partida (v0.5): franja fina siempre encima con los timers de dragón y barón y tu nivel/CS contra tu rival.
Solo lee el estado de HTC (que a su vez solo lee la Live Client Data): no inyecta nada en el juego. Los clics la
atraviesan (WS_EX_TRANSPARENT) y no roba el foco. Se ve con LoL en «sin bordes» (el modo por defecto), no en pantalla
completa exclusiva. Sin dependencias: tkinter + ctypes."""
import time

BG, TXT, ROSA, AMBAR = "#1A0C13", "#F2F4F7", "#F28DB0", "#F5C26B"
AVISO_SEGUNDOS = 12  # F1: lo que dura el aviso corto en la franja (lo bastante para leer 8 palabras de reojo)


def reloj(seg):
    seg = max(0, int(seg)); return f"{seg // 60}:{seg % 60:02d}"


def pieza_aviso(aviso, ahora):
    """F1: el aviso corto de la partida, los AVISO_SEGUNDOS que dura en la franja (la quinta pieza, siempre al final); o None."""
    if not aviso or not aviso.get("franja") or not aviso.get("corto") or ahora - aviso["franja"] >= AVISO_SEGUNDOS: return None
    return (aviso["corto"], AMBAR)


def partes(meta, ahora, aj=None, regla=None):
    """[(texto, color)] de la franja, o [] sin datos. meta = ESTADO["meta"] (companion.meta_fase + «recibido»): los
    timers llegan cada 30 s; entre fotos se descuentan con el reloj local."""
    if not meta: return []
    aj = aj or {}; on = lambda k: aj.get(k, True) is not False  # piezas de Ajustes: sin dato, visibles
    if meta.get("modo") == "ARAM":  # sin líneas ni dragón: el marcador, la amenaza y tu KDA
        (tu, ellos), a = meta.get("kills") or [0, 0], (meta.get("amenazas") or [{}])[0]
        cuidado = [(f"Cuidado {a['campeon']} {a['kda']}", AMBAR)] if a.get("campeon") else []
        return [(("▼ " if tu < ellos else "") + f"Kills {tu} vs {ellos}", ROSA if tu < ellos else TXT)] + cuidado + [(f"Tu KDA {meta.get('kda', '')}", TXT)]
    o, edad = meta.get("objetivos") or {}, 0.0 if meta.get("pausa") else max(0.0, ahora - (meta.get("recibido") or ahora))  # en pausa no bajan
    minuto, c = meta.get("minuto") or 0, {}  # c: pieza → (texto, color); luego se eligen por fase
    for nombre, k in (("Anciano" if o.get("anciano") else "Dragón", "dragon"), ("Barón", "baron")):
        if k not in o or not on("franja_objetivos"): continue
        if o[k] is None: c[k] = (f"{nombre} vivo", ROSA); continue
        falta = max(0, o[k] - edad)
        if falta < 60: c[k] = (f"! {nombre} {reloj(falta)}", AMBAR)  # «!» además del color: urgente
        else: c[k] = (f"{nombre} {reloj(falta)}", TXT)
        c[k + "_falta"] = falta
    if on("franja_linea") and meta.get("nivel") is not None and meta.get("nivel_rival") is not None:
        d = meta["nivel"] - meta["nivel_rival"]; c["abajo_nv"] = d < 0
        c["nivel"] = (("▼ " if d < 0 else "") + f"Nv {meta['nivel']} vs {meta['nivel_rival']}" + (f" {meta['rival']}" if meta.get("rival") else ""), ROSA if d < 0 else TXT)
    if on("franja_linea") and meta.get("cs") is not None and meta.get("rival_cs") is not None:
        c["cs"] = (("▼ " if meta["cs"] < meta["rival_cs"] else "") + f"CS {meta['cs']} vs {meta['rival_cs']}", ROSA if meta["cs"] < meta["rival_cs"] else TXT)
    m14, de_nivel = meta.get("muertes14"), (regla or {}).get("metrica") == "nivel"
    if on("franja_regla") and de_nivel and minuto < 8 and "nivel" in c:  # F3: tu regla de hoy es la del nivel al 6
        nv = c.pop("nivel"); c["regla"] = (nv[0].replace("Nv ", "Regla Nv 6: ", 1), nv[1])
    tope = (regla or {}).get("tope", 2)  # F12: tu coach puede poner otro tope de muertes
    if on("franja_regla") and not de_nivel and m14 is not None and 14 <= minuto < 25:  # tu regla que más pesa (≤ 2 muertes del 14 al 25), a la vista toda la fase
        c["regla"] = (("▼ " if m14 > tope else "") + f"Muertes 14–25: {m14}/{tope}", ROSA if m14 > tope else AMBAR if m14 == tope else TXT)
    oro = meta.get("oro") or {}
    dif = lambda a, b: round((a - b) / 50) * 50  # oro en ítems (lo de Tab), redondeado: el detalle no cambia la decisión
    if on("franja_linea") and oro.get("tu") is not None and oro.get("rival") is not None:
        d = dif(oro["tu"], oro["rival"]); c["oro"] = (("▼ " if d < 0 else "") + f"Oro {d:+d}", ROSA if d < 0 else TXT)
    if oro.get("equipo") is not None and oro.get("equipo_rival") is not None:
        d = dif(oro["equipo"], oro["equipo_rival"]); c["oro_equipo"] = (("▼ " if d < 0 else "") + f"Equipo {d:+d}", ROSA if d < 0 else TXT)
    if meta.get("muerto"):  # F4: muerto es el único momento con atención libre: tu regla y el próximo objetivo, nada más
        sig = min((k for k in ("dragon", "baron") if k in c), key=lambda k: c.get(k + "_falta", -1), default=None)
        if "regla" not in c and m14 is not None and 14 <= minuto < 25: c["regla"] = (f"Muertes 14–25: {m14}/{tope}", ROSA if m14 > tope else TXT)  # pasado el 25 ya cuenta otras
        return [c[k] for k in ("regla", sig) if k and c.get(k)]
    return elegir(c, minuto)


MAX_PIEZAS = 4  # más que esto no se lee de reojo en partida (plan en partida, F6)
ORDEN = ("regla", "nivel", "cs", "oro", "oro_equipo", "dragon", "baron")  # orden fijo en pantalla: el ojo aprende dónde mirar


def elegir(c, minuto):
    """Las MAX_PIEZAS más importantes para la fase de la partida, en el orden fijo de ORDEN."""
    pronto = lambda k, s: k in c and (c.get(k + "_falta") is None or c[k + "_falta"] <= s)  # vivo, o sale en ≤ s segundos
    if minuto < 6: prio = ["regla", "nivel", "cs"] + (["dragon"] if pronto("dragon", 90) else [])
    elif minuto < 14: prio = ["regla", "oro", "cs", "dragon"] + (["nivel"] if c.get("abajo_nv") else [])
    elif minuto < 25: prio = ["regla", "dragon"] + (["baron"] if pronto("baron", 180) else []) + ["oro_equipo"]
    else: prio = (["baron"] if pronto("baron", 180) else []) + ["dragon", "oro_equipo"]
    elegidas = [k for k in prio if k in c][:MAX_PIEZAS]
    return [c[k] for k in ORDEN if k in elegidas]


def atravesable(root):
    """Los clics pasan al juego y la franja no aparece en la barra de tareas ni toma el foco (Windows)."""
    try:
        import ctypes
        u = ctypes.windll.user32; hwnd = u.GetParent(root.winfo_id())
        u.SetWindowLongW(hwnd, -20, u.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20 | 0x80 | 0x08000000)  # LAYERED|TRANSPARENT|TOOLWINDOW|NOACTIVATE
    except (AttributeError, OSError): pass  # fuera de Windows: ventana normal


def pos_y(pos, alto_pantalla, alto_franja, margen=6, util=1.0):
    """Coordenada y de la franja: arriba (por defecto) o abajo, sobre la barra de tareas (util = fracción de alto sin ella)."""
    return max(0, int(alto_pantalla * util) - alto_franja - margen) if pos == "abajo" else margen


def rect_juego():
    """(x0, y0, x1, y1) de la ventana del juego (RiotWindowClass) o None. Solo se lee su posición: nunca se le manda nada."""
    try:
        import ctypes, ctypes.wintypes
        u = ctypes.windll.user32; h = u.FindWindowW("RiotWindowClass", None)
        if not h or not u.IsWindowVisible(h) or u.IsIconic(h): return None
        r = ctypes.wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r))
        return (r.left, r.top, r.right, r.bottom) if r.right - r.left > 200 and r.bottom - r.top > 200 else None
    except Exception: return None


TOPE_DERECHO = 0.76  # el marcador del juego (kills, KDA, CS, reloj) empieza en ~0,78 del ancho (D9 del plan En vivo)


def colocar(juego, pantalla, alto_franja, x=0.22, pos=None, margen=6, util=1.0, ancho_franja=0):
    """(x, y) de la franja: relativa a la ventana del juego si se conoce (otro monitor, modo ventana); si no, a la pantalla
    principal sin la barra de tareas (D4). Si no cabe antes del marcador (pantallas chicas, escala alta), se corre a la izquierda."""
    if juego: x0, y0, x1, y1 = juego
    else: x0, y0, (x1, y1) = 0, 0, pantalla
    px = max(x0 + margen, min(int(x0 + (x1 - x0) * x), int(x0 + (x1 - x0) * TOPE_DERECHO) - ancho_franja))
    if juego: return px, (y1 - alto_franja - margen if pos == "abajo" else y0 + margen)
    return px, pos_y(pos, y1, alto_franja, margen, util)


def fraccion_util():
    """Alto del área de trabajo de Windows / alto de pantalla (ambos de la misma API: no importa la escala de DPI); 1.0 si falla."""
    try:
        import ctypes, ctypes.wintypes
        r = ctypes.wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
            return max(0.5, min(1.0, r.bottom / ctypes.windll.user32.GetSystemMetrics(1)))  # SM_CYSCREEN
    except Exception: pass
    return 1.0


FRESCA = 30  # s: la foto llega cada 10 s; sin foto nueva en 30 s el juego ya no responde y los timers mentirían


def visible(s, ahora):
    """La franja se dibuja solo en partida con datos frescos. Fase None (cliente de LoL cerrado o reiniciándose) o
    Reconnect también: la partida sigue y la foto sigue llegando; si deja de llegar (juego cerrado), se oculta."""
    recibido = (s.get("meta") or {}).get("recibido")
    return ((s.get("ajustes") or {}).get("overlay", True) is not False and s.get("fase") in ("InProgress", None, "Reconnect")
            and recibido is not None and ahora - recibido < FRESCA)


def correr(leer, seguir, x=0.22, y=6, registrar=lambda txt: None):
    """Bucle de tkinter (hilo principal). leer() -> estado de HTC; seguir() -> False para cerrar. x = fracción del ancho.
    registrar(txt): a dónde va un error de dibujo (una vez por texto)."""
    import tkinter as tk, traceback
    root = tk.Tk(); root.withdraw(); root.title("Racha franja"); root.overrideredirect(True); root.attributes("-topmost", True); root.attributes("-alpha", 0.88)
    root.configure(bg=BG); fila = tk.Frame(root, bg=BG, padx=10, pady=4); fila.pack()
    root.update_idletasks(); atravesable(root); mostrada, ultimo, errores, etiquetas = [False], [None], set(), []

    def tick():
        if not seguir(): root.destroy(); return
        try: dibujar()
        except Exception:  # un dato raro no congela la franja el resto de la partida (revisión de DeepSeek)
            if (txt := traceback.format_exc(limit=2).strip().splitlines()[-1]) not in errores: errores.add(txt); registrar(txt)
        root.after(1000, tick)

    def dibujar():
        s = leer() or {}
        aj = s.get("ajustes") or {}
        regla = (((s.get("rendimiento") or {}).get("vistas") or {}).get("regla_hoy"))  # F3: la tuya, no la del autor
        ps = partes(s.get("meta"), time.time(), aj, regla) if visible(s, time.time()) else []
        if ps and (pa := pieza_aviso(s.get("aviso"), time.time())): ps = ps + [pa]  # el aviso corto, al final y por 12 s
        if ps == ultimo[0] and ps: return  # nada cambió: no se crean widgets cada segundo (plan en partida, F6)
        if ultimo[0] and len(ps) == len(ultimo[0]):  # mismas piezas, otro texto (el timer bajó un segundo): sin crear widgets
            for et, (t, c) in zip(etiquetas, ps): et.config(text=t, fg=c)
        else:
            ultimo[0] = None  # si el dibujo falla a medias, la próxima vuelta rehace todo (revisión del asistente, 16)
            for w in fila.winfo_children(): w.destroy()
            etiquetas.clear()
            for i, (t, c) in enumerate(ps):
                if i: tk.Label(fila, text="·", fg="#7A5A68", bg=BG, font=("Segoe UI", 11)).pack(side="left", padx=4)
                etiquetas.append(tk.Label(fila, text=t, fg=c, bg=BG, font=("Segoe UI Semibold", 11))); etiquetas[-1].pack(side="left")
        ultimo[0] = ps
        if ps:  # se recoloca cada segundo: cambiar «franja_pos» en partida mueve la franja al instante
            root.update_idletasks()
            px, py = colocar(rect_juego(), (root.winfo_screenwidth(), root.winfo_screenheight()), root.winfo_reqheight(), x, aj.get("franja_pos"), y, fraccion_util(), root.winfo_reqwidth())
            root.geometry(f"+{px}+{py}")
            if not mostrada[0]: root.deiconify(); root.attributes("-topmost", True); mostrada[0] = True
        elif mostrada[0]: root.withdraw(); mostrada[0] = False

    tick(); root.mainloop()
