"""Build de los mejores con un campeón, y la tuya contra la suya.
Uso: python scripts/builds.py <Campeón> [rol]     (rol: top, mid, jungla, bot, support; sin rol, cualquiera)
     python scripts/builds.py --pool              (tus campeones con 10+ partidas → datos/analisis-builds-<fecha>.md)

Fuentes:
  Los mejores: Riot API (necesita RIOT_KEY). Challenger y Grandmaster de LAN (la1) y Corea (kr), de más a menos LP;
    los 2 primeros de cada región que tienen maestría en el campeón y lo jugaron en los últimos 14 días;
    de sus últimas 20 ranked, las partidas con ese campeón (y rol) y su timeline. Unas 100–250 llamadas la primera vez
    (~1.2 s entre cada una por el límite de la dev key); todo queda en caché en datos/meta/ (no se sube a git).
  Tú: datos/raw (sin red).
  Nombres de ítems y runas: Data Dragon (público, sin key), en caché en datos/meta/ddragon/.

Qué es la build: los 3 primeros ítems legendarios en el orden en que se compraron (ITEM_PURCHASED del timeline,
quitando los ITEM_UNDO), las primeras botas de tier 2, la runa principal con su página más común y el orden en que
se maximizan Q/W/E (el que llega antes a 3 puntos va primero). Cada posición se resume con el ítem más común.
`--pool` además guarda datos/meta/builds.json, que draft.py lee (sin red) para mostrar la build en champ select
(la de los mejores; si no hay, por ejemplo con la key caducada, la tuya)."""
import json, math, os, pathlib, re, sys, time, urllib.error, urllib.request
from collections import Counter
from datetime import datetime

if __name__ == "__main__": sys.stdout.reconfigure(encoding="utf-8")
BASE = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or BASE / "datos" / "raw")
META = pathlib.Path(os.environ.get("META_DIR") or BASE / "datos" / "meta")
ROLES = {"top": "TOP", "jungla": "JUNGLE", "jungle": "JUNGLE", "mid": "MIDDLE", "bot": "BOTTOM", "adc": "BOTTOM",
         "support": "UTILITY", "sup": "UTILITY"}
REGIONES = {"la1": "americas", "kr": "asia"}
DIA = 86400
SKILL = "QWER"


class SinKey(Exception): pass


def get(url, ttl=None, riot=False):
    """JSON de la URL, con caché en datos/meta/ (ttl en s; None = para siempre). 404 → None. Sin key/401/403 → SinKey."""
    f = META / "cache" / (re.sub(r"[^\w.-]+", "_", url.split("://", 1)[1])[:180] + ".json")
    if f.exists() and (ttl is None or time.time() - f.stat().st_mtime < ttl):
        return json.loads(f.read_text(encoding="utf-8"))
    hdr = {"User-Agent": "plan-challenger"}
    if riot:
        if not os.environ.get("RIOT_KEY"): raise SinKey("falta RIOT_KEY")
        hdr["X-Riot-Token"] = os.environ["RIOT_KEY"]  # nunca se guarda: la caché es solo la respuesta
    for intento in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 404: data = None; break
            if e.code in (401, 403): raise SinKey(f"Riot respondió {e.code}: renueva RIOT_KEY")
            if e.code == 429 and intento < 3: time.sleep(int(e.headers.get("Retry-After", 10))); continue
            if e.code < 500 or intento == 3: raise
            time.sleep(5)
    if riot: time.sleep(1.2)  # dev key: 100 llamadas cada 2 min
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data), encoding="utf-8")
    return data


def ddragon():
    """(ítems {id: dict}, runas {id: nombre}, campeones {nombre normalizado: (id, key numérica)}) de Data Dragon en español."""
    v = get("https://ddragon.leagueoflegends.com/api/versions.json", ttl=DIA)[0]
    cdn = f"https://ddragon.leagueoflegends.com/cdn/{v}/data/es_MX/"
    items = get(cdn + "item.json")["data"]
    runas = {}
    for s in get(cdn + "runesReforged.json"):
        runas[s["id"]] = s["name"]
        for slot in s["slots"]:
            for r in slot["runes"]: runas[r["id"]] = r["name"]
    champs = {norm(c["id"]): (c["id"], int(c["key"])) for c in get(cdn + "champion.json")["data"].values()}
    champs.update({norm(c["name"]): (c["id"], int(c["key"])) for c in get(cdn + "champion.json")["data"].values()})
    return items, runas, champs


def norm(s): return "".join(c for c in s.lower() if c.isalnum())


