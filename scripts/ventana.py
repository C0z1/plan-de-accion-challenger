"""Ventana de Racha sin barra de título (pedido del usuario; opción B de DeepSeek, probada en Windows 11): la app sigue
siendo una ventana de Edge --app, y aquí se le quita la barra de Windows con ctypes conservando el borde para
redimensionar. Los botones y el arrastre los dibuja la página (Ventana_Vino) y llegan por POST /api/ventana.
Todo es «si se puede»: fuera de Windows, o si no aparece la ventana, Racha queda con la barra normal."""
import time

HWND = [None]  # la ventana de Racha ya sin barra, o None
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
    rgn = ctypes.windll.gdi32.CreateRectRgn(0, arriba, r.right - r.left, r.bottom - r.top)
    u.SetWindowRgn(h, rgn, True)  # Windows se queda con la región: no se libera aquí
    return True


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
    elif nombre == "maximizar": u.ShowWindow(h, 9 if u.IsZoomed(h) else 3)
    elif nombre == "cerrar": u.PostMessageW(h, 0x0010, 0, 0)
    else:
        if u.IsZoomed(h): return True  # maximizada no se arrastra
        p, r = wintypes.POINT(), wintypes.RECT()
        u.GetCursorPos(ctypes.byref(p)); u.GetWindowRect(h, ctypes.byref(r))
        dx, dy, ancho, alto = p.x - r.left, p.y - r.top, r.right - r.left, r.bottom - r.top
        fin = time.time() + 30
        while u.GetAsyncKeyState(0x01) & 0x8000 and time.time() < fin:  # botón izquierdo apretado
            u.GetCursorPos(ctypes.byref(p)); u.MoveWindow(h, p.x - dx, p.y - dy, ancho, alto, True); time.sleep(0.01)
    return True
