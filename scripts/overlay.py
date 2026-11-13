"""Overlay en partida (0.17): una pastilla de 380×72 siempre encima, del lienzo «Base LOL» (plan de Fable y DeepSeek):
nivel y farm hasta el 14, muertes y peleas del 14 al 25, KDA después, y el aviso corto 8 s.
Solo lee el estado de HTC (que a su vez solo lee la Live Client Data): no inyecta nada en el juego. Los clics la
atraviesan (WS_EX_TRANSPARENT) y no roba el foco. Se ve con LoL en «sin bordes» (el modo por defecto), no en pantalla
completa exclusiva. tkinter + ctypes + Pillow (dibujo a imagen y UpdateLayeredWindow: alfa por píxel)."""
import time

import io, pathlib

# Paleta Vino del lienzo «Base LOL» (Overlay_Vino), en rgb
ROSA, ROSA2, ROSA3, ROJO, ROJO2 = (242, 141, 176), (248, 195, 214), (163, 58, 99), (255, 138, 138), (154, 46, 58)
SALVIA, ORO, TXT, ETQ = (168, 216, 192), (242, 196, 107), (242, 244, 247), (174, 149, 160)
COLORES = {"rosa": (ROSA2, ROSA3), "rojo": (ROJO, ROJO2), "salvia": (SALVIA, (62, 122, 98)), "oro": (ORO, (156, 106, 28)), "gris": (ETQ, (90, 70, 80))}
AVISO_SEGUNDOS = 8  # el aviso corto ocupa la pastilla 8 s (plan del overlay; antes 12 en la franja de texto)
LINEA_HASTA, PELEAS_HASTA = 840, 1500  # s de juego: 0–14 nivel y farm; 14–25 muertes y peleas; después KDA
CHIP_MAX = 10  # caracteres que caben en el chip junto a los dos medallones


def ritmo(cs_meta, t):
    """CS esperado a los t s si cs_meta es tu meta de CS al minuto 10 (los minions llegan a la línea ~1:15)."""
    return cs_meta * max(0, t - 75) / 525


IGUALO_S, ORO14_S = 3, 5  # fase 2 del plan: cuánto duran «Igualaste» y la moneda del 14
MUERTE_ESPERA, COMPRA_S, ITEM_DESDE = 6, 8, 90  # ÍTEM (PLAN-OVERLAY-2): 6 s tras morir, 8 s tras comprar, nunca antes de 1:30


def marcar(m, meta, ahora):
    """Memoria entre fotos para los momentos de la fase 2 (estado() es pura): igualar a tu rival en nivel y cruzar el 14.
    m: dict que vive en correr(); se vacía solo si empieza otra partida (el reloj de juego baja)."""
    if not meta or meta.get("modo") == "ARAM": return m
    t = meta.get("t") or 0
    if t < m.get("t", 0) - 30: m.clear()  # otra partida (30 s de margen por el temblor al reconectar)
    m["t"] = t
    nv, nvr = meta.get("nivel"), meta.get("nivel_rival")
    if meta.get("rival") != m.get("rival"): m["rival"] = meta.get("rival"); m.pop("d", None)  # otro rival de línea: sin «Igualaste» falso (DeepSeek)
    if nv is not None and nvr is not None:
        if m.get("d", 0) < 0 <= nv - nvr and meta.get("rival"): m["igualo"] = ahora
        m["d"] = nv - nvr
    muerto, items = bool(meta.get("muerto")), [str(i[0]) for i in meta.get("items") or []]
    if muerto and not m.get("muerto"): m["muerte"] = ahora
    if not muerto: m.pop("muerte", None)
    if "items" in m and items != m["items"]: m["compra"] = ahora  # cambió tu inventario: solo pasa en la tienda o muerto
    m["muerto"], m["items"] = muerto, items
    oro = meta.get("oro") or {}
    if t >= LINEA_HASTA and "oro14" not in m: m["oro14"] = (ahora, oro["tu"] - oro["rival"]) if oro.get("tu") is not None and oro.get("rival") is not None else None
    return m


