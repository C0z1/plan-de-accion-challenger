"""Recorrido de champ select con datos reales: ficha() contra tus rivales más frecuentes de un rol, en texto, para leerla
como la vería el usuario: `recorrido_ficha.py [rol] [N]`."""
import collections, sys
import draft
from companion_gui import lineas_ficha

pos = draft.ROLES.get((sys.argv[1] if len(sys.argv) > 1 else "mid").lower(), "MIDDLE")
n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
for rival, k in collections.Counter(g["opp"] for g in draft.games if g["pos"] == pos).most_common(n):
    f = draft.ficha(rival, pos)
    print(f"\n=== {rival} ({k} partidas) ===")
    if not f: print("(sin ficha)"); continue
    print("Por qué:", f["por_que"]["frase"])
    for r in f["reglas"]: print("Regla:", r["texto"], "·", r["numero"])
    cuidado, counters = lineas_ficha(f)
    for l in cuidado: print("Cuidado:", l)
    for l in counters: print(f"Counter de {f['por_que']['champ']}:", l)
