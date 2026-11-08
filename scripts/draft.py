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
        if len(fr) > 14:
            pf = fr[14]["participantFrames"]
            g["gd14"] = pf[str(me["participantId"])]["totalGold"] - pf[str(opp["participantId"])]["totalGold"]
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