def legendario(it): return bool(it) and not it.get("into") and it["gold"]["total"] >= 2000 and "Boots" not in it.get("tags", []) \
    and it.get("maps", {}).get("11", True)
def botas(it, iid): return bool(it) and "Boots" in it.get("tags", []) and iid != "1001"


def build_de(match, timeline, puuid, items):
    """La build de `puuid` en una partida: dict(champ, pos, win, core [ids], botas, runas (estilo, keystone, página), skills)."""
    p = next(x for x in match["info"]["participants"] if x["puuid"] == puuid)
    pid = next((x["participantId"] for x in timeline["info"]["participants"] if x["puuid"] == puuid), p["participantId"])
    compras, ups = [], []
    for fr in timeline["info"]["frames"]:
        for e in fr["events"]:
            if e.get("participantId") != pid: continue
            if e["type"] == "ITEM_PURCHASED": compras.append(str(e["itemId"]))
            elif e["type"] == "ITEM_UNDO" and str(e.get("beforeId")) in compras:
                del compras[len(compras) - 1 - compras[::-1].index(str(e["beforeId"]))]
            # un legendario vendido no es core (compra equivocada); las botas vendidas al final sí cuentan
            elif e["type"] == "ITEM_SOLD" and legendario(items.get(str(e.get("itemId")))) and str(e["itemId"]) in compras:
                del compras[len(compras) - 1 - compras[::-1].index(str(e["itemId"]))]
            elif e["type"] == "SKILL_LEVEL_UP" and e.get("levelUpType", "NORMAL") == "NORMAL": ups.append(e["skillSlot"])
    core = []
    for i in compras:
        if legendario(items.get(i)) and i not in core: core.append(i)
    rango, llega3 = Counter(), {}
    for n, s in enumerate(ups):
        rango[s] += 1
        if rango[s] == 3: llega3.setdefault(s, n)
    orden = sorted((1, 2, 3), key=lambda s: (llega3.get(s, math.inf), -rango[s]))
    st = p["perks"]["styles"]
    return dict(champ=p["championName"], pos=p["teamPosition"], win=p["win"], core=core[:3],
                botas=next((i for i in compras if botas(items.get(i), i)), None),
                runas=(st[0]["style"], st[0]["selections"][0]["perk"],
                       tuple(s["perk"] for s in st[0]["selections"]) + (st[1]["style"],) + tuple(s["perk"] for s in st[1]["selections"])),
                skills=">".join(SKILL[s - 1] for s in orden))


def resumir(bs, items, runas):
    """Lo más común de una lista de builds: dict(n, wr, core [(nombre, %)], botas, runa, pagina, skills) o None."""
    if not bs: return None
    n = len(bs); nom = lambda i: items.get(i, {}).get("name", i)
    core, usados = [], set()
    for k in range(3):
        c = Counter(b["core"][k] for b in bs if len(b["core"]) > k and b["core"][k] not in usados)
        if not c: break
        i, v = c.most_common(1)[0]; usados.add(i); core.append((nom(i), v / n, i))
    b_ = Counter(b["botas"] for b in bs if b["botas"])
    ks = Counter(b["runas"][1] for b in bs).most_common(1)[0]
    pag = Counter(b["runas"][2] for b in bs if b["runas"][1] == ks[0]).most_common(1)[0][0]
    sk = Counter(b["skills"] for b in bs).most_common(1)[0]
    return dict(n=n, wr=sum(b["win"] for b in bs) / n, core=core,
                botas=(nom(b_.most_common(1)[0][0]), b_.most_common(1)[0][1] / n) if b_ else None,
                runa=(runas.get(ks[0], ks[0]), ks[1] / n), pagina=[runas.get(r, r) for r in pag],
                skills=(sk[0], sk[1] / n))


def lineas(r, quien):
    """3 líneas de texto de un resumen (para draft.py y la consola)."""
    if not r: return [f"{quien}: sin partidas."]
    core = " → ".join(f"{c} ({p:.0%})" for c, p, _ in r["core"]) or "-"
    bot = f"{r['botas'][0]} ({r['botas'][1]:.0%})" if r["botas"] else "-"
    return [f"{quien} ({r['n']} partidas, WR {r['wr']:.0%}): {core}; botas {bot}",
            f"  Runas: {r['runa'][0]} ({r['runa'][1]:.0%}) · {', '.join(map(str, r['pagina'][1:4]))} · secundaria {r['pagina'][4]}",
            f"  Habilidades: {r['skills'][0]} ({r['skills'][1]:.0%})"]


