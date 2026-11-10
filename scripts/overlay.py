"""Overlay en partida (v0.5): franja fina siempre encima con los timers de dragón y barón y tu nivel/CS contra tu rival.
Solo lee el estado de HTC (que a su vez solo lee la Live Client Data): no inyecta nada en el juego. Los clics la
atraviesan (WS_EX_TRANSPARENT) y no roba el foco. Se ve con LoL en «sin bordes» (el modo por defecto), no en pantalla
completa exclusiva. Sin dependencias: tkinter + ctypes."""
import time

BG, TXT, ROSA, AMBAR = "#1A0C13", "#F2F4F7", "#F28DB0", "#F5C26B"


def reloj(seg):
    seg = max(0, int(seg)); return f"{seg // 60}:{seg % 60:02d}"


def partes(meta, ahora):
    """[(texto, color)] de la franja, o [] sin datos. meta = ESTADO["meta"] (companion.meta_fase + «recibido»): los
    timers llegan cada 30 s; entre fotos se descuentan con el reloj local."""
    if not meta: return []
    if meta.get("modo") == "ARAM":  # sin líneas ni dragón: el marcador, la amenaza y tu KDA
        (tu, ellos), a = meta.get("kills") or [0, 0], (meta.get("amenazas") or [{}])[0]
        cuidado = [(f"Cuidado {a['campeon']} {a['kda']}", AMBAR)] if a.get("campeon") else []
        return [(f"Kills {tu} vs {ellos}", ROSA if tu < ellos else TXT)] + cuidado + [(f"Tu KDA {meta.get('kda', '')}", TXT)]
    o, edad = meta.get("objetivos") or {}, max(0.0, ahora - (meta.get("recibido") or ahora))
    out = []
    for nombre, k in (("Dragón", "dragon"), ("Barón", "baron")):
        if k not in o: continue
        if o[k] is None: out.append((f"{nombre} vivo", ROSA)); continue
        falta = o[k] - edad
        out.append((f"{nombre} {reloj(falta)}", AMBAR if falta < 60 else TXT))
    if meta.get("nivel") is not None and meta.get("nivel_rival") is not None:
        d = meta["nivel"] - meta["nivel_rival"]
        out.append((f"Nv {meta['nivel']} vs {meta['nivel_rival']}" + (f" {meta['rival']}" if meta.get("rival") else ""), ROSA if d < 0 else TXT))
    if meta.get("cs") is not None and meta.get("rival_cs") is not None:
        out.append((f"CS {meta['cs']} vs {meta['rival_cs']}", ROSA if meta["cs"] < meta["rival_cs"] else TXT))
    return out


def atravesable(root):
    """Los clics pasan al juego y la franja no aparece en la barra de tareas ni toma el foco (Windows)."""
    try:
        import ctypes
        u = ctypes.windll.user32; hwnd = u.GetParent(root.winfo_id())
        u.SetWindowLongW(hwnd, -20, u.GetWindowLongW(hwnd, -20) | 0x80000 | 0x20 | 0x80 | 0x08000000)  # LAYERED|TRANSPARENT|TOOLWINDOW|NOACTIVATE
    except (AttributeError, OSError): pass  # fuera de Windows: ventana normal


def correr(leer, seguir, x=0.22, y=6):
    """Bucle de tkinter (hilo principal). leer() -> estado de HTC; seguir() -> False para cerrar. x = fracción del ancho."""
    import tkinter as tk
    root = tk.Tk(); root.withdraw(); root.overrideredirect(True); root.attributes("-topmost", True); root.attributes("-alpha", 0.88)
    root.configure(bg=BG); fila = tk.Frame(root, bg=BG, padx=10, pady=4); fila.pack()
    root.update_idletasks(); atravesable(root); visible = [False]

    def tick():
        if not seguir(): root.destroy(); return
        s = leer() or {}
        ps = partes(s.get("meta"), time.time()) if s.get("fase") == "InProgress" else []
        for w in fila.winfo_children(): w.destroy()
        for i, (t, c) in enumerate(ps):
            if i: tk.Label(fila, text="·", fg="#7A5A68", bg=BG, font=("Segoe UI", 11)).pack(side="left", padx=4)
            tk.Label(fila, text=t, fg=c, bg=BG, font=("Segoe UI Semibold", 11)).pack(side="left")
        if ps and not visible[0]:
            root.geometry(f"+{int(root.winfo_screenwidth() * x)}+{y}"); root.deiconify(); root.attributes("-topmost", True); visible[0] = True
        elif not ps and visible[0]: root.withdraw(); visible[0] = False
        root.after(1000, tick)

    tick(); root.mainloop()
