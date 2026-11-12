"""Ventana de Racha: una ventana normal de Edge --app con perfil propio (datos/edge). Reescrita desde cero el 2026-11-12
(plan de Fable): sin quitarle el marco ni recortarla, que fallaba en PCs ajenas (doble barra, franjas, ventanas huérfanas).
- La barra es la de Windows, oscura con --force-dark-mode (probado en la PC del usuario).
- El proceso de Edge es nuestro: lo encontramos por PID (no por título) y vive en un Job Object que lo mata cuando
  Racha termina por cualquier motivo (salida, taskkill del instalador, actualización): nunca queda una ventana huérfana.
Todo es «si se puede»: fuera de Windows o sin Edge, abrir() devuelve False y Racha usa el navegador."""
import pathlib, shutil, subprocess, threading

PROC = [None]  # el msedge.exe que lanzamos
JOB = [None]  # handle del Job Object (se cierra solo al morir Racha, y con él Edge)
LOCK = threading.Lock()  # abrir a mano y champ select a la vez: una sola ventana
EDGES = (pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
         pathlib.Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"))


def edge():
    return shutil.which("msedge") or next((str(p) for p in EDGES if p.exists()), None)


def _win():
    """(ctypes, wintypes, user32, kernel32) o None fuera de Windows."""
    try:
        import ctypes
        from ctypes import wintypes
        return ctypes, wintypes, ctypes.windll.user32, ctypes.windll.kernel32
    except (ImportError, AttributeError, OSError): return None


def viva():
    return PROC[0] is not None and PROC[0].poll() is None


def ventanas(pid):
    """Ventanas visibles de nivel superior de ese proceso."""
    w = _win()
    if not w: return []
    ctypes, wintypes, u, _ = w
    hallada = []
    def cb(h, _):
        p = wintypes.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u.IsWindowVisible(h) and not u.GetWindow(h, 4): hallada.append(h)  # 4 = GW_OWNER: sin dueño
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return hallada


def al_frente():
    """Restaura y trae al frente nuestra ventana. False si no hay."""
    w = _win()
    if not w or not viva() or not (hs := ventanas(PROC[0].pid)): return False
    u = w[2]
    if u.IsIconic(hs[0]): u.ShowWindow(hs[0], 9)
    u.SetForegroundWindow(hs[0])  # Windows puede negarlo si otro programa tiene el foco: igual queda restaurada
    return True


def _al_job(pid):
    """Mete el proceso de Edge en un Job con KILL_ON_JOB_CLOSE: si Racha muere, Edge también."""
    w = _win()
    if not w: return
    ctypes, wintypes, _, k = w
    class BASICA(ctypes.Structure): _fields_ = [("t1", ctypes.c_int64), ("t2", ctypes.c_int64), ("flags", wintypes.DWORD), ("a", ctypes.c_size_t),
                                                ("b", ctypes.c_size_t), ("c", wintypes.DWORD), ("d", ctypes.c_size_t), ("e", wintypes.DWORD), ("f", wintypes.DWORD)]
    class EXT(ctypes.Structure): _fields_ = [("basica", BASICA), ("io", ctypes.c_uint64 * 6), ("m", ctypes.c_size_t * 4)]
    k.CreateJobObjectW.restype = k.OpenProcess.restype = wintypes.HANDLE
    if not JOB[0]:
        e = EXT(); e.basica.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        j = k.CreateJobObjectW(None, None)
        if not j or not k.SetInformationJobObject(j, 9, ctypes.byref(e), ctypes.sizeof(e)): return
        JOB[0] = j
    if (hp := k.OpenProcess(0x0101, False, pid)):  # PROCESS_SET_QUOTA | PROCESS_TERMINATE
        k.AssignProcessToJobObject(JOB[0], hp); k.CloseHandle(hp)


def abrir(url, perfil):
    """Trae al frente la ventana de Racha o abre una (perfil propio: aparte del Edge del usuario). False sin Edge."""
    with LOCK:
        if al_frente(): return True
        if not (e := edge()): return False
        PROC[0] = subprocess.Popen([e, f"--app={url}", f"--user-data-dir={perfil}", "--force-dark-mode", "--disable-features=Translate,msEdgeTranslate", "--lang=es", "--window-size=1440,1024",
                                    "--no-first-run", "--no-default-browser-check"])
        _al_job(PROC[0].pid)
        return True


def cerrar():
    if viva():
        try: PROC[0].terminate()
        except OSError: pass


def limpiar_viejas():
    """Migración desde 0.14–0.16: cierra las ventanas «Racha» de Edge sin barra de título (las que esas versiones dejaban
    sin marco). Una ventana normal de Edge siempre tiene WS_CAPTION, así que no toca las del usuario. Cuántas cerró."""
    w = _win()
    if not w: return 0
    ctypes, wintypes, u, _ = w
    u.GetWindowLongPtrW.restype = ctypes.c_ssize_t; u.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    viejas = []
    def cb(h, _):
        n = u.GetWindowTextLengthW(h); t = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(h, t, n + 1)
        c = ctypes.create_unicode_buffer(64); u.GetClassNameW(h, c, 64)
        if t.value == "Racha" and c.value == "Chrome_WidgetWin_1" and u.IsWindowVisible(h) and not u.GetWindowLongPtrW(h, -16) & 0x00C00000:
            viejas.append(h)
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    for h in viejas: u.PostMessageW(h, 0x0010, 0, 0)  # WM_CLOSE
    return len(viejas)