def mejores(cid, nombre, pos=None, por_region=2, partidas=20, ahora=None):
    """[(match, timeline, puuid, "Nombre#TAG región")] de los mejores con ese campeón (Riot API). Lanza SinKey sin key."""
    ahora = ahora or time.time()
    out = []
    for plat, ruta in REGIONES.items():
        lad = []
        for liga in ("challengerleagues", "grandmasterleagues"):
            d = get(f"https://{plat}.api.riotgames.com/lol/league/v4/{liga}/by-queue/RANKED_SOLO_5x5", ttl=DIA, riot=True)
            lad += (d or {}).get("entries", [])
        lad.sort(key=lambda e: -e["leaguePoints"])
        hallados = 0
        for e in lad[:60]:  # tope de llamadas: los 60 de más LP por región
            m = get(f"https://{plat}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{e['puuid']}"
                    f"/by-champion/{cid}", ttl=DIA, riot=True)
            if not m or ahora - m["lastPlayTime"] / 1000 > 14 * DIA: continue
            acc = get(f"https://{ruta}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{e['puuid']}", ttl=7 * DIA, riot=True) or {}
            quien = f"{acc.get('gameName', '?')}#{acc.get('tagLine', '?')} ({plat}, {e['leaguePoints']} LP)"
            ids = get(f"https://{ruta}.api.riotgames.com/lol/match/v5/matches/by-puuid/{e['puuid']}/ids?queue=420&count={partidas}",
                      ttl=DIA, riot=True) or []
            antes = len(out)
            for mid in ids:
                mt = get(f"https://{ruta}.api.riotgames.com/lol/match/v5/matches/{mid}", riot=True)
                p = mt and next((x for x in mt["info"]["participants"] if x["puuid"] == e["puuid"]), None)
                if not p or p["championName"] != nombre or (pos and p["teamPosition"] != pos): continue
                tl = get(f"https://{ruta}.api.riotgames.com/lol/match/v5/matches/{mid}/timeline", riot=True)
                if tl: out.append((mt, tl, e["puuid"], quien))
            hallados += len(out) > antes
            if hallados >= por_region: break
    return out


def tuyas(nombre, pos=None):
    """[(match, timeline, puuid)] de tus partidas en datos/raw con ese campeón (y rol), sin remakes."""
    yo = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
    out = []
    for f in sorted(RAW.glob("*_*.json")):
        m = json.loads(f.read_text())
        p = next((x for x in m["info"]["participants"] if x["puuid"] == yo), None)
        tf = RAW / "timeline" / f.name
        if p and p["championName"] == nombre and (not pos or p["teamPosition"] == pos) and m["info"]["gameDuration"] >= 300 and tf.exists():
            out.append((m, json.loads(tf.read_text()), yo))
    return out


def wilson(k, n, z=1.96):  # misma que draft.py
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def wr(bs):
    if not bs: return "-"
    k = sum(b["win"] for b in bs); lo, hi = wilson(k, len(bs))
    return f"{k}/{len(bs)} = {k / len(bs):.0%} ({lo:.0%}–{hi:.0%})"


def por_primer(bs, items, minimo=5):
    """[(nombre del primer legendario, [builds])] con `minimo`+ partidas, de más a menos jugado (sin key: solo las tuyas)."""
    g = {}
    for b in bs:
        if b["core"]: g.setdefault(b["core"][0], []).append(b)
    return [(items.get(i, {}).get("name", i), v) for i, v in sorted(g.items(), key=lambda x: -len(x[1])) if len(v) >= minimo]


