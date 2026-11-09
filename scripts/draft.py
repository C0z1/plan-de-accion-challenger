"""Matchups y draft con tus datos.
Uso:
  python scripts/draft.py > datos/analisis-matchups-AAAA-MM-DD.md   guía completa (bans, rivales de línea, pool por rol)
  python scripts/draft.py Viktor [mid]                             champ select: qué pickear contra ese rival
Rol: top, jungla, mid, bot, support (por defecto mid)."""
import json, os, math, pathlib, random, statistics as st, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
ROLES = {"top": "TOP", "jungla": "JUNGLE", "jungle": "JUNGLE", "mid": "MIDDLE", "bot": "BOTTOM", "adc": "BOTTOM",
         "support": "UTILITY", "sup": "UTILITY"}
ALIAS = {"wukong": "monkeyking", "nunu": "nunuwillump", "renata": "renataglasc"}
M = 10  # partidas "virtuales" del prior: con pocas partidas contra un rival, manda el WR general de tu campeón


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))  # sin el recorte, 0 de n salía «-0%» por redondeo


def shrink(k, n, p0): return (k + M * p0) / (n + M)
assert round(shrink(0, 0, .55), 2) == .55 and round(shrink(10, 10, .5), 2) == .75


def wr(rs):
    if not rs: return "-"
    k = sum(r["win"] for r in rs); lo, hi = wilson(k, len(rs))
    return f"{k / len(rs):.0%} ({lo:.0%}–{hi:.0%})"


def key(name): s = "".join(c for c in name.lower() if c.isalnum()); return ALIAS.get(s, s)
def gd(rs):
    v = [r["gd14"] for r in rs if r["gd14"] is not None]
    return f"{st.mean(v):+.0f}" if v else "-"


