"""Companion del cliente de LoL (solo lectura: nunca hace POST/PATCH ni actúa por el jugador).
Uso:
  python scripts/companion.py                        sondea el cliente cada 3 s
  python scripts/companion.py --fixture scripts/fixtures/champselect   una pasada con JSON de ejemplo
- ChampSelect: identifica tu posición y a tu rival (o a todos los rivales ya elegidos si no se sabe su rol)
  y corre draft.py; imprime una vez por cada cambio de rivales.
- InProgress: cada 30 s guarda una foto de la Live Client Data API (puerto 2999) en datos/vivo/<inicio>.jsonl
  y avisa una vez: del minuto 5 al 7 si vas abajo de nivel contra tu rival de línea; del 10 al 11 si vas bajo
  la meta minions10 de config.json (p. ej. Sylas 69+).
- EndOfGame/PreEndOfGame: una línea con la última foto en vivo (KDA, CS, muertes del 14 al 25; sirve sin key), espera 60 s y corre descargar.py 5 y revision.py 1 (si la key caducó, lo avisa).
Lockfile: C:\\Riot Games\\League of Legends\\lockfile (o la variable LOL_LOCKFILE)."""
import argparse, base64, http.client, json, os, pathlib, ssl, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
DIR = pathlib.Path(__file__).resolve().parent
LOCK = pathlib.Path(os.environ.get("LOL_LOCKFILE", r"C:\Riot Games\League of Legends\lockfile"))
POS = {"top": "TOP", "jungle": "JUNGLE", "middle": "MIDDLE", "bottom": "BOTTOM", "utility": "UTILITY"}
FALLAS = (OSError, ValueError, http.client.HTTPException)  # HTTPException: respuesta cortada (IncompleteRead) si el cliente se cae
SSL = ssl.create_default_context(); SSL.check_hostname = False; SSL.verify_mode = ssl.CERT_NONE  # cert propio del cliente, solo 127.0.0.1