def estado(meta, ahora, aj=None, regla=None, aviso=None, marcas=None, racha_oro=None):
    """Qué muestra la pastilla (plan del overlay de Fable con la revisión de DeepSeek), o None. Solo datos y tu regla,
    nunca órdenes (Riot: no dictar decisiones). Huecos: a (tu medallón), rival (opcional), b (anillo + número), chip."""
    if not meta: return None
    aj = aj or {}; on = lambda k: aj.get(k, True) is not False
    t = meta["t"] if meta.get("t") is not None else (meta.get("minuto") or 0) * 60
    camp = meta.get("campeon")
    if aviso and aviso.get("franja") is not None and aviso.get("corto") and ahora - aviso["franja"] < AVISO_SEGUNDOS:
        return {"tipo": "aviso", "a": {"campeon": camp, "anillo": 1.0, "color": "rojo", "insignia": None, "atenuado": True},
                "texto": aviso["corto"], "chip": None}
    mk = marcas or {}
    if (o := mk.get("oro14")) and ahora - o[0] < ORO14_S and meta.get("modo") != "ARAM":  # la moneda del 14 (fase 2)
        dif = round(o[1] / 50) * 50; r = racha_oro or {}
        return {"tipo": "oro14", "a": {"campeon": camp, "anillo": 1.0, "color": "oro", "insignia": "14"},
                "num": f"{dif:+d}", "etq": "oro en ítems vs rival", "moneda": True,
                "b": {"icono": None, "color": "oro", "num": f"{r['ok']} / {r['n']}", "etq": "racha de oro"} if r.get("n") else None,
                "chip": ("Arriba", "salvia") if dif >= 0 else ("Abajo", "rojo")}
    if mk.get("igualo") is not None and ahora - mk["igualo"] < IGUALO_S and meta.get("rival") and meta.get("nivel") is not None:  # «Igualaste» (fase 2)
        return {"tipo": "igualaste", "a": {"campeon": camp, "anillo": 1.0, "color": "salvia", "insignia": meta["nivel"]},
                "rival": {"campeon": meta["rival"], "anillo": 1.0, "color": "gris", "insignia": meta.get("nivel_rival")},
                "flecha": {"txt": "=", "color": "salvia"}, "b": {"icono": None, "color": "salvia", "num": "Igualaste", "etq": f"nivel {meta['nivel']}"},
                "chip": ("Igualado", "salvia")}  # dato, no consejo (DeepSeek)
    p, t0 = meta.get("proximo"), meta.get("t") or 0
    if p and t0 >= ITEM_DESDE and on_aj(aj, "franja_build") and ((mk.get("muerte") is not None and ahora - mk["muerte"] >= MUERTE_ESPERA)
                                                                or (mk.get("compra") is not None and ahora - mk["compra"] < COMPRA_S)):
        return {"tipo": "item", "a": {"item": p["id"], "campeon": p["nombre"], "anillo": p["i"] / p["de"], "color": "oro", "insignia": f"{p['i']}/{p['de']}"},
                "num": p["nombre"][:16].rstrip(), "etq": "build OTPs" if p.get("fuente") == "mejores" else "tu build",
                "b": {"icono": None, "color": "oro", "num": f"{p['falta']:,}".replace(",", " "), "etq": "oro que falta"}, "chip": None}  # dato: nunca «compra»
    if meta.get("modo") == "ARAM":
        tu, ellos = meta.get("kills") or [0, 0]
        return {"tipo": "aram", "a": {"campeon": camp, "anillo": 1.0, "color": "rosa", "insignia": meta.get("nivel")},
                "num": f"{tu} – {ellos}", "etq": "kills", "b": {"icono": None, "color": "rosa", "num": meta.get("kda") or "", "etq": "KDA"}, "chip": None}
    nv, nvr, rival = meta.get("nivel"), meta.get("nivel_rival"), meta.get("rival")
    if t < LINEA_HASTA and on("franja_linea"):
        a = {"campeon": camp, "anillo": min(nv or 0, 6) / 6, "color": "rosa", "insignia": nv}  # hacia tu regla del nivel 6 (la API no trae XP)
        dif_nv = (nv - nvr) if nv is not None and nvr is not None else None
        riv = flecha = None
        if dif_nv is not None and rival:
            riv = {"campeon": rival, "anillo": min(nvr, 6) / 6, "color": "rojo" if dif_nv < 0 else "gris", "insignia": nvr}
            flecha = {"txt": f"{dif_nv:+d}" if dif_nv else "=", "color": "rojo" if dif_nv < 0 else "salvia" if dif_nv > 0 else "gris"}
        cs, meta10, rcs = meta.get("cs"), meta.get("cs_meta"), meta.get("rival_cs")
        b, bajo = {"icono": "minion", "anillo": None, "color": "rosa", "num": str(cs if cs is not None else "—"), "etq": "CS"}, None
        if cs is not None and meta10 and t < 600:
            obj = ritmo(meta10, t)  # el umbral va sobre el flotante, no sobre el redondeo (DeepSeek)
            col = "salvia" if cs >= obj else "oro" if cs >= .85 * obj else "rojo"
            b.update(anillo=min(1.0, cs / obj) if obj else 1.0, color=col, etq=f"ritmo {round(obj)}"); bajo = col != "salvia"
        elif cs is not None and rcs is not None:
            dcs = cs - rcs
            b.update(num=f"{dcs:+d}", color="rojo" if dcs <= -10 else "salvia" if dcs >= 0 else "oro", etq="CS vs rival"); bajo = dcs < 0
        if riv and dif_nv < 0: chip = ("Nivel " + flecha["txt"], "rojo")
        elif bajo: chip = ("Bajo ritmo" if b["etq"].startswith("ritmo") else "CS abajo", "oro")
        elif bajo is False or (riv and dif_nv >= 0): chip = ("Vas bien", "salvia")
        else: chip = None
        return {"tipo": "linea", "a": a, "rival": riv, "flecha": flecha, "b": b, "chip": chip}
    m14, tope = meta.get("muertes14"), max(1, int((regla or {}).get("tope", 2)))
    part = meta.get("participacion")
    bpart = {"icono": "espadas", "anillo": part, "color": "rosa", "num": f"{round(part * 100)}%" if part is not None else "—", "etq": "en kills"}
    if LINEA_HASTA <= t < PELEAS_HASTA and m14 is not None and on("franja_regla"):  # siempre, aunque tu regla de hoy sea otra (decisión del usuario)
        col = "salvia" if m14 < tope else "oro" if m14 == tope else "rojo"
        return {"tipo": "peleas", "a": {"campeon": camp, "tramos": min(tope, 5), "apagados": min(m14, tope, 5), "color": "rojo" if m14 >= tope else "rosa",
                                         "insignia": f"{m14}/{tope}", "atenuado": m14 > tope},
                "num": f"{m14} / {tope}", "etq": "muertes", "b": bpart,
                "chip": ("Vas bien" if m14 < tope else "En tu tope" if m14 == tope else "Sobre tope", col)}
    oro = meta.get("oro") or {}
    eq = round((oro["equipo"] - oro["equipo_rival"]) / 50) * 50 if oro.get("equipo") is not None and oro.get("equipo_rival") is not None else None
    return {"tipo": "tarde", "a": {"campeon": camp, "anillo": 1.0, "color": "rosa", "insignia": nv}, "num": meta.get("kda") or "", "etq": "KDA",
            "b": bpart, "chip": (f"Eq {eq:+d}"[:CHIP_MAX], "salvia" if eq >= 0 else "rojo") if eq is not None else None}


