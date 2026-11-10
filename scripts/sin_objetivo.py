"""¿«Morir 14–25 sin objetivo» (vistas.errores) separa V/D? Compara la ventana de solo después (0..+60 s)
con ±60 s (morir asegurando o robando un objetivo de tu equipo no es error): momentos, partidas de las
últimas 20 y WR por número de momentos en todas tus partidas con timeline."""
import json, sys
import score
from score import wilson


def momentos(g, antes):
    tf = g["f"].parent / "timeline" / g["f"].name
    try:
        fr = json.loads(tf.read_text())["info"]["frames"]; info = json.loads(g["f"].read_text())["info"]
    except (OSError, ValueError, KeyError):
        return None
    yo = g["pid"]; eq = next(p for p in info["participants"] if p["participantId"] == yo)["teamId"]
    ev = [e for f in fr for e in f["events"]]
    obj = [e["timestamp"] for e in ev if (e["type"] == "ELITE_MONSTER_KILL" and e.get("killerTeamId") == eq)
           or (e["type"] == "BUILDING_KILL" and e.get("teamId") not in (None, eq))]
    return sum(1 for e in ev if e["type"] == "CHAMPION_KILL" and e.get("victimId") == yo
               and 14 * 60000 <= e["timestamp"] < 25 * 60000
               and not any(-antes <= t - e["timestamp"] <= 60000 for t in obj))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    gs = score.partidas()[0]
    for antes, nombre in ((0, "0..+60 s (hoy)"), (60000, "±60 s")):
        r = [(c, g["win"]) for g in gs if (c := momentos(g, antes)) is not None]
        print(f"## {nombre}: {sum(c for c, _ in r)} momentos en {len(r)} partidas; "
              f"últimas 20 con 1+: {sum(c > 0 for c, _ in r[-20:])}/20")
        for et, f in (("0", lambda c: c == 0), ("1", lambda c: c == 1), ("2+", lambda c: c >= 2)):
            s = [w for c, w in r if f(c)]
            if s:
                lo, hi = wilson(sum(s), len(s))
                print(f"- {et}: {sum(s)}/{len(s)} = {sum(s) / len(s):.0%} ({lo:.0%}–{hi:.0%})")
