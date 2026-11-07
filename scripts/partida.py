"""Replay en datos de una partida: minuto a minuto del 12 al 26 (oro, zona, eventos) para revisar decisiones.
Uso:
  python scripts/partida.py                 lista tus últimas 15 derrotas con la línea ganada al 14 (oro >= 0)
  python scripts/partida.py LA1_1759165331  narra esa partida
  python scripts/partida.py --ultimas 8     narra las últimas 8 derrotas con la línea ganada
Las posiciones de los demás jugadores son por minuto (foto del frame), no del instante exacto."""
import json, math, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
DESDE, HASTA, CERCA = 12, 26, 2500  # minutos, unidades del mapa
CONTROL = 2055  # itemId del control ward


def zone(x, y, team):  # misma función que scripts/timeline.py
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"
assert zone(7000, 7000, 100) == "mid (lado propio)" and zone(500, 500, 200) == "base rival"


def mmss(ms): return f"{ms // 60000:02d}:{ms // 1000 % 60:02d}"
assert mmss(754_000) == "12:34"


def cargar(mid):
    m = json.loads((RAW / f"{mid}.json").read_text())["info"]
    fr = json.loads((RAW / "timeline" / f"{mid}.json").read_text())["info"]["frames"]
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    return m, fr, ps, me, opp


def candidatas():
    out = []
    for tf in (RAW / "timeline").glob("LA1_*.json"):
        if not (RAW / tf.name).exists(): continue
        m, fr, ps, me, opp = cargar(tf.stem)
        if m["gameDuration"] < 1200 or not opp or me["win"] or len(fr) <= 14: continue
        g = lambda i: fr[14]["participantFrames"][str(i)]["totalGold"]
        gd = g(me["participantId"]) - g(opp["participantId"])
        if gd >= 0: out.append((m["gameCreation"], tf.stem, me["championName"], opp["championName"], gd, m["gameDuration"]))
    return sorted(out, reverse=True)


def narrar(mid):
    m, fr, ps, me, opp = cargar(mid)
    pid, team = me["participantId"], me["teamId"]
    nom = {p["participantId"]: ("tú" if p is me else ("aliado " if p["teamId"] == team else "rival ") + p["championName"])
           for p in ps}
    aliados = {p["participantId"] for p in ps if p["teamId"] == team}
    pf = lambda mn, i: fr[min(mn, len(fr) - 1)]["participantFrames"][str(i)]
    pos = lambda mn, i: (pf(mn, i)["position"]["x"], pf(mn, i)["position"]["y"])
    eq = lambda mn: sum(pf(mn, p["participantId"])["totalGold"] * (1 if p["teamId"] == team else -1) for p in ps)
    print(f"\n## {mid} · {me['championName']} {me['teamPosition']} contra {opp['championName']} · derrota "
          f"en {m['gameDuration'] // 60} min · KDA {me['kills']}/{me['deaths']}/{me['assists']}\n")
    print("| min | tu zona | oro vs rival | oro equipo | CS | aliados a < 2500 | rivales a < 2500 |\n|---|---|---|---|---|---|---|")
    for mn in range(DESDE, min(HASTA, len(fr) - 1) + 1):
        x, y = pos(mn, pid)
        cerca = lambda grupo: sum(math.dist((x, y), pos(mn, i)) < CERCA for i in grupo if i != pid)
        rivales = set(nom) - aliados
        cs = pf(mn, pid)["minionsKilled"] + pf(mn, pid)["jungleMinionsKilled"]
        print(f"| {mn} | {zone(x, y, team)} | {pf(mn, pid)['totalGold'] - pf(mn, opp['participantId'])['totalGold']:+} "
              f"| {eq(mn):+} | {cs} | {cerca(aliados)} | {cerca(rivales)} |")
    print("\n**Eventos**")
    for f in fr:
        for e in f["events"]:
            t = e["timestamp"]
            if not DESDE * 60000 <= t <= HASTA * 60000: continue
            if e["type"] == "CHAMPION_KILL":
                p = e["position"]; ayuda = [nom[i] for i in e.get("assistingParticipantIds", [])]
                yo = pid in (e["victimId"], e["killerId"], *e.get("assistingParticipantIds", []))
                marca = "**MUERES**" if e["victimId"] == pid else ("**participas**" if yo else "")
                mn = t // 60000
                ali = sum(math.dist((p["x"], p["y"]), pos(mn, i)) < CERCA for i in aliados if i != pid)
                extra = f" (aliados cerca en el frame {mn}: {ali})" if e["victimId"] == pid else ""
                txt = (f"- {mmss(t)} {nom.get(e['killerId'], 'torre/minion')} mata a {nom[e['victimId']]}"
                       f"{' con ' + ', '.join(ayuda) if ayuda else ''} en {zone(p['x'], p['y'], team)} {marca}{extra}")
                print(txt.replace("tú mata a", "matas a").replace("mata a tú", "te mata"))
            elif e["type"] == "ELITE_MONSTER_KILL":
                quien = "tu equipo" if e.get("killerTeamId") == team else "el rival"
                print(f"- {mmss(t)} {quien} toma {e.get('monsterSubType') or e['monsterType']}")
            elif e["type"] == "BUILDING_KILL":
                quien = "pierdes" if e["teamId"] == team else "tu equipo toma"
                print(f"- {mmss(t)} {quien} {e.get('towerType') or e['buildingType']} de {e['laneType']}")
            elif e.get("participantId") == pid and e["type"] == "ITEM_PURCHASED" and e["itemId"] == CONTROL:
                print(f"- {mmss(t)} compras control ward")
            elif e.get("creatorId") == pid and e["type"] == "WARD_PLACED" and e["wardType"] == "CONTROL_WARD":
                print(f"- {mmss(t)} pones control ward")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print("| partida | campeón | rival | oro @14 | min |\n|---|---|---|---|---|")
        for _, mid, c, o, gd, dur in candidatas()[:15]: print(f"| {mid} | {c} | {o} | {gd:+} | {dur // 60} |")
    elif a[0] == "--ultimas":
        for _, mid, *_ in candidatas()[:int(a[1]) if len(a) > 1 else 8]: narrar(mid)
    else:
        narrar(a[0])