games = []
for f in RAW.glob("*_*.json"):
    m = json.loads(f.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    g = dict(win=me["win"], champ=me["championName"], pos=me["teamPosition"] or "?", opp=opp["championName"] if opp else "?",
             enemies={p["championName"] for p in ps if p["teamId"] != me["teamId"]}, gd14=None, t=m["gameCreation"])
    tf = RAW / "timeline" / f.name
    if opp and tf.exists():
        fr = json.loads(tf.read_text())["info"]["frames"]
        yo, el = str(me["participantId"]), str(opp["participantId"])
        dif = lambda i, f: f(fr[i]["participantFrames"][yo]) - f(fr[i]["participantFrames"][el])
        if len(fr) > 14:
            g["gd14"] = dif(14, lambda p: p["totalGold"])
            g["xp14"] = dif(14, lambda p: p["xp"])
            g["cs14"] = dif(14, lambda p: p["minionsKilled"] + p["jungleMinionsKilled"])
        if len(fr) > 6: g["nivel6"] = dif(6, lambda p: p["level"])
        g["muertes6"] = sum(e.get("type") == "CHAMPION_KILL" and e.get("victimId") == me["participantId"] and e["timestamp"] < 360000
                            for f in fr for e in f["events"])
    games.append(g)
assert games, "sin partidas"
base = sum(g["win"] for g in games) / len(games)


def pool(pos, minimo=5):
    """Tus campeones en ese rol con al menos `minimo` partidas: {campeón: [partidas]}."""
    by = defaultdict(list)
    for g in games:
        if g["pos"] == pos: by[g["champ"]].append(g)
    return {c: rs for c, rs in by.items() if len(rs) >= minimo}


def guia():
    print(f"# Guía de matchups y draft: {len(games)} partidas (WR base {base:.0%})\n")
    print("Intervalos: Wilson 95%. Con menos de ~20 partidas son pistas, no reglas. Generado por `scripts/draft.py`.\n")

    print("## Bans: campeones rivales (en cualquier rol) contra los que peor te va\n")
    print("Mínimo 8 partidas. «Techo» = el WR más alto que es compatible con tus datos: si está por debajo de tu WR base, es un ban con respaldo.\n")
    print("| Rival en el equipo enemigo | Partidas | WR (IC 95%) | ¿Techo < base? |\n|---|---|---|---|")
    by = defaultdict(list)
    for g in games:
        for e in g["enemies"]: by[e].append(g)
    filas = [(sum(r["win"] for r in rs) / len(rs), c, rs) for c, rs in by.items() if len(rs) >= 8]
    for p, c, rs in sorted(filas, key=lambda x: x[0])[:12]:
        hi = wilson(sum(r["win"] for r in rs), len(rs))[1]
        print(f"| {c} | {len(rs)} | {wr(rs)} | {'sí' if hi < base else 'no'} |")
    # control de comparaciones múltiples: permutación a nivel de partida (barajar V/D entre partidas conserva que
    # una misma partida cuenta para 5 rivales); ¿cuántos «sí» saldrían si el rival no importara?
    idx = {id(g): i for i, g in enumerate(games)}
    grupos = [[idx[id(r)] for r in rs] for _, _, rs in filas]
    cuenta = lambda w: sum(wilson(sum(w[i] for i in gi), len(gi))[1] < base for gi in grupos)
    real, rnd, w = cuenta([g["win"] for g in games]), random.Random(1), [g["win"] for g in games]
    perms = [cuenta(rnd.sample(w, len(w))) for _ in range(1000)]
    pval = sum(c >= real for c in perms) / len(perms)
    print(f"\nControl (permutación de 1000 barajadas de V/D): de {len(grupos)} rivales con 8+ partidas, {real} tienen techo < base; "
          f"por puro azar saldrían ~{st.mean(perms):.1f}, y {real} o más en el {pval:.0%} de las barajadas. "
          f"{'Ningún ban tiene respaldo real todavía: úsalos como pista.' if pval >= 0.05 else 'Hay más de lo que da el azar.'}")

    print("\n## Rivales de línea (3+ partidas)\n\n| Rival | Rol | Partidas | WR (IC 95%) | Oro @14 | Con qué jugaste (V-D) |\n|---|---|---|---|---|---|")
    by = defaultdict(list)
    for g in games: by[(g["opp"], g["pos"])].append(g)
    for (c, pos), rs in sorted(by.items(), key=lambda x: (-len(x[1]), x[0])):
        if len(rs) < 3 or c == "?": continue
        mis = defaultdict(lambda: [0, 0])
        for r in rs: mis[r["champ"]][0 if r["win"] else 1] += 1
        uso = ", ".join(f"{ch} {v}-{d}" for ch, (v, d) in sorted(mis.items(), key=lambda x: -sum(x[1])))
        print(f"| {c} | {pos} | {len(rs)} | {wr(rs)} | {gd(rs)} | {uso} |")

    print("\n## Tu pool por rol (5+ partidas)\n\n| Rol | Campeón | Partidas | WR (IC 95%) | Oro @14 |\n|---|---|---|---|---|")
    for pos in ("MIDDLE", "TOP", "UTILITY", "JUNGLE", "BOTTOM"):
        for c, rs in sorted(pool(pos).items(), key=lambda x: -len(x[1])):
            print(f"| {pos} | {c} | {len(rs)} | {wr(rs)} | {gd(rs)} |")


def datos_draft(rival, pos):
    """Los números de draft() sin imprimir (companion_gui.py los dibuja). filas: mejor estimado primero; [] sin partidas en el rol."""
    k = key(rival)
    vs = [g for g in games if key(g["opp"]) == k and g["pos"] == pos]
    en = [g for g in games if k in {key(e) for e in g["enemies"]}]
    nombre = next((e for g in en for e in g["enemies"] if key(e) == k), rival)
    p = pool(pos) or pool(pos, 1)
    filas = []
    for c, rs in p.items():
        p0 = shrink(sum(r["win"] for r in rs), len(rs), base)  # el prior del campeón también se encoge hacia tu base
        mv = [r for r in vs if r["champ"] == c]
        v = sum(r["win"] for r in mv)
        filas.append(dict(est=shrink(v, len(mv), p0), champ=c, wr_rol=wr(rs), vd=f"{v}-{len(mv) - v}", oro=gd(mv), n=len(rs),
                          counter=wilson(v, len(mv))[1] < base if mv else False))  # techo < base, el criterio de los bans
    filas.sort(key=lambda f: -f["est"])
    import builds  # sin red: lo que dejó `builds.py --pool` en datos/meta/builds.json
    return dict(nombre=nombre, conocido=bool(en), vs=vs, en=en, filas=filas, avisos=avisos(filas, nombre, pos),
                build=builds.guardado(filas[0]["champ"], pos) if filas else [],
                build_dict=builds.guardado_dict(filas[0]["champ"], pos) if filas else None)


def avisos(filas, nombre, pos):
    """Avisos sobre el pick recomendado (filas[0]), cada uno con una alternativa si la hay."""
    if not filas: return []
    b, out = filas[0], []
    if b["n"] < 5:
        alt = max(filas, key=lambda f: f["n"])
        out.append(f"{b['champ']} tiene solo {b['n']} partidas en {pos}: el estimado es casi puro azar. "
                   + (f"Alternativa: {alt['champ']} ({alt['n']} partidas, {alt['est']:.0%})." if alt is not b else "No tienes otro con más partidas en el rol."))
    if b["counter"]:
        alt = next((f for f in filas[1:] if not f["counter"]), None)
        out.append(f"{b['champ']} va {b['vd']} contra {nombre}: aun en el mejor caso queda bajo tu WR base (counter duro). "
                   + (f"Alternativa: {alt['champ']} ({alt['est']:.0%})." if alt else "Ningún otro de tu pool lo evita."))
    return out


MEDIDAS = {"oro14": "gd14", "cs14": "cs14", "xp14": "xp14", "nivel6": "nivel6", "muertes6": "muertes6"}  # contra tu rival de línea; muertes6 = tuyas antes del 6
# Medidas cuya media contra un rival anticipa la próxima partida contra él (anticipa.py: muertes6 r 0.28–0.37, p×5 ≤ 0.03;
# oro, CS, XP y nivel al 6 predicen peor que tu media del rol). shortcut: fijo a mano, al rehacer anticipa.py revisarlo.
ANTICIPA = ("muertes6",)
NOTAS = RAW.parent / "matchups-notas.json"  # opcional, a mano: {"Zed": "pega fuerte al 6", ...}


def medidas(rs):
    out = {"n": len(rs)}
    for k, campo in MEDIDAS.items():
        v = [r[campo] for r in rs if r.get(campo) is not None]
        out[k] = round(st.mean(v), 1) if v else None
    return out


def notas(rival):
    try: t = json.loads(NOTAS.read_text(encoding="utf-8"))
    except (OSError, ValueError): return []  # sin tabla o rota: no hay notas, el draft sigue
    if not isinstance(t, dict): return []
    v = next((v for k, v in t.items() if key(k) == key(rival)), [])
    v = [v] if isinstance(v, str) else v if isinstance(v, list) else []
    return [x for x in v if isinstance(x, str)]


# Pedido 2: «cómo jugarlo», reglas de PLAN.md con su número (n = partidas detrás del número; pista = IC cruzados).
# shortcut: números copiados del PLAN a mano, al cambiar el PLAN hay que actualizarlos aquí.
R = lambda texto, numero, n, pista=False, fuente="": dict(texto=texto, numero=numero, n=n, pista=pista, fuente=fuente)
REGLAS_CHAMP = {
    "Sylas": [R("No tradees ni roamees a costa de oleadas antes del 10: 69+ minions de línea al 10.",
                "74% (32/43) con 69+ contra 32% (15/47) con 68 o menos", 90, fuente="early.py")],
    "Ekko": [R("Si pierdes la línea, cuida el farm: no más de 10 de CS abajo al 14.",
               "con la línea perdida, 69% (9/13) contra 24% (4/17)", 30, True, "linea.py"),
             R("Abajo, castiga a tu rival cuando se pase: busca el kill en tu línea.",
               "con la línea perdida, 57% con 1+ kill sobre él contra 31% con 0", 30, True, "castigo.py")],
    "Yone": [R("No necesitas ganar la línea: no fuerces tradeos, escala.",
               "con oro < 0 al 14 ganas 57% (21/37); Ekko, 43%", 37, fuente="convertir.py")],
    "Mordekaiser": [R("Busca un kill antes del 14.", "90% con 1+ kill antes del 14 contra 45% con 0", 21, True, "early.py")],
}
R_NIVEL6 = R("No salgas del 6 con un nivel abajo: tradea, pero no pierdas la carrera al 6.",
             "abajo al 6, 44% (16/36); igual, 54%; arriba, 69%", 36, True, "muertes6.py")
R_MUERTES = R("≤ 2 muertes del 14 al 25: antes de un dragón, heraldo o barón, no pelees si no hace falta.",
              "0–2 muertes del 14 al 25, 68%; 3+, 43% (282 partidas)", 282, fuente="midgame.py")
R_RIO = R("Con nivel arriba en top, no empujes pasado el río sin ver al jungla rival.",
          "pasado el río con nivel arriba mueres ×2.43 por 10 min (top/bot)", 270, fuente="nivel6.py")


def reglas(champ, pos):
    """2–3 reglas del PLAN para ese campeón y rol, la del campeón primero. No hay versión «contra este rival»: tu media
    de nivel al 6 contra él no anticipa ir abajo en la siguiente (corte6.py: 14% contra 13%)."""
    return (REGLAS_CHAMP.get(champ, []) + [R_NIVEL6, R_MUERTES] + ([R_RIO] if pos == "TOP" else []))[:3]


def ficha(rival, pos, champ=None):
    """Champ select en torno a un pick (por defecto el recomendado), como dict para la GUI (pedidos 1, 3 y 4 del Diseñador).
    por_que: el dato que justifica el pick; cuidado: tus partidas contra ese rival en el rol (cualquier campeón tuyo) contra
    tu media del rol, más notas a mano; counters: rivales de línea con peor estimado para ese campeón (3+ partidas).
    Las medidas son diferencias contra tu rival de línea; pocas = n < 5 (pista)."""
    d = datos_draft(rival, pos)
    if not d["filas"]: return None
    f = next((x for x in d["filas"] if key(x["champ"]) == key(champ)), d["filas"][0]) if champ else d["filas"][0]
    c, nombre, vs = f["champ"], d["nombre"], d["vs"]
    mv = [r for r in vs if r["champ"] == c]
    v = sum(r["win"] for r in mv)
    otro = next((x for x in d["filas"] if x is not f), None)
    rol = [g for g in games if g["pos"] == pos]
    mias = [g for g in rol if g["champ"] == c]
    p0 = shrink(sum(r["win"] for r in mias), len(mias), base)
    wr_rol = sum(r["win"] for r in mias) / len(mias)
    if len(mv) >= 3:
        frase = f"{c} va {v}-{len(mv) - v} contra {nombre} (oro @14 {gd(mv).replace('-', '−')}): estimado {f['est']:.0%}"
    else:
        frase = (f"{'Sin' if not mv else 'Casi sin'} partidas de {c} contra {nombre}"
                 f"{f' ({v}-{len(mv) - v})' if mv else ''}: el estimado {f['est']:.0%} sale de tu {wr_rol:.0%} con {c} "
                 f"en el rol ({f['n']} partidas)")
    if otro and abs(f["est"] - otro["est"]) < .02:  # 1 punto de estimado es ruido: «por encima» engañaba (54% contra 54%)
        frase += f", casi igual que {otro['champ']} ({otro['est']:.0%}): cualquiera de los dos."
    elif otro: frase += f", {'por encima' if f['est'] > otro['est'] else 'por debajo'} de {otro['champ']} ({otro['est']:.0%})."
    por_que = dict(champ=c, est=round(f["est"], 3), n_rol=f["n"], wr_rol=round(wr_rol, 3), v=v, n=len(mv),
                   oro14=medidas(mv)["oro14"], alternativa=dict(champ=otro["champ"], est=round(otro["est"], 3)) if otro else None,
                   frase=frase, pocas=len(mv) < 5)
    k = sum(r["win"] for r in vs)
    cuidado = dict(rival=nombre, v=k, wr=round(k / len(vs), 3) if vs else None, ic=[round(x, 3) for x in wilson(k, len(vs))],
                   **medidas(vs), ref=medidas(rol), notas=notas(nombre), pocas=len(vs) < 5, anticipa=list(ANTICIPA))
    por = defaultdict(list)
    for g in mias:
        if g["opp"] != "?": por[g["opp"]].append(g)
    cs = []
    for o, rs in por.items():
        w = sum(r["win"] for r in rs)
        if len(rs) < 3 or shrink(w, len(rs), p0) >= p0: continue  # solo los que te bajan del WR con ese campeón
        cs.append(dict(rival=o, v=w, wr=round(w / len(rs), 3), ic=[round(x, 3) for x in wilson(w, len(rs))],
                       est=round(shrink(w, len(rs), p0), 3), **medidas(rs), pocas=len(rs) < 5))
    cs.sort(key=lambda x: x["est"])
    return dict(champ=c, rival=nombre, pos=pos, por_que=por_que, cuidado=cuidado, reglas=reglas(c, pos),
                counters=dict(lista=cs[:3], ref=medidas(mias)))


def draft(rival, pos):
    d = datos_draft(rival, pos); nombre, vs, en = d["nombre"], d["vs"], d["en"]
    if not d["conocido"]: print(f"Aviso: {rival} no aparece en ninguna de tus partidas (¿nombre mal escrito?). Va solo tu WR por campeón.\n")
    print(f"Contra {nombre} en {pos}: {len(vs)} partidas, WR {wr(vs)}, oro @14 {gd(vs)}")
    print(f"Con {nombre} en el equipo rival (cualquier rol): {len(en)} partidas, WR {wr(en)}  (tu base: {base:.0%})\n")
    if not d["filas"]: print("No tienes partidas en ese rol."); return
    print(f"| Tu campeón | WR en {pos} | vs {nombre} (V-D) | Oro @14 vs {nombre} | Estimado |\n|---|---|---|---|---|")
    for f in d["filas"]:
        print(f"| {f['champ']} | {f['wr_rol']} | {f['vd']} | {f['oro']} | {f['est']:.0%} |")
    best = d["filas"][0]
    print(f"\nRecomendación: {best['champ']} (estimado {best['est']:.0%}). "
          f"Estimado = tu récord contra {nombre} mezclado con tu WR del campeón en el rol (pesa como {M} partidas), "
          f"que a su vez se mezcla con tu WR base.")
    if len(vs) < 5: print("Ojo: menos de 5 partidas contra este rival; la recomendación sale casi toda de tu WR general.")
    for a in d["avisos"]: print(f"Aviso: {a}")
    for l in d["build"]: print(l)


if __name__ == "__main__":  # companion.py lo importa
    if len(sys.argv) > 1:
        rol = sys.argv[2].lower() if len(sys.argv) > 2 else "mid"
        if rol not in ROLES: sys.exit(f"Rol desconocido: {rol}. Usa: {', '.join(ROLES)}")
        draft(sys.argv[1], ROLES[rol])
    else:
        guia()
