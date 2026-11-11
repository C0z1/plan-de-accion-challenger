"""Overlay en partida (v0.5): franja fina siempre encima con los timers de dragón y barón y tu nivel/CS contra tu rival.
Solo lee el estado de HTC (que a su vez solo lee la Live Client Data): no inyecta nada en el juego. Los clics la
atraviesan (WS_EX_TRANSPARENT) y no roba el foco. Se ve con LoL en «sin bordes» (el modo por defecto), no en pantalla
completa exclusiva. Sin dependencias: tkinter + ctypes."""
import time

BG, TXT, ROSA, AMBAR = "#1A0C13", "#F2F4F7", "#F28DB0", "#F5C26B"


def reloj(seg):
    seg = max(0, int(seg)); return f"{seg // 60}:{seg % 60:02d}"


def partes(meta, ahora, aj=None):
    """[(texto, color)] de la franja, o [] sin datos. meta = ESTADO["meta"] (companion.meta_fase + «recibido»): los
    timers llegan cada 30 s; entre fotos se descuentan con el reloj local."""
    if not meta: return []
    aj = aj or {}; on = lambda k: aj.get(k, True) is not False  # piezas de Ajustes: sin dato, visibles
    if meta.get("modo") == "ARAM":  # sin líneas ni dragón: el marcador, la amenaza y tu KDA
        (tu, ellos), a = meta.get("kills") or [0, 0], (meta.get("amenazas") or [{}])[0]
        cuidado = [(f"Cuidado {a['campeon']} {a['kda']}", AMBAR)] if a.get("campeon") else []
        return [(("▼ " if tu < ellos else "") + f"Kills {tu} vs {ellos}", ROSA if tu < ellos else TXT)] + cuidado + [(f"Tu KDA {meta.get('kda', '')}", TXT)]
    o, edad = meta.get("objetivos") or {}, max(0.0, ahora - (meta.get("recibido") or ahora))
    minuto, c = meta.get("minuto") or 0, {}  # c: pieza → (texto, color); luego se eligen por fase
    for nombre, k in (("Dragón", "dragon"), ("Barón", "baron")):
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
    m14 = meta.get("muertes14")
    if on("franja_regla") and m14 is not None and 14 <= minuto < 25:  # tu regla que más pesa (≤ 2 muertes del 14 al 25), a la vista toda la fase
        c["regla"] = (("▼ " if m14 > 2 else "") + f"Muertes 14–25: {m14}/2", ROSA if m14 > 2 else AMBAR if m14 == 2 else TXT)
    oro = meta.get("oro") or {}
    dif = lambda a, b: round((a - b) / 50) * 50  # oro en ítems (lo de Tab), redondeado: el detalle no cambia la decisión
    if on("franja_linea") and oro.get("tu") is not None and oro.get("rival") is not None:
        d = dif(oro["tu"], oro["rival"]); c["oro"] = (("▼ " if d < 0 else "") + f"Oro {d:+d}", ROSA if d < 0 else TXT)
    if oro.get("equipo") is not None and oro.get("equipo_rival") is not None:
        d = dif(oro["equipo"], oro["equipo_rival"]); c["oro_equipo"] = (("▼ " if d < 0 else "") + f"Equipo {d:+d}", ROSA if d < 0 else TXT)
    return elegir(c, minuto)


MAX_PIEZAS = 4  # más que esto no se lee de reojo en partida (plan en partida, F6)
ORDEN = ("regla", "nivel", "cs", "oro", "oro_equipo", "dragon", "baron")  # orden fijo en pantalla: el ojo aprende dónde mirar


def elegir(c, minuto):
    """Las MAX_PIEZAS más importantes para la fase de la partida, en el orden fijo de ORDEN."""
    pronto = lambda k, s: k in c and (c.get(k + "_falta") is None or c[k + "_falta"] <= s)  # vivo, o sale en ≤ s segundos
    if minuto < 6: prio = ["nivel", "cs", "regla"] + (["dragon"] if pronto("dragon", 90) else [])
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


def fraccion_util():
    """Alto del área de trabajo de Windows / alto de pantalla (ambos de la misma API: no importa la escala de DPI); 1.0 si falla."""
    try:
        import ctypes, ctypes.wintypes
        r = ctypes.wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
            return max(0.5, min(1.0, r.bottom / ctypes.windll.user32.GetSystemMetrics(1)))  # SM_CYSCREEN
    except Exception: pass
    return 1.0


def correr(leer, seguir, x=0.22, y=6):
    """Bucle de tkinter (hilo principal). leer() -> estado de HTC; seguir() -> False para cerrar. x = fracción del ancho."""
    import tkinter as tk
    root = tk.Tk(); root.withdraw(); root.overrideredirect(True); root.attributes("-topmost", True); root.attributes("-alpha", 0.88)
    root.configure(bg=BG); fila = tk.Frame(root, bg=BG, padx=10, pady=4); fila.pack()
    root.update_idletasks(); atravesable(root); visible = [False]

    def tick():
        if not seguir(): root.destroy(); return
        s = leer() or {}
        encendido = (s.get("ajustes") or {}).get("overlay", True)  # Ajustes_Vino: «Siempre encima en partida»
        aj = s.get("ajustes") or {}
        ps = partes(s.get("meta"), time.time(), aj) if s.get("fase") == "InProgress" and encendido else []
        for w in fila.winfo_children(): w.destroy()
        for i, (t, c) in enumerate(ps):
            if i: tk.Label(fila, text="·", fg="#7A5A68", bg=BG, font=("Segoe UI", 11)).pack(side="left", padx=4)
            tk.Label(fila, text=t, fg=c, bg=BG, font=("Segoe UI Semibold", 11)).pack(side="left")
        if ps:  # se recoloca cada segundo: cambiar «franja_pos» en partida mueve la franja al instante
            root.update_idletasks()
            root.geometry(f"+{int(root.winfo_screenwidth() * x)}+{pos_y(aj.get('franja_pos'), root.winfo_screenheight(), root.winfo_reqheight(), y, fraccion_util())}")
            if not visible[0]: root.deiconify(); root.attributes("-topmost", True); visible[0] = True
        elif visible[0]: root.withdraw(); visible[0] = False
        root.after(1000, tick)

    tick(); root.mainloop()