def on_aj(aj, k): return (aj or {}).get(k, True) is not False


def textos(e):
    """Los textos de la pastilla en orden de lectura: para replay (lista negra) y salud."""
    if not e: return []
    b = e.get("b") or {}
    out = [e.get("texto"), e.get("num"), e.get("etq"), (e.get("flecha") or {}).get("txt"), b.get("num"), b.get("etq"), (e.get("chip") or (None,))[0]]
    return [str(x) for x in out if x not in (None, "")]


FUENTE = pathlib.Path(r"C:\Windows\Fonts\segoeuib.ttf")
_CACHE = {}


def _fuente(px):
    from PIL import ImageFont
    if ("f", px) not in _CACHE:
        try: _CACHE[("f", px)] = ImageFont.truetype(str(FUENTE), px)
        except OSError: _CACHE[("f", px)] = ImageFont.load_default(px)  # fuera de Windows (CI en Ubuntu)
    return _CACHE[("f", px)]


def _png(icono, tipo, nombre, px):
    """PNG de icono(tipo, nombre) -> bytes, a px×px; None si no hay."""
    from PIL import Image
    try:
        b = icono(tipo, nombre) if icono and nombre else None
        return Image.open(io.BytesIO(b)).convert("RGBA").resize((px, px), Image.LANCZOS) if b else None
    except Exception: return None


