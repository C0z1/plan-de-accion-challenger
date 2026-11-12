"""Ventana de Racha sin barra de título (pedido del usuario; opción B de DeepSeek, probada en Windows 11): la app sigue
siendo una ventana de Edge --app, y aquí se le quita la barra de Windows con ctypes conservando el borde para
redimensionar. Los botones y el arrastre los dibuja la página (Ventana_Vino) y llegan por POST /api/ventana.
Todo es «si se puede»: fuera de Windows, o si no aparece la ventana, Racha queda con la barra normal."""
import time

HWND = [None]  # la ventana de Racha ya sin barra, o None
ARRIBA = [0]  # alto en px físicos de la barra de Edge con la ventana normal (lo que se recorta)
MAXI = {}  # hwnd -> (rect normal, borde lado, borde abajo, rect maximizado): maximizada «a mano»
CLASE_EDGE = "Chrome_WidgetWin_1"
ACCIONES = ("minimizar", "maximizar", "cerrar", "arrastrar", "recortar")


def _win():
    """(user32, wintypes) o None fuera de Windows."""
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
    except (ImportError, AttributeError, OSError): return None
    u.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    u.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    u.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    u.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    return ctypes, wintypes, u


WS_CAPTION = 0x00C00000


def es_racha(u, ctypes, h, titulo="Racha"):
    """¿h es una ventana visible de Edge cuyo título es exactamente `titulo`?"""
    n = u.GetWindowTextLengthW(h)
    if not n or not u.IsWindowVisible(h): return False
    t = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, t, n + 1)
    c = ctypes.create_unicode_buffer(64); u.GetClassNameW(h, c, 64)
    return t.value == titulo and c.value == CLASE_EDGE


def buscar(titulo="Racha", con_barra=False):
    """HWND visible de la ventana de Edge cuyo título es exactamente `titulo`, o None. con_barra: solo una que aún tenga la
    barra de Windows, es decir, la recién abierta (si Racha se abre dos veces, la primera ya no la tiene: lo vio el usuario)."""
    w = _win()
    if not w: return None
    ctypes, wintypes, u = w
    hallada = []
    def cb(h, _):
        if es_racha(u, ctypes, h, titulo) and (not con_barra or u.GetWindowLongPtrW(h, -16) & WS_CAPTION): hallada.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return hallada[0] if hallada else None


def al_frente(titulo="Racha"):
    """Si ya hay una ventana de Racha, la restaura y la trae al frente: True. Si no, False (hay que abrir una)."""
    w = _win()
    if not w or not (h := buscar(titulo)): return False
    u = w[2]
    if u.IsIconic(h): u.ShowWindow(h, 9)
    u.SetForegroundWindow(h)  # Windows puede negarlo si otro programa tiene el foco: la ventana igual queda restaurada
    return True


def sin_marco(segundos=15, al_listo=None):
    """Espera a que Edge abra la ventana de Racha y le quita la barra de título (deja WS_THICKFRAME: se redimensiona)."""
    w = _win()
    if not w: return
    _, _, u = w
    fin = time.time() + segundos
    while time.time() < fin and not (h := buscar(con_barra=True)): time.sleep(0.3)
    if not h: return
    GWL_STYLE = -16
    u.SetWindowLongPtrW(h, GWL_STYLE, u.GetWindowLongPtrW(h, GWL_STYLE) & ~WS_CAPTION)
    u.SetWindowPos(h, 0, 0, 0, 0, 0, 0x0027)  # NOMOVE | NOSIZE | NOZORDER | FRAMECHANGED
    HWND[0] = h
    if al_listo: al_listo()


def recortar(alto_css, dpr):
    """Edge dibuja su propia barra dentro de la ventana (quitar WS_CAPTION no basta: lo vio el usuario). La página mide
    cuánto ocupa (outerHeight - innerHeight, en px CSS) y aquí se recorta esa franja de arriba con una región."""
    w = _win()
    if not w or not (0 < alto_css <= 80) or not (0.5 <= dpr <= 4): return False
    ctypes, wintypes, u = w
    h = objetivo(u, ctypes)
    if not h: return False
    try:  # Edge extiende el marco de DWM dentro de la ventana para su barra (con efecto vidrio) y esa zona ignora la
        # región: sin esto queda una franja blanca vacía (probado en la PC del usuario, Windows 11)
        class MARGINS(ctypes.Structure): _fields_ = [("l", ctypes.c_int), ("r", ctypes.c_int), ("t", ctypes.c_int), ("b", ctypes.c_int)]
        d = ctypes.windll.dwmapi; d.DwmExtendFrameIntoClientArea(h, ctypes.byref(MARGINS(0, 0, 0, 0)))
        ninguno = ctypes.c_int(1); d.DwmSetWindowAttribute(h, 38, ctypes.byref(ninguno), 4)  # DWMWA_SYSTEMBACKDROP_TYPE = sin vidrio
        # sin el marco que Windows 11 dibuja sobre el rectángulo completo (se veía como un contorno y una línea encima de la
        # región recortada; lo vio el usuario): sin color de borde, sin esquinas redondeadas y sin dibujo de marco
        for attr, valor in ((34, ctypes.c_uint(0xFFFFFFFE)), (33, ctypes.c_int(1)), (2, ctypes.c_int(1))):
            d.DwmSetWindowAttribute(h, attr, ctypes.byref(valor), 4)
    except (AttributeError, OSError): pass
    r = wintypes.RECT(); u.GetWindowRect(h, ctypes.byref(r))
    arriba = round(alto_css * dpr)
    if u.IsZoomed(h):  # maximizada por Windows (Win+↑, doble clic en el borde, snap): pasarla a la maximizada a mano
        if ARRIBA[0]: maximizar(u, ctypes, wintypes, h)
        return True
    ARRIBA[0] = arriba
    m = MAXI.get(h)
    if m and (r.left, r.top, r.right, r.bottom) != m[3]: MAXI.pop(h); m = None  # la movieron o la achicaron: ya no está maximizada
    caja = (m[1], arriba, r.right - r.left - m[1], r.bottom - r.top - m[2]) if m else (0, arriba, r.right - r.left, r.bottom - r.top)
    rgn = ctypes.windll.gdi32.CreateRectRgn(*caja)  # maximizada, sin los bordes invisibles: no asoman en el otro monitor
    u.SetWindowRgn(h, rgn, True)  # Windows se queda con la región: no se libera aquí
    return True


