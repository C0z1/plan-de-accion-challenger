"""Cuenta en la nube de Racha (pedido del usuario): iniciar sesión con Google y guardar tu Riot ID, tus ajustes y el
resumen de tus partidas en el backend (backend/cuenta.js). Flujo de Google para apps de escritorio: PKCE + redirect a
127.0.0.1 (el servidor local de la app); el `code` lo cambia el Worker, que es el único que tiene el secreto.
La sesión vive en datos/cache/sesion.json (fuera de git); el token es de Racha, no de Google."""
import base64, hashlib, json, pathlib, secrets, time, urllib.error, urllib.parse, urllib.request

import companion_gui as gui

SESION_F = gui.REPO / "datos" / "cache" / "sesion.json"
PENDIENTE = {}  # state → verifier del inicio en curso


def api():
    return (gui.companion.acceso(gui.REPO) or (gui.companion.API_DEF, ""))[0] or gui.companion.API_DEF


def sesion():
    """{token, email, nombre, sync} de tu sesión, o None."""
    try: d = json.loads(SESION_F.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None
    return d if isinstance(d, dict) and isinstance(d.get("token"), str) and len(d["token"]) == 64 else None


def _guardar(d):
    SESION_F.parent.mkdir(parents=True, exist_ok=True); SESION_F.write_text(json.dumps(d), encoding="utf-8")


def pedir(metodo, ruta, cuerpo=None, token=None, timeout=15):
    """JSON del backend; lanza urllib.error.HTTPError/URLError si falla."""
    h = {"Content-Type": "application/json", "User-Agent": "racha"}
    if token: h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(api() + ruta, data=None if cuerpo is None else json.dumps(cuerpo).encode(), headers=h, method=metodo)
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)


def iniciar(puerto):
    """URL de Google para iniciar sesión (abre en el navegador); None si el backend aún no tiene el cliente de Google."""
    cid = pedir("GET", "/v1/config").get("google_client_id")
    if not cid: return None
    verifier = secrets.token_urlsafe(48); state = secrets.token_urlsafe(16)
    PENDIENTE.clear(); PENDIENTE[state] = (verifier, time.time())
    reto = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    q = dict(client_id=cid, response_type="code", scope="openid email profile", redirect_uri=f"http://127.0.0.1:{puerto}/oauth",
             code_challenge=reto, code_challenge_method="S256", state=state, prompt="select_account")
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(q)


def completar(code, state, puerto):
    """Termina el inicio de sesión con lo que Google mandó a /oauth; devuelve la sesión o lanza ValueError con el motivo."""
    v = PENDIENTE.pop(state, None)
    if not v or time.time() - v[1] > 600: raise ValueError("El inicio de sesión venció: vuelve a intentarlo desde Ajustes.")
    try: d = pedir("POST", "/v1/login", {"code": code, "verifier": v[0], "redirect_uri": f"http://127.0.0.1:{puerto}/oauth"})
    except urllib.error.HTTPError as e:
        try: msg = json.load(e).get("error")
        except ValueError: msg = None
        raise ValueError(msg or "Google no aceptó el inicio de sesión.")
    s = {"token": d["token"], "email": d.get("email", ""), "nombre": d.get("nombre", ""), "sync": None}
    _guardar(s); return s


def compacto(p):
    """Resumen chico de una partida para la nube (lo que muestran Partidas y Perfil)."""
    return dict(campeon=p.get("campeon"), rival=p.get("rival"), win=p.get("win"), kda=p.get("kda"), score=p.get("score"),
                puesto_eq=p.get("puesto_eq"), fecha=p.get("fecha"))


def sincronizar(rendimiento=None, cuenta=None, region=None, ajustes=None):
    """Sube Riot ID, ajustes y el resumen de tus últimas partidas; devuelve la hora de la sincronización o None."""
    s = sesion()
    if not s: return None
    t = s["token"]
    try:
        if cuenta and region: pedir("PUT", "/v1/yo/riot", {"riot_id": cuenta, "region": region.lower().replace("lan", "la1").replace("las", "la2")}, t)
        if ajustes is not None: pedir("PUT", "/v1/yo/ajustes", ajustes, t)
        ps = ((rendimiento or {}).get("resumen") or {}).get("partidas") or []
        filas = [dict(match_id=p["archivo"], ts=p.get("t") or 0, resumen=compacto(p)) for p in ps if p.get("archivo")]
        if filas: pedir("PUT", "/v1/yo/resumenes", filas[:50], t)
    except urllib.error.HTTPError as e:
        if e.code == 401: SESION_F.unlink(missing_ok=True)  # la sesión venció o se cerró en otro lado
        return None
    except (urllib.error.URLError, OSError, ValueError): return None
    s["sync"] = time.time(); _guardar(s); return s["sync"]


def salir():
    s = sesion()
    if s:
        try: pedir("POST", "/v1/yo/salir", {}, s["token"])
        except (urllib.error.URLError, OSError, ValueError): pass
    SESION_F.unlink(missing_ok=True)


def borrar_todo():
    """«Borrar mis datos de la nube»: borra tu cuenta, sesiones y resúmenes del backend y cierra la sesión."""
    s = sesion()
    if s: pedir("DELETE", "/v1/yo", None, s["token"])
    SESION_F.unlink(missing_ok=True)