def _retrato(nombre, px, icono, apagado=False, item=None):
    """Retrato circular del campeón, en caché; sin imagen, un círculo con la inicial. apagado: gris y más oscuro."""
    from PIL import Image, ImageDraw, ImageOps
    k = ("r", item or nombre, px, apagado)
    if k in _CACHE: return _CACHE[k]
    im = _png(icono, "item", item, px) if item else _png(icono, "champion", nombre, px)
    if im is None:
        im = Image.new("RGBA", (px, px), ROSA3 + (255,))
        ImageDraw.Draw(im).text((px / 2, px / 2), (nombre or "?")[:1], font=_fuente(int(px * .5)), fill=TXT + (255,), anchor="mm")
    if apagado: im = ImageOps.grayscale(im).point(lambda v: int(v * .7)).convert("RGBA")
    mask = Image.new("L", (px, px), 0); ImageDraw.Draw(mask).ellipse((0, 0, px - 1, px - 1), fill=255)
    im.putalpha(mask); _CACHE[k] = im
    return im


def pintar(e, esc=1.0, icono=None):
    """La pastilla (RGBA de 380×72 por esc) para el estado e. Dibujo a 2× y reducción: bordes suaves."""
    from PIL import Image, ImageDraw
    S = 2; W, H = round(380 * esc), round(72 * esc); k = lambda v: round(v * esc * S)
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    alarma = e["tipo"] == "aviso" or (e["tipo"] == "peleas" and e["chip"][1] == "rojo")
    momento = {"igualaste": SALVIA, "oro14": ORO}.get(e["tipo"])  # fase 2: borde del color del momento
    d.rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=k(16), fill=(60, 14, 26, 240) if alarma else (11, 7, 9, 214),
                        outline=ROJO + (255,) if alarma else momento + (255,) if momento else ROSA + (90,),
                        width=k(3.5) if e.get("pulso") else k(2) if alarma or momento else max(1, k(1)))  # pulso: el borde engorda un instante
    f17, f11 = _fuente(k(17)), _fuente(k(11))

    def anillo(cx, r, frac, col, ancho=3):
        d.ellipse((cx - r, k(36) - r, cx + r, k(36) + r), outline=(255, 255, 255, 26), width=k(ancho))
        if frac: d.arc((cx - r, k(36) - r, cx + r, k(36) + r), -90, -90 + 360 * max(0.0, min(1.0, frac)), fill=col + (255,), width=k(ancho))

    def medallon(x, m):
        cx, r = k(x + 22), k(17); c1 = COLORES.get(m.get("color"), COLORES["rosa"])[0]
        if m.get("tramos"):  # muertes: anillo partido en tramos; cada muerte apaga uno
            d.ellipse((cx - r, k(36) - r, cx + r, k(36) + r), outline=(255, 255, 255, 20), width=k(3))
            n = m["tramos"]; paso = 360 / n
            for i in range(n):
                d.arc((cx - r, k(36) - r, cx + r, k(36) + r), -90 + i * paso + 6, -90 + (i + 1) * paso - 6,
                      fill=ROJO + (217,) if i >= n - m.get("apagados", 0) else ROSA2 + (255,), width=k(3.5))
        else: anillo(cx, r, m.get("anillo"), c1)
        im.alpha_composite(_retrato(m.get("campeon"), k(28), icono, m.get("atenuado"), m.get("item")), (cx - k(14), k(36) - k(14)))
        if m.get("insignia") is not None:
            t = str(m["insignia"]); f = _fuente(k(10)); w = max(k(18), d.textlength(t, font=f) + k(8))
            d.rounded_rectangle((cx - w / 2, k(50), cx + w / 2, k(66)), radius=k(8), fill=c1 + (255,))
            d.text((cx, k(58)), t, font=f, fill=(36, 17, 26, 255), anchor="mm")
        return x + 44

    def dos(x, num, etq, col=TXT):
        d.text((k(x), k(27)), num, font=f17, fill=col + (255,), anchor="lm")
        d.text((k(x), k(47)), etq, font=f11, fill=ETQ + (255,), anchor="lm")
        return x + max(d.textlength(num, font=f17), d.textlength(etq, font=f11)) / (esc * S)

    x = medallon(14, e["a"]) + 12
    if e["tipo"] == "aviso":  # el texto corto en dos renglones como mucho
        f, lin = _fuente(k(12)), [""]
        for p in e["texto"].split():
            prueba = (lin[-1] + " " + p).strip()
            if not lin[-1] or d.textlength(prueba, font=f) <= k(380 - x - 14): lin[-1] = prueba
            elif len(lin) < 2: lin.append(p)
            else: lin[-1] += "…"; break
        for i, l in enumerate(lin): d.text((k(x), k(36 + (i - (len(lin) - 1) / 2) * 17)), l, font=f, fill=TXT + (255,), anchor="lm")
        return im.resize((W, H), Image.LANCZOS)
    if e.get("rival"):
        fl = e["flecha"]; d.text((k(x + 9), k(36)), fl["txt"], font=_fuente(k(13)), fill=COLORES[fl["color"]][0] + (255,), anchor="mm")
        x = medallon(x + 20, e["rival"]) + 12
    elif e.get("num"): x = dos(x, e["num"], e["etq"], ORO if e.get("moneda") else TXT) + 12
    if e.get("b"):
        b = e["b"]; c1 = COLORES.get(b["color"], COLORES["rosa"])[0]
        d.line((k(x), k(18), k(x), k(54)), fill=(255, 255, 255, 31), width=max(1, k(1))); x += 12
        if b.get("icono"):
            cx = k(x + 22); anillo(cx, k(19), b.get("anillo"), c1)
            ic = _png(icono, "minion", "caster", k(32)) if b["icono"] == "minion" else None
            if ic: im.alpha_composite(ic, (cx - k(16), k(36) - k(16)))
            elif b["icono"] == "espadas":
                for (x1, y1), (x2, y2) in (((-7, 7), (7, -7)), ((-7, -7), (7, 7))):
                    d.line((cx + k(x1), k(36 + y1), cx + k(x2), k(36 + y2)), fill=ROSA2 + (255,), width=k(2))
            x += 54
        x = dos(x, b["num"], b["etq"], c1 if b["etq"] == "CS vs rival" else TXT)
    if e.get("chip"):
        t, c = e["chip"]; col = COLORES[c][0]; f = _fuente(k(12)); w = d.textlength(t, font=f) + k(20)
        d.rounded_rectangle((W * S - k(14) - w, k(22), W * S - k(14), k(50)), radius=k(14), fill=col + (38,))
        d.text((W * S - k(14) - w / 2, k(36)), t, font=f, fill=col + (255,), anchor="mm")
    return im.resize((W, H), Image.LANCZOS)


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