def lcu(path):
    """GET a la API local del cliente; None si el cliente está cerrado."""
    try:
        _, _, port, pw, proto = LOCK.read_text().split(":")
        auth = base64.b64encode(f"riot:{pw}".encode()).decode()
        req = urllib.request.Request(f"{proto}://127.0.0.1:{port}{path}", headers={"Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, context=SSL, timeout=5) as r: return json.load(r)
    except FALLAS: return None  # sin lockfile o a medias, cliente cerrándose, timeout, 404 fuera de champ select


def lcu_escribir(metodo, path, cuerpo=None):
    """POST/PUT/DELETE a la API local del cliente; True si respondió 2xx. Solo la usa importar_runas (un clic del jugador)."""
    try:
        _, _, port, pw, proto = LOCK.read_text().split(":")
        auth = base64.b64encode(f"riot:{pw}".encode()).decode()
        req = urllib.request.Request(f"{proto}://127.0.0.1:{port}{path}", method=metodo, data=None if cuerpo is None else json.dumps(cuerpo).encode(),
                                     headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, context=SSL, timeout=5) as r: return 200 <= r.status < 300
    except FALLAS: return False


def importar_runas(nombre, pagina, leer=None, escribir=None):
    """Crea en el cliente la página de runas `pagina` ({primaryStyleId, subStyleId, selectedPerkIds[9]}) y la deja activa.
    Solo en selección de campeón y solo cuando el jugador pulsa el botón: Racha nunca elige, banea ni acepta por ti.
    Si la página activa es editable la reemplaza (así no se llena el límite de páginas). Devuelve (ok, mensaje)."""
    leer, escribir = leer or lcu, escribir or lcu_escribir
    ids = (pagina or {}).get("selectedPerkIds") or []
    if len(ids) != 9 or not all(isinstance(i, int) for i in ids + [pagina.get("primaryStyleId"), pagina.get("subStyleId")]):
        return False, "Esta build no trae la página completa de runas."
    if leer("/lol-gameflow/v1/gameflow-phase") != "ChampSelect": return False, "Solo se puede en la selección de campeón."
    act = leer("/lol-perks/v1/currentpage") or {}
    if act.get("isDeletable") and act.get("id") is not None: escribir("DELETE", f"/lol-perks/v1/pages/{act['id']}")
    ok = escribir("POST", "/lol-perks/v1/pages", {"name": f"Racha: {nombre}"[:25], "primaryStyleId": pagina["primaryStyleId"],
                                                 "subStyleId": pagina["subStyleId"], "selectedPerkIds": ids, "current": True})
    return (True, "Listo: la página de runas ya está en tu cliente.") if ok else (False, "El cliente no aceptó la página (¿llegaste al límite de páginas?).")


def rango(s):
    """Solo/dúo de /lol-ranked/v1/current-ranked-stats (fresco, sin key de Riot) como dict
    {tier, division, lp, wins, losses, n, wr}; division None en Master+ (la LCU da «NA»). None sin datos."""
    q = ((s or {}).get("queueMap") or {}).get("RANKED_SOLO_5x5") or next((e for e in (s or {}).get("queues") or [] if isinstance(e, dict) and e.get("queueType") == "RANKED_SOLO_5x5"), None)
    if not q or q.get("tier") in (None, "", "NONE"): return None
    v, d = q.get("wins") or 0, q.get("losses") or 0
    apex = q["tier"] in ("MASTER", "GRANDMASTER", "CHALLENGER") or q.get("division") in (None, "", "NA")
    return {"tier": q["tier"], "division": None if apex else q["division"],
            "lp": q.get("leaguePoints") or 0, "wins": v, "losses": d, "n": v + d, "wr": round(100 * v / (v + d)) if v + d else None}


# Backend de Racha (backend/worker.js en Cloudflare): con tu código de acceso, la app baja tus partidas sin RIOT_KEY.
# Se fija al desplegar; RACHA_API (entorno) o "api" en datos/cache/acceso.json lo cambian.
API_DEF = "https://racha-api.racha-api.workers.dev"


def acceso(base=None):
    """(api, token) para el backend de Racha, o None. Token: RACHA_TOKEN o datos/cache/acceso.json (lo guarda Ajustes)."""
    f = pathlib.Path(base or DIR.parent) / "datos" / "cache" / "acceso.json"
    try: d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError): d = {}
    api = (os.environ.get("RACHA_API") or d.get("api") or API_DEF).rstrip("/")
    token = os.environ.get("RACHA_TOKEN") or d.get("token")
    if not token:  # sin código: la sesión de Google (datos/cache/sesion.json), que el backend acepta igual
        try: token = json.loads((pathlib.Path(base or DIR.parent) / "datos" / "cache" / "sesion.json").read_text(encoding="utf-8")).get("token")
        except (OSError, ValueError, AttributeError): token = None
    return (api, token) if api and token else None


def backend(metodo, ruta, cuerpo=None, base=None, timeout=20):
    """JSON del backend de Racha con tu código o tu sesión de Google; None si no hay acceso. Lanza urllib.error si falla."""
    a = acceso(base)
    if not a: return None
    h = {"Content-Type": "application/json", "User-Agent": "racha"}
    h.update({"Authorization": "Bearer " + a[1]} if len(a[1]) == 64 else {"X-Racha-Token": a[1]})  # sesión o código
    req = urllib.request.Request(a[0] + ruta, data=None if cuerpo is None else json.dumps(cuerpo).encode(), headers=h, method=metodo)
    with urllib.request.urlopen(req, timeout=timeout) as r: return json.load(r)


COLAS = {420: "Solo/Duo", 440: "Flex", 400: "Normal", 430: "Normal", 490: "Rápida", 480: "Rápida", 450: "ARAM"}


def historial(h, nombres):
    """Tus últimas partidas del cliente (/lol-match-history, sin key de Riot; trae ~20 y solo tus datos), la más nueva
    primero: [{campeon, win, kda, cs, cola, ts, min}]. Sin remakes (< 5 min) ni modos de evento (colas fuera de COLAS)."""
    out = []
    for g in ((h or {}).get("games") or {}).get("games") or []:
        p = (g.get("participants") or [None])[0]
        if not p or g.get("queueId") not in COLAS or (g.get("gameDuration") or 0) < 300: continue
        st = p.get("stats") or {}
        out.append({"campeon": nombres.get(p.get("championId"), str(p.get("championId"))), "win": bool(st.get("win")),
                    "kda": f"{st.get('kills', 0)}/{st.get('deaths', 0)}/{st.get('assists', 0)}",
                    "cs": (st.get("totalMinionsKilled") or 0) + (st.get("neutralMinionsKilled") or 0),
                    "cola": COLAS[g["queueId"]], "ts": g.get("gameCreation") or 0, "min": (g.get("gameDuration") or 0) // 60})
    return sorted(out, key=lambda x: -x["ts"])


VIVO = DIR.parent / "datos" / "vivo"


def vivo():
    """Foto de /liveclientdata/allgamedata (sin auth, solo durante la partida); None si no responde."""
    try:
        with urllib.request.urlopen("https://127.0.0.1:2999/liveclientdata/allgamedata", context=SSL, timeout=5) as r: return json.load(r)
    except FALLAS: return None


def capturar(archivo, d):
    """Agrega la foto en vivo d a archivo (lo crea en VIVO al primer dato); devuelve el archivo."""
    if d is None: return archivo
    if archivo is None: VIVO.mkdir(parents=True, exist_ok=True); archivo = VIVO / f"{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    with open(archivo, "a", encoding="utf-8") as f: f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return archivo


def yo_rival(d):
    """(tu jugador, tu rival de línea) en allPlayers de la foto en vivo; rival None sin position (normales, ARAM)."""
    yo = (d or {}).get("activePlayer") or {}; ids = {yo.get("riotId"), yo.get("summonerName")} - {None, ""}  # null al cargar
    ps = (d or {}).get("allPlayers") or []
    me = next((p for p in ps if {p.get("riotId"), p.get("summonerName")} & ids), None)
    if not me or me.get("position") in (None, "", "NONE"): return me, None  # ARAM y modos sin líneas: «NONE», no hay rival de línea
    return me, next((p for p in ps if p.get("position") == me["position"] and p.get("team") != me.get("team")), None)


def grieta(d):
    """True en la Grieta del Invocador (CLASSIC): dragón, barón y reglas de línea solo tienen sentido ahí."""
    return (((d or {}).get("gameData") or {}).get("gameMode") or "CLASSIC") == "CLASSIC"


def kda(p):
    s = (p or {}).get("scores") or {}
    return f"{s.get('kills') or 0}/{s.get('deaths') or 0}/{s.get('assists') or 0}"


def meta_aram(d, me):
    """ARAM y modos sin líneas: {modo, minuto, campeon, nivel, kda, kills, torres, amenazas}. amenazas = los 3 rivales más
    fuertes ahora (kills, luego asistencias, luego menos muertes) con su KDA, nivel e ítems: a quién cuidar en la pelea."""
    ps, yo = (d or {}).get("allPlayers") or [], me.get("team")
    o = objetivos(d, me)
    sc = lambda p: p.get("scores") or {}
    rivales = sorted((p for p in ps if p.get("team") != yo),
                     key=lambda p: (-(sc(p).get("kills") or 0), -(sc(p).get("assists") or 0), sc(p).get("deaths") or 0))
    return {"modo": "ARAM", "minuto": int(((d.get("gameData") or {}).get("gameTime") or 0) // 60), "campeon": me.get("championName"),
            "nivel": me.get("level"), "kda": kda(me), "kills": [o["tuyos"]["kills"], o["rival"]["kills"]],
            "torres": [o["tuyos"]["torres"], o["rival"]["torres"]],
            "amenazas": [{"campeon": p.get("championName"), "kda": kda(p), "nivel": p.get("level"),
                          "items": [[i["itemID"], i.get("displayName") or ""] for i in p.get("items") or [] if i.get("itemID") and not i.get("consumable")][:6]}
                         for p in rivales[:3]]}


PRECIOS, LEGENDARIOS = {}, set()  # itemID (str) → costo total · ids de ítems completos (Data Dragon; se llenan una vez)


def precios():
    """Costo total de cada ítem (Data Dragon, en caché de disco). El «price» de la Live Client Data es el costo de
    combinar (Sheen marca 650 y cuesta 900), así que no sirve para sumar oro."""
    if not PRECIOS:
        try:
            import builds
            items = builds.ddragon()[0]
            PRECIOS.update({k: (v.get("gold") or {}).get("total") or 0 for k, v in items.items()})
            LEGENDARIOS.update(k for k, v in items.items() if builds.legendario(v))
        except Exception: pass  # sin Data Dragon: sin oro por ítems (la franja no lo muestra)
    return PRECIOS


def valor_items(p, pr=None):
    """Oro en ítems de un jugador (lo mismo que se ve con Tab): suma de costos totales; None si no hay precios."""
    pr = precios() if pr is None else pr
    if not pr: return None
    return sum((pr.get(str(i.get("itemID"))) or 0) * (i.get("count") or 1) for i in (p or {}).get("items") or [])


def meta_fase(d, m10=None):
    """La meta de la fase como números para la GUI: {minuto, campeon, nivel, rival, nivel_rival, cs, cs_meta, muertes14}; None sin tu jugador.
    muertes14: tus muertes desde el 14:00 (None antes del 14; meta ≤ 2 hasta el 25).
    cs_meta solo con el campeón de minions10 de config.json. La Live Client Data no trae el oro del rival: no hay «oro al 14»."""
    me, rival = yo_rival(d)
    if not me: return None
    if not grieta(d): return meta_aram(d, me)
    if m10 is None: m10 = minions10()
    rs = (rival or {}).get("scores") or {}
    return {"minuto": int(((d.get("gameData") or {}).get("gameTime") or 0) // 60), "campeon": me.get("championName"),
            "nivel": me.get("level"), "rival": (rival or {}).get("championName"), "nivel_rival": (rival or {}).get("level"),
            "cs": (me.get("scores") or {}).get("creepScore"), "muertes14": muertes14(d, me),
            "cs_meta": m10.get("minimo") if m10 and me.get("championName") == m10.get("campeon") else None,
            "rival_kda": f"{rs.get('kills') or 0}/{rs.get('deaths') or 0}/{rs.get('assists') or 0}" if rival else None,
            "rival_cs": rs.get("creepScore"), "rival_items": [[i["itemID"], i.get("displayName") or ""] for i in (rival or {}).get("items") or [] if i.get("itemID") and not i.get("consumable") and i.get("slot") != 6][:6],  # slot 6 = trinket
            "objetivos": objetivos(d, me), "t": int(((d.get("gameData") or {}).get("gameTime") or 0)), "kda": kda(me),
            "oro": oro_lineas(d, me, rival),
            "items": [[i["itemID"], i.get("displayName") or ""] for i in me.get("items") or [] if i.get("itemID") and not i.get("consumable") and i.get("slot") != 6][:6]}


def completos(p, leg=None):
    """Ítems completos (legendarios, sin botas) de un jugador, en el orden de sus casillas."""
    leg = LEGENDARIOS if leg is None else leg
    return [i.get("displayName") or "" for i in (p or {}).get("items") or [] if str(i.get("itemID")) in leg]


def aviso_pico(d, leg=None):
    """Pico de poder del rival de línea: cuando termina un ítem completo y ya tiene más que tú → (clave, texto); si no, None.
    La clave («pico:<n>:<ítem>») hace que cada ítem avise una sola vez. Solo con lo que se ve con Tab."""
    if leg is None: precios(); leg = LEGENDARIOS
    me, rival = yo_rival(d)
    if not rival or not leg: return None
    suyos, mios = completos(rival, leg), completos(me, leg)
    if len(suyos) <= len(mios): return None
    t = ((d or {}).get("gameData") or {}).get("gameTime") or 0
    n = len(suyos)
    return (f"pico:{n}:{suyos[-1]}", f"Min {int(t // 60)}: {rival.get('championName', 'tu rival')} terminó {suyos[-1]} ({n} ítem{'s' if n > 1 else ''} completo{'s' if n > 1 else ''} contra "
            f"{len(mios)} tuyo{'s' if len(mios) != 1 else ''}): ahora pega más. No pelees sin ventaja hasta tener el tuyo; farmea y espera a tu jungla.")


def oro_lineas(d, me, rival, pr=None):
    """Oro en ítems: {tu, rival, equipo, equipo_rival}; None sin precios. Solo lo visible en la tabla (Tab) de la partida."""
    pr = precios() if pr is None else pr
    if not pr: return None
    ps = (d or {}).get("allPlayers") or []
    v = lambda p: valor_items(p, pr)
    return {"tu": v(me), "rival": v(rival) if rival else None,
            "equipo": sum(v(p) for p in ps if p.get("team") == me.get("team")),
            "equipo_rival": sum(v(p) for p in ps if p.get("team") != me.get("team"))}


def objetivos(d, me):
    """Lo de cada equipo en la foto en vivo: {tuyos|rival: {kills, torres, dragones, larvas, heraldo, baron}, dragon, baron}.
    dragon/baron = segundos que faltan para que salga (None: está vivo). Torres por el dueño en el nombre (Turret_TOrder_ / _TChaos_);
    lo demás por el equipo de KillerName (gameName sin tag, o Minion_T100/T200); si no se reconoce, no cuenta."""
    ps = (d or {}).get("allPlayers") or []
    eq = {n: p.get("team") for p in ps for n in (p.get("riotIdGameName"), p.get("summonerName"), (p.get("riotId") or "").split("#")[0]) if n}
    eq.update({"Minion_T100": "ORDER", "Minion_T200": "CHAOS"})
    yo = me.get("team")
    lado = lambda t: None if t is None else "tuyos" if t == yo else "rival"
    r = {k: {"kills": sum((p.get("scores") or {}).get("kills") or 0 for p in ps if lado(p.get("team")) == k),
             "torres": 0, "dragones": 0, "larvas": 0, "heraldo": 0, "baron": 0} for k in ("tuyos", "rival")}
    ult = {"DragonKill": None, "BaronKill": None}
    tipo = {"DragonKill": "dragones", "HordeKill": "larvas", "HeraldKill": "heraldo", "BaronKill": "baron"}
    for e in ((d or {}).get("events") or {}).get("Events") or []:
        n, k = e.get("EventName"), str(e.get("KillerName") or "")
        if n == "TurretKilled":
            t = str(e.get("TurretKilled") or "")
            if (l := lado("CHAOS" if "_TOrder_" in t else "ORDER" if "_TChaos_" in t else None)): r[l]["torres"] += 1
        elif n in tipo and (l := lado(eq.get(k) or eq.get(k[:11]))):
            r[l][tipo[n]] += 1
            if n in ult: ult[n] = e.get("EventTime") or 0
    t = ((d or {}).get("gameData") or {}).get("gameTime") or 0
    # shortcut: dragón 5:00 y cada 5 min, barón 20:00 y cada 6 (ni el Anciano ni cambios de parche); si cambia, ajustar aquí
    def falta(u, primero, cada):  # segundos hasta que sale; None si ya está vivo
        s = (primero if u is None else u + cada) - t
        return round(s) if s > 0 else None
    return {**r, "dragon": falta(ult["DragonKill"], 300, 300), "baron": falta(ult["BaronKill"], 1200, 360)}


def aviso_nivel(d):
    """Del minuto 5 al 7, si vas abajo de nivel contra tu rival de línea (misma position, otro equipo): el aviso; si no, None.
    Sin position (normales, ARAM) no hay rival claro y no avisa. Abajo al 6 → 44% de WR en cozi (.equipo/PLAN.md, nivel6.py/muertes6.py)."""
    t = ((d or {}).get("gameData") or {}).get("gameTime") or 0  # null mientras carga la partida
    if not 300 <= t <= 420: return None
    me, rival = yo_rival(d)
    if not rival or (n := (rival.get("level") or 0) - (me.get("level") or 0)) < 1: return None  # level puede venir null
    return (f"Min {int(t // 60)}: vas {n} nivel{'es' if n > 1 else ''} abajo de {rival.get('championName', 'tu rival')} "
            f"({me.get('level') or '?'} contra {rival.get('level') or '?'}). No tradees hasta igualar; quédate en rango de XP de cada oleada.")


REGRESO_DESDE, REGRESO_HASTA = 600, 840  # min 10 al 14: aún hay tiempo de igualar antes de la ventana de objetivos del 14
REGRESO_CS = 10  # CS de diferencia que cuenta como farm perdido (misma meta que draft.py: CS al 14 >= -10)


def aviso_regreso(d):
    """«Plan de regreso»: del min 10 al 14, si vas abajo de nivel contra tu rival de línea, un solo consejo tranquilo. La Live Client Data
    no trae XP ni oro del rival: el nivel es el proxy de XP (lo que más importa yendo abajo, .equipo/PLAN.md) y el CS el dato de farm."""
    t = ((d or {}).get("gameData") or {}).get("gameTime") or 0
    if not grieta(d) or not REGRESO_DESDE <= t <= REGRESO_HASTA: return None
    me, rival = yo_rival(d)
    if not rival or (n := (rival.get("level") or 0) - (me.get("level") or 0)) < 1: return None
    dcs = ((rival.get("scores") or {}).get("creepScore") or 0) - ((me.get("scores") or {}).get("creepScore") or 0)
    farm = f" y {dcs} CS" if dcs >= REGRESO_CS else ""
    return (f"Min {int(t // 60)}: vas {n} nivel{'es' if n > 1 else ''}{farm} abajo de {rival.get('championName', 'tu rival')}. Juega seguro hasta igualar, "
            "farmea bajo torre y no pelees el próximo objetivo sin tu jungla.")


def muertes14(d, me=None, hasta=float("inf")):
    """Tus muertes desde el 14:00 hasta `hasta` s (eventos ChampionKill de la foto en vivo); None antes del 14 o sin tu jugador."""
    if me is None: me, _ = yo_rival(d)
    if not me or (((d or {}).get("gameData") or {}).get("gameTime") or 0) < 840: return None
    return muertes_en(d, me, 840, hasta)


def muertes_en(d, me, desde=0, hasta=float("inf")):
    """Tus eventos ChampionKill de la foto con desde <= EventTime < hasta. VictimName sin cotejar con una partida real
    (¿con o sin #tag?): el riotId completo siempre vale; los demás nombres (summonerName incluido, que puede venir
    sin tag) solo si nadie más en la partida usa ese mismo nombre en cualquiera de sus campos."""
    otros = [p for p in (d or {}).get("allPlayers") or [] if p is not me]
    nom = lambda p: {p.get("riotIdGameName"), p.get("summonerName"), (p.get("riotId") or "").split("#")[0]}
    corto = nom(me) - set().union(*map(nom, otros)) if otros else nom(me)
    ids = ({me.get("riotId")} | corto) - {None, ""}
    evs = (((d or {}).get("events") or {}).get("Events")) or []
    return sum(1 for e in evs if e.get("EventName") == "ChampionKill" and e.get("VictimName") in ids and desde <= (e.get("EventTime") or 0) < hasta)


def resumen_fin(d):
    """«Una línea al terminar» sin key de Riot, de la última foto en vivo (hasta 30 s antes del final): meta_fase() más
    kda y muertes14_25 (tus muertes del 14:00 al 25:00; None si acabó antes del 14). None sin foto o sin tu jugador."""
    if not (mf := meta_fase(d)): return None
    me = yo_rival(d)[0]; s = me.get("scores") or {}
    # cotejo: con muertes en el marcador y ningún evento con tu nombre, el formato de VictimName no es el esperado
    # y el aviso 14–25 no te cuenta (no se exige igualdad: las fotos de prueba traen eventos parciales)
    cotejo = None if not s.get("deaths") else muertes_en(d, me) > 0
    return {**mf, "kda": f"{s.get('kills') or 0}/{s.get('deaths') or 0}/{s.get('assists') or 0}", "muertes14_25": muertes14(d, hasta=1500), "cotejo": cotejo}


def linea_fin(r):
    """«Min 31 · Sylas 5/4/7 contra Zed · CS 245 · muertes del 14 al 25: 3 (meta ≤ 2) ✕» o None."""
    if not r: return None
    t = [f"Min {r['minuto']}", f"{r['campeon'] or '?'} {r['kda']}" + (f" contra {r['rival']}" if r["rival"] else ""), f"CS {r['cs'] if r['cs'] is not None else '?'}"]
    if r.get("cotejo") is False: t.append("no cuadran tus muertes con los eventos: el aviso del 14 al 25 no te cuenta, avísale a Opus")
    elif r["muertes14_25"] is not None: t.append(f"muertes del 14 al 25: {r['muertes14_25']} (meta ≤ 2) {'✓' if r['muertes14_25'] <= 2 else '✕'}")
    return " · ".join(t)


def aviso_muertes(d):
    """Del 14 al 25, al llegar a 2 muertes desde el 14: el aviso; si no, None. 0–2 muertes del 14 al 25 → 68%, 3+ → 43%
    en tus 282 partidas (datos/analisis-aviso-muertes-*.md; con línea y equipo ≥ 0 al 14, 82% contra 57%)."""
    t = ((d or {}).get("gameData") or {}).get("gameTime") or 0
    if not grieta(d) or not 840 <= t < 1500 or (n := muertes14(d) or 0) < 2: return None
    return (f"Min {int(t // 60)}: {n} muertes desde el 14. Juega con objetivo: no pelees si no sale un dragón, heraldo o torre; "
            "la meta es 2 o menos del 14 al 25.")


CFG = DIR.parent / "config.json"  # opcional, como en revision.py


def minions10():
    """La meta minions10 de config.json, o None sin archivo o si está roto (no debe tumbar los avisos en partida)."""
    try: c = json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
    except (OSError, ValueError): return None
    m = c.get("minions10") if isinstance(c, dict) else None
    return m if isinstance(m, dict) and "campeon" in m and "minimo" in m else None


def aviso_minions(d, m10=None):
    """Del minuto 10 al 11, si juegas el campeón de la meta minions10 de config.json y vas bajo el mínimo: el aviso; si no, None.
    Sylas con 69+ minions de línea al 10 → 74%, con ≤ 68 → 32% (early.py). creepScore en vivo incluye monstruos (en mid, pocos)."""
    if m10 is None: m10 = minions10()
    t = ((d or {}).get("gameData") or {}).get("gameTime") or 0
    if not m10 or not grieta(d) or not 600 <= t <= 660: return None  # 60 s de ventana: la foto de cada 30 s siempre cae dentro
    me, _ = yo_rival(d)
    if not me or me.get("championName") != m10["campeon"]: return None
    cs = (me.get("scores") or {}).get("creepScore") or 0
    if cs >= m10["minimo"]: return None
    return (f"Min 10: llevas {cs} de CS con {m10['campeon']} (meta {m10['minimo']}+). "
            "No roamees ni tradees a costa de oleadas hasta el 14.")



def espera(fallos):
    """Segundos hasta el próximo sondeo: 3 con el cliente arriba; con fallos seguidos, 6, 12, 24 y tope 30."""
    return min(3 * 2 ** fallos, 30)


def rivales(s):
    """(tu posición de Riot, [championId de tus rivales]) de una sesión de /lol-champ-select/v1/session."""
    ellos = s.get("theirTeam") or []  # or []: la LCU puede traer la clave en null
    me = next((p for p in s.get("myTeam") or [] if p.get("cellId") == s.get("localPlayerCellId")), {})
    pos = POS.get(me.get("assignedPosition") or "", "MIDDLE")  # sin rol asignado (normales): mid, como draft.py
    elegidos = [p for p in ellos if p.get("championId")]
    mismo = [p["championId"] for p in elegidos if POS.get(p.get("assignedPosition") or "") == pos]
    if any(p.get("assignedPosition") for p in ellos): return pos, mismo  # con roles: espera a tu rival, no al jungla
    return pos, sorted(p["championId"] for p in elegidos)


def nombres_lcu():
    """championId -> alias («MonkeyKing», como championName de la Riot API) de la lista local del cliente: sirve sin partidas."""
    s = lcu("/lol-game-data/assets/v1/champion-summary.json")
    return {c["id"]: c["alias"] for c in s if isinstance(c, dict) and (c.get("id") or -1) > 0 and c.get("alias")} if isinstance(s, list) else {}


def nombres():
    """championId -> championName sacado de tus partidas en datos/raw (sin red)."""
    m = {}
    for f in (pathlib.Path(os.environ.get("DATOS_DIR") or DIR.parent / "datos" / "raw")).glob("*_*.json"):
        for p in json.loads(f.read_text())["info"]["participants"]: m[p["championId"]] = p["championName"]
    return m


def recomendar(pos, ids, m):
    import draft  # carga tus partidas: solo al entrar a champ select
    if len(ids) > 1: print(f"(rol del rival desconocido: van los {len(ids)} rivales elegidos)")
    for i in ids:
        if i not in m: print(f"\nRival id {i}: no aparece en tus partidas.\n"); continue
        print(f"\n=== {m[i]} ({pos}) ==="); draft.draft(m[i], pos)


FIN = ("PreEndOfGame", "EndOfGame")


def post_partida():
    print("Partida terminada: espero 60 s a que Riot la publique…"); time.sleep(60)
    r = subprocess.run([sys.executable, str(DIR / "descargar.py"), "5"])
    if r.returncode == 2: print("\n*** renueva RIOT_KEY y corre: python scripts/descargar.py 5 && python scripts/revision.py 1 ***\n"); return
    if r.returncode == 3: print("Riot aún no publica la partida (404): en unos minutos corre python scripts/descargar.py 5 && python scripts/revision.py 1"); return
    if r.returncode: print(f"descargar.py falló ({r.returncode}); la partida queda pendiente."); return
    subprocess.run([sys.executable, str(DIR / "revision.py"), "1"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fixture", metavar="CARPETA", help="una pasada con gameflow-phase.json y session.json de esa carpeta (sin cliente)")
    a = ap.parse_args(argv)
    get = lcu
    if a.fixture:
        d = pathlib.Path(a.fixture)
        get = lambda path: json.loads((d / ("session.json" if "champ-select" in path else "gameflow-phase.json")).read_text())
    m, visto, fase_ant, real, archivo, ult, avisado, fallos, foto = None, None, None, None, None, 0, set(), 0, None
    while True:
        fase = get("/lol-gameflow/v1/gameflow-phase")  # fuera del try: lcu() ya atrapa todo, y las pruebas cortan el bucle desde aquí
        if fase is None and fase_ant != "cerrado": print("Cliente cerrado: espero…")
        elif fase != fase_ant: print(f"Fase: {fase}")
        jugando = (fase or real) == "InProgress"  # si el cliente se reinicia a media partida, la partida (y el puerto 2999) sigue
        try:
            if fase == "ChampSelect" and (s := get("/lol-champ-select/v1/session")):
                pos, ids = rivales(s)
                if ids and (pos, ids) != visto:
                    m = m or nombres(); recomendar(pos, ids, m); visto = (pos, ids)
            elif fase != "ChampSelect": visto = None
            if jugando and get is lcu and time.time() - ult >= 30:
                d = vivo(); archivo, ult = capturar(archivo, d), time.time(); foto = d or foto
                for f in (aviso_nivel, aviso_muertes):  # cada aviso, una vez por partida
                    if f.__name__ not in avisado and (txt := f(d)): print(f"\n*** {txt} ***\n"); avisado.add(f.__name__)
            elif not jugando: archivo, avisado = None, set()  # partida nueva, archivo y avisos nuevos
            if fase in FIN and real not in FIN and get is lcu:  # real: un reinicio en EndOfGame no repite la descarga
                if txt := linea_fin(resumen_fin(foto)): print(f"\n{txt}\n")
                foto = None; post_partida()
        except Exception as e: print(f"Error (sigo): {e!r}")  # un JSON raro no tumba el companion
        fase_ant, real, fallos = fase or "cerrado", fase or real, 0 if fase else fallos + 1
        if get is not lcu: return
        time.sleep(espera(fallos))


if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
