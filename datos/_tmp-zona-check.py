"""Chequeo de zone() para top/bot: ¿x+y=14800 marca bien 'pasado el río'?"""
import json, pathlib, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LINEA = {"MIDDLE", "TOP", "BOTTOM", "UTILITY"}
FIN = 14 * 60000

def zone(x, y, team):
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"

# muerte en tu línea, ¿lado propio (ZONAS[0]) o pasado el río (ZONAS[1])?
def clasif(z, linea):
    if z.startswith(linea):
        return "tu_lado" if "propio" in z else "pasado_rio"
    return None

for rol in ("TOP", "BOTTOM", "UTILITY"):
    pts = []  # (x, y, team, lado)
    for tf in (RAW / "timeline").glob("LA1_*.json"):
        mf = RAW / tf.name
        if not mf.exists(): continue
        m = json.loads(mf.read_text())["info"]
        if m["gameDuration"] < 1200: continue
        ps = m["participants"]
        me = next((p for p in ps if p["puuid"] == puuid), None)
        if not me or me["teamPosition"] != rol: continue
        fr = json.loads(tf.read_text())["info"]["frames"]
        ev = [e for f in fr for e in f["events"]]
        for e in ev:
            if e["type"] == "CHAMPION_KILL" and e["timestamp"] <= FIN and e["victimId"] == me["participantId"]:
                x, y = e["position"]["x"], e["position"]["y"]
                z = zone(x, y, me["teamId"])
                c = clasif(z, "top" if rol == "TOP" else "bot")
                if c:
                    pts.append((x, y, me["teamId"], c))
    print(f"\n== {rol}: {len(pts)} muertes en tu línea (lado propio o pasado el río) ==")
    # separa por team y lado
    for team in (100, 200):
        for lado in ("tu_lado", "pasado_rio"):
            s = [p for p in pts if p[2] == team and p[3] == lado]
            if not s: continue
            xs = [p[0] for p in s]; ys = [p[1] for p in s]
            sums = [p[0] + p[1] for p in s]
            print(f"  team {team} {lado}: n={len(s)}  x mediana {sorted(xs)[len(xs)//2]:.0f} (rango {min(xs):.0f}–{max(xs):.0f})  y mediana {sorted(ys)[len(ys)//2]:.0f} (rango {min(ys):.0f}–{max(ys):.0f})  x+y mediana {sorted(sums)[len(sums)//2]:.0f} (rango {min(sums):.0f}–{max(sums):.0f})")
