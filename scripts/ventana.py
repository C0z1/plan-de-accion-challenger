"""Ventana de Racha sin barra de título (pedido del usuario; opción B de DeepSeek, probada en Windows 11): la app sigue
siendo una ventana de Edge --app, y aquí se le quita la barra de Windows con ctypes conservando el borde para
redimensionar. Los botones y el arrastre los dibuja la página (Ventana_Vino) y llegan por POST /api/ventana.
Todo es «si se puede»: fuera de Windows, o si no aparece la ventana, Racha queda con la barra normal."""
import time

HWND = [None]  # la ventana de Racha ya sin barra, o None
CLASE_EDGE = "Chrome_WidgetWin_1"
ACCIONES = ("minimizar", "maximizar", "cerrar", "arrastrar")


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


def buscar(titulo="Racha"):
    """HWND visible de la ventana de Edge cuyo título es exactamente `titulo`, o None."""
    w = _win()
    if not w: return None
    ctypes, wintypes, u = w
    hallada = []
    def cb(h, _):
        n = u.GetWindowTextLengthW(h)
        if n and u.IsWindowVisible(h):
            t = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, t, n + 1)
            c = ctypes.create_unicode_buffer(64); u.GetClassNameW(h, c, 64)
            if t.value == titulo and c.value == CLASE_EDGE: hallada.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return hallada[0] if hallada else None


def sin_marco(segundos=15, al_listo=None):
    """Espera a que Edge abra la ventana de Racha y le quita la barra de título (deja WS_THICKFRAME: se redimensiona)."""
    w = _win()
    if not w: return
    _, _, u = w
    fin = time.time() + segundos
    while time.time() < fin and not (h := buscar()): time.sleep(0.3)
    if not h: return
    GWL_STYLE, WS_CAPTION = -16, 0x00C00000
    u.SetWindowLongPtrW(h, GWL_STYLE, u.GetWindowLongPtrW(h, GWL_STYLE) & ~WS_CAPTION)
    u.SetWindowPos(h, 0, 0, 0, 0, 0, 0x0027)  # NOMOVE | NOSIZE | NOZORDER | FRAMECHANGED
    HWND[0] = h
    if al_listo: al_listo()


def accion(nombre):
    """minimizar / maximizar (alterna) / cerrar / arrastrar (sigue al mouse mientras el botón izquierdo esté apretado)."""
    if nombre not in ACCIONES: raise ValueError(nombre)
    w, h = _win(), HWND[0]
    if not w or not h: return False
    ctypes, wintypes, u = w
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