ABAJO_X, HUD_Y = 0.30, 0.85  # «abajo»: a la derecha del chat y encima de la barra de habilidades (zonas de salud.py)
TOPE_DERECHO = 0.76  # el marcador del juego (kills, KDA, CS, reloj) empieza en ~0,78 del ancho (D9 del plan En vivo)


def colocar(juego, pantalla, alto_franja, x=0.22, pos=None, margen=6, util=1.0, ancho_franja=0):
    """(x, y) de la franja: relativa a la ventana del juego si se conoce (otro monitor, modo ventana); si no, a la pantalla
    principal sin la barra de tareas (D4). Si no cabe antes del marcador (pantallas chicas, escala alta), se corre a la izquierda."""
    if juego: x0, y0, x1, y1 = juego
    else: x0, y0, (x1, y1) = 0, 0, pantalla
    if pos == "abajo":  # abajo: a la derecha del chat (x < 0,25) y encima de la barra de habilidades (y > 0,85), sin pisar el HUD
        x, y_hud = max(x, ABAJO_X), int(y0 + (y1 - y0) * (HUD_Y if juego else min(HUD_Y, util)))
        px = max(x0 + margen, min(int(x0 + (x1 - x0) * x), int(x0 + (x1 - x0) * TOPE_DERECHO) - ancho_franja))
        return px, max(y0, y_hud - alto_franja - margen)
    px = max(x0 + margen, min(int(x0 + (x1 - x0) * x), int(x0 + (x1 - x0) * TOPE_DERECHO) - ancho_franja))
    return px, y0 + margen


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