def caja_max(trabajo, lado, arriba, abajo):
    """(x, y, ancho, alto) de la ventana para que, recortada, la página llene justo el área de trabajo del monitor: la barra
    de Edge queda arriba, fuera de la pantalla. Con ShowWindow(3) Windows deja la barra de Edge dentro de la pantalla y
    asoma encima de la nuestra (lo vio el usuario al maximizar, 2026-11-12)."""
    izq, sup, der, inf = trabajo
    return izq - lado, sup - arriba, der - izq + 2 * lado, inf - sup + arriba + abajo


def maximizar(u, ctypes, wintypes, h):
    """Alterna entre la ventana normal y la maximizada a mano (ver caja_max)."""
    if h in MAXI:
        a = MAXI.pop(h)[0]; u.SetWindowPos(h, 0, a[0], a[1], a[2] - a[0], a[3] - a[1], 0x0014); return  # NOZORDER | NOACTIVATE
    if u.IsZoomed(h): u.ShowWindow(h, 9)
    r, c, o = wintypes.RECT(), wintypes.RECT(), wintypes.POINT(0, 0)
    u.GetWindowRect(h, ctypes.byref(r)); u.GetClientRect(h, ctypes.byref(c)); u.ClientToScreen(h, ctypes.byref(o))
    lado, abajo = o.x - r.left, (r.bottom - o.y) - c.bottom  # bordes invisibles de redimensionar (arriba no tiene)
    class MI(ctypes.Structure): _fields_ = [("cb", wintypes.DWORD), ("mon", wintypes.RECT), ("trab", wintypes.RECT), ("f", wintypes.DWORD)]
    mi = MI(); mi.cb = ctypes.sizeof(MI)
    if not u.GetMonitorInfoW(u.MonitorFromWindow(h, 2), ctypes.byref(mi)): return
    t = mi.trab
    x, y, an, al = caja_max((t.left, t.top, t.right, t.bottom), lado, ARRIBA[0], abajo)
    normal = (r.left, r.top, r.right, r.bottom)
    if normal == (x, y, x + an, y + al):  # Edge abrió la ventana con el tamaño de maximizada (se cerró así): restaurar a una centrada
        an2, al2 = min(1280, (t.right - t.left) * 7 // 10), (t.bottom - t.top) * 9 // 10
        cx, cy = t.left + (t.right - t.left - an2) // 2, t.top + (t.bottom - t.top - al2) // 2
        u.SetWindowPos(h, 0, cx, cy, an2, al2, 0x0014); return
    MAXI[h] = (normal, lado, abajo, (x, y, x + an, y + al))
    u.SetWindowPos(h, 0, x, y, an, al, 0x0014)


def objetivo(u, ctypes):
    """La ventana de Racha a la que van los botones: la que está al frente (la del clic, aunque haya dos abiertas); si no,
    la última que se dejó sin barra, si sigue existiendo."""
    f = u.GetForegroundWindow()
    if f and es_racha(u, ctypes, f): HWND[0] = f; return f
    return HWND[0] if HWND[0] and u.IsWindow(HWND[0]) else None


def accion(nombre, alto=0, dpr=1):
    """minimizar / maximizar (alterna) / cerrar / arrastrar (sigue al mouse mientras el botón izquierdo esté apretado)."""
    if nombre not in ACCIONES: raise ValueError(nombre)
    w = _win()
    if not w: return False
    ctypes, wintypes, u = w
    if nombre == "recortar": return recortar(alto, dpr)
    h = objetivo(u, ctypes)
    if not h: return False
    if nombre == "minimizar": u.ShowWindow(h, 6)
    elif nombre == "maximizar":
        if ARRIBA[0]: maximizar(u, ctypes, wintypes, h)
        else: u.ShowWindow(h, 9 if u.IsZoomed(h) else 3)  # sin recorte medido todavía (o con la barra de Windows): la de siempre
    elif nombre == "cerrar": u.PostMessageW(h, 0x0010, 0, 0)
    else:
        if u.IsZoomed(h) or h in MAXI: return True  # maximizada no se arrastra
        p, r = wintypes.POINT(), wintypes.RECT()
        u.GetCursorPos(ctypes.byref(p)); u.GetWindowRect(h, ctypes.byref(r))
        dx, dy, ancho, alto = p.x - r.left, p.y - r.top, r.right - r.left, r.bottom - r.top
        fin = time.time() + 30
        while u.GetAsyncKeyState(0x01) & 0x8000 and time.time() < fin:  # botón izquierdo apretado
            u.GetCursorPos(ctypes.byref(p)); u.MoveWindow(h, p.x - dx, p.y - dy, ancho, alto, True); time.sleep(0.01)
    return True