def informe(campeon, pos=None):
    """(texto markdown, resumen de los mejores o None, el tuyo o None)."""
    items, runas, champs = ddragon()
    if norm(campeon) not in champs: return f"Campeón desconocido: {campeon}", None, None
    nombre, cid = champs[norm(campeon)]
    rol = f" {pos}" if pos else ""
    txt = [f"## {nombre}{rol}\n"]
    try:
        top = mejores(cid, nombre, pos)
        jug = sorted({q for *_, q in top})
        rt = resumir([build_de(m, t, u, items) for m, t, u, _ in top], items, runas)
        txt += ["Fuente: Riot API (match-v5 y timeline), " + (", ".join(jug) or "ningún Challenger/GM lo jugó en 14 días") + "\n"]
        txt += [l + "  " for l in lineas(rt, "Los mejores")]
    except (SinKey, urllib.error.URLError) as e:  # 429 sostenido o sin red: sale tu parte, el pool sigue
        rt = None
        cura = "con una key nueva" if isinstance(e, SinKey) else "en unos minutos (límite de Riot o sin red)"
        txt += [f"Los mejores: sin datos ({e}). Corre `builds.py {nombre}` otra vez {cura}.\n"]
    mias = [build_de(m, t, u, items) for m, t, u in tuyas(nombre, pos)]
    tu = resumir(mias, items, runas)
    txt += [""] + [l + "  " for l in lineas(tu, "Tú")]
    if (pp := por_primer(mias, items)):
        txt += ["", "Tu WR por primer ítem (5+ partidas; pista, no causa): " + "; ".join(f"{nm} {wr(bs)}" for nm, bs in pp) + "."]
    if rt and mias and rt["core"]:
        uno = rt["core"][0][2]
        si = [b for b in mias if b["core"][:1] == [uno]]; no = [b for b in mias if b["core"][:1] != [uno]]
        rt["primer"] = dict(item=rt["core"][0][0], si=[sum(b["win"] for b in si), len(si)], no=[sum(b["win"] for b in no), len(no)])
        txt += ["", f"Tu WR con {rt['core'][0][0]} de primer ítem (como los mejores): {wr(si)}; con otro: {wr(no)}. "
                    "Si los intervalos se cruzan, es pista, no hecho (y aun sin cruzarse, no prueba que el ítem cause la victoria)."]
    return "\n".join(txt) + "\n", rt, tu


def pool(minimo=10):
    """[(campeón, rol más jugado)] con `minimo`+ partidas tuyas en datos/raw."""
    yo = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
    c = Counter()
    for f in RAW.glob("*_*.json"):
        p = next((x for x in json.loads(f.read_text())["info"]["participants"] if x["puuid"] == yo), None)
        if p: c[(p["championName"], p["teamPosition"])] += 1
    tot = Counter()
    for (ch, _), v in c.items(): tot[ch] += v
    return [(ch, max((r for (x, r) in c if x == ch), key=lambda r: c[(ch, r)])) for ch, v in tot.most_common() if v >= minimo]


def guardado_dict(campeon, pos):
    """La build que dejó `--pool` (sin red) como dict para la GUI: el resumen de `resumir` más `fuente` ("mejores" o "tu")
    y, en la de los mejores, `primer` = {item, si: [V, n], no: [V, n]} (tu récord con su primer ítem y con otro); o None."""
    f = META / "builds.json"
    try: d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError): return None  # sin archivo o cortado: champ select sigue sin build
    for k, fuente in ((f"{campeon}|{pos}", "mejores"), (f"{campeon}|{pos}|tu", "tu")):
        if d.get(k): return dict(d[k], fuente=fuente)
    return None


def guardado(campeon, pos):
    """Las 3 líneas de esa build (la de los mejores; sin ella, la tuya), más una con tu WR con su primer ítem si la hay; o []."""
    r = guardado_dict(campeon, pos)
    if not r: return []
    ls = lineas(r, "Los mejores" if r["fuente"] == "mejores" else "Tu build (aún sin la de los mejores)")
    p = r.get("primer")
    if p and p["si"][1] and p["no"][1]:
        rec = lambda k, n: f"{k}/{n} = {k / n:.0%} ({wilson(k, n)[0]:.0%}–{wilson(k, n)[1]:.0%})"
        ls.append(f"  Tú con {p['item']} primero: {rec(*p['si'])}; con otro: {rec(*p['no'])} (pista, no causa)")
    return ls


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    if sys.argv[1] == "--pool":
        partes, guarda = [f"# Builds de los mejores contra la tuya ({datetime.now():%Y-%m-%d})\n"], {}
        for ch, pos in pool():
            t, rt, tu = informe(ch, pos); partes.append(t)
            if rt: guarda[f"{ch}|{pos}"] = rt
            if tu: guarda[f"{ch}|{pos}|tu"] = tu
        if guarda:
            META.mkdir(parents=True, exist_ok=True)
            (META / "builds.json").write_text(json.dumps(guarda, ensure_ascii=False), encoding="utf-8")
        out = BASE / "datos" / f"analisis-builds-{datetime.now():%Y-%m-%d}.md"
        out.write_text("\n".join(partes), encoding="utf-8")
        print("\n".join(partes)); print(f"→ {out.relative_to(BASE)}")
    else:
        rol = sys.argv[2].lower() if len(sys.argv) > 2 else None
        if rol and rol not in ROLES: sys.exit(f"Rol desconocido: {rol}. Usa: {', '.join(ROLES)}")
        print(informe(sys.argv[1], ROLES.get(rol))[0])