def animar():
    """¿Windows deja animar? (Configuración > Accesibilidad > Efectos de animación; SPI_GETCLIENTAREAANIMATION). Fuera de Windows, no."""
    try:
        import ctypes
        v = ctypes.c_int(1); ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(v), 0); return bool(v.value)
    except (AttributeError, OSError): return False


SACUDIDA = (-5, 5, -3, 3, -1, 0)  # px, cada 60 ms al entrar un aviso (≈ 0,4 s; solo se mueve la ventana, sin repintar)
PULSOS = (True, False, True, False)  # borde grueso / normal cada 250 ms: dos pulsos al entrar un aviso o un momento


def escala(juego):
    """Tamaño de la pastilla según el alto del juego (1080 = 1), en pasos de 0,25 entre 0,75 y 2."""
    alto = (juego[3] - juego[1]) if juego else 1080
    return max(0.75, min(2.0, round(alto / 1080 * 4) / 4))


def bgra_premultiplicado(im):
    """Bytes BGRA con el color multiplicado por el alfa: lo que pide UpdateLayeredWindow (sin esto, halos oscuros: DeepSeek)."""
    from PIL import Image, ImageChops
    r, g, b, a = im.convert("RGBA").split()
    return Image.merge("RGBA", tuple(ImageChops.multiply(c, a) for c in (b, g, r)) + (a,)).tobytes()


def mostrar(hwnd, im, x, y):
    """Pone la imagen RGBA en la ventana en capas: DIB de 32 bits BGRA premultiplicado (sin premultiplicar salen halos,
    DeepSeek). True si Windows la aceptó."""
    import ctypes, ctypes.wintypes as w
    u, g, H = ctypes.windll.user32, ctypes.windll.gdi32, ctypes.c_void_p
    u.GetDC.restype = H; u.GetDC.argtypes = [w.HWND]; u.ReleaseDC.argtypes = [w.HWND, H]
    g.CreateCompatibleDC.restype = H; g.CreateCompatibleDC.argtypes = [H]
    g.CreateDIBSection.restype = H; g.CreateDIBSection.argtypes = [H, ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_void_p), H, w.DWORD]
    g.SelectObject.restype = H; g.SelectObject.argtypes = [H, H]; g.DeleteObject.argtypes = [H]; g.DeleteDC.argtypes = [H]
    u.UpdateLayeredWindow.argtypes = [w.HWND, H, ctypes.c_void_p, ctypes.c_void_p, H, ctypes.c_void_p, w.DWORD, ctypes.c_void_p, w.DWORD]
    class BLEND(ctypes.Structure): _fields_ = [("op", ctypes.c_byte), ("flags", ctypes.c_byte), ("alpha", ctypes.c_ubyte), ("fmt", ctypes.c_byte)]
    class BIH(ctypes.Structure): _fields_ = [("size", w.DWORD), ("w", ctypes.c_long), ("h", ctypes.c_long), ("planes", w.WORD), ("bits", w.WORD), ("comp", w.DWORD),
                                             ("isize", w.DWORD), ("xp", ctypes.c_long), ("yp", ctypes.c_long), ("used", w.DWORD), ("imp", w.DWORD)]
    W, Hh = im.size; px = bgra_premultiplicado(im)
    sdc = u.GetDC(0); mdc = g.CreateCompatibleDC(sdc); bits = ctypes.c_void_p()
    hb = g.CreateDIBSection(mdc, ctypes.byref(BIH(ctypes.sizeof(BIH), W, -Hh, 1, 32, 0, 0, 0, 0, 0, 0)), 0, ctypes.byref(bits), None, 0)
    if not hb: g.DeleteDC(mdc); u.ReleaseDC(0, sdc); return False
    ctypes.memmove(bits, px, len(px)); viejo = g.SelectObject(mdc, hb)
    ok = u.UpdateLayeredWindow(hwnd, sdc, ctypes.byref(w.POINT(x, y)), ctypes.byref(w.SIZE(W, Hh)), mdc, ctypes.byref(w.POINT(0, 0)), 0,
                               ctypes.byref(BLEND(0, 0, 255, 1)), 2)  # AC_SRC_OVER, AC_SRC_ALPHA, ULW_ALPHA
    g.SelectObject(mdc, viejo); g.DeleteObject(hb); g.DeleteDC(mdc); u.ReleaseDC(0, sdc)
    return bool(ok)


def correr(leer, seguir, x=0.22, y=6, registrar=lambda txt: None, icono=None):
    """Bucle de tkinter (hilo principal): la pastilla en una ventana en capas (alfa por píxel), siempre encima y
    atravesable. leer() -> estado de HTC; seguir() -> False para cerrar; icono(tipo, nombre) -> PNG en bytes o None.
    Solo se repinta cuando cambia lo que muestra (la foto llega cada 10 s)."""
    import tkinter as tk, traceback
    try: import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(2)  # coordenadas reales por monitor (antes de crear Tk)
    except (AttributeError, OSError): pass
    root = tk.Tk(); root.withdraw(); root.title("Racha franja"); root.overrideredirect(True); root.attributes("-topmost", True)
    root.update_idletasks(); atravesable(root)
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) if hasattr(ctypes, "windll") else None
    mostrada, ultimo, errores, marcas, tipo_ant, gen = [False], [None], set(), {}, [None], [0]

    def tick():
        if not seguir(): root.destroy(); return
        try: dibujar()
        except Exception:  # un dato raro no congela la franja el resto de la partida (revisión de DeepSeek)
            if (txt := traceback.format_exc(limit=2).strip().splitlines()[-1]) not in errores: errores.add(txt); registrar(txt)
        root.after(1000, tick)

    def dibujar():
        s = leer() or {}; ahora = time.time(); aj = s.get("ajustes") or {}
        regla = (((s.get("rendimiento") or {}).get("vistas") or {}).get("regla_hoy"))  # tu regla, no la del autor
        marcar(marcas, s.get("meta"), ahora)
        oro = (((s.get("rendimiento") or {}).get("resumen") or {}).get("racha_oro14"))
        e = estado(s.get("meta"), ahora, aj, regla, s.get("aviso"), marcas, oro) if visible(s, ahora) else None
        if not e:
            if mostrada[0]: root.withdraw(); mostrada[0] = False
            ultimo[0] = tipo_ant[0] = None; gen[0] += 1; return
        juego = rect_juego(); esc = escala(juego)
        px, py = colocar(juego, (root.winfo_screenwidth(), root.winfo_screenheight()), round(72 * esc), x, aj.get("franja_pos"), y, fraccion_util(), round(380 * esc))
        clave = (repr(e), esc, px, py)
        if clave == ultimo[0] and mostrada[0]: return  # nada cambió: no se repinta
        if not mostrada[0]: root.deiconify(); root.attributes("-topmost", True); mostrada[0] = True  # la ventana en capas solo se ve tras mostrarla
        gen[0] += 1; g = gen[0]  # los pasos de una animación vieja no pisan un estado nuevo ni una franja oculta (DeepSeek)
        img = pintar(e, esc, icono)
        if hwnd: mostrar(hwnd, img, px, py)
        if hwnd and e["tipo"] in ("aviso", "igualaste", "oro14") and e["tipo"] != tipo_ant[0] and animar():  # al entrar: sacudida (aviso) y dos pulsos
            imgs = (pintar({**e, "pulso": True}, esc, icono), img)
            vale = lambda: gen[0] == g and mostrada[0]
            for i, p in enumerate(PULSOS): root.after(250 * (i + 1), lambda p=p: vale() and mostrar(hwnd, imgs[0 if p else 1], px, py))
            if e["tipo"] == "aviso":
                for i, dx in enumerate(SACUDIDA):
                    root.after(60 * (i + 1), lambda dx=dx: vale() and ctypes.windll.user32.SetWindowPos(hwnd, 0, px + round(dx * esc), py, 0, 0, 0x15))  # NOSIZE|NOZORDER|NOACTIVATE
        tipo_ant[0] = e["tipo"]
        ultimo[0] = clave

    tick(); root.mainloop()
