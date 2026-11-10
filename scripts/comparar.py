"""Tú contra el onetrick del top: compara tu build y tus números con la de los onetricks del top
guardada en datos/meta/builds.json (la que dejó `builds.py --pool`).
Uso: python scripts/comparar.py <Campeón> [rol]   (rol: top, mid, jungla, bot, support; sin rol, la que haya)

`diferencias` y `frase` son puras; `comparar` lee builds.json sin red y devuelve {difs, frase} o None."""
import json, sys

import builds

if __name__ == "__main__": sys.stdout.reconfigure(encoding="utf-8")

TEMAS = ("primer ítem", "core", "botas", "runa", "habilidades")
VERBO = {"primer ítem": "abren", "core": "arman", "botas": "usan", "runa": "llevan", "habilidades": "suben"}


def _valor(r, tema):
    """El valor legible de un tema en un resumen de builds.resumir, o None si falta ese dato."""
    if tema == "primer ítem":
        core = r.get("core")
        return core[0][0] if core else None
    if tema == "core":
        core = r.get("core")
        return " → ".join(c[0] for c in core) if core else None
    if tema == "botas":
        b = r.get("botas")
        return b[0] if b else None
    if tema == "runa":
        ru = r.get("runa")
        return ru[0] if ru else None
    sk = r.get("skills")  # habilidades
    return sk[0] if sk else None


def diferencias(mejores, tuya):
    """[{tema, ellos, tu, igual}] solo con los temas presentes en ambas builds."""
    out = []
    for tema in TEMAS:
        e, t = _valor(mejores, tema), _valor(tuya, tema)
        if e is None or t is None: continue
        out.append({"tema": tema, "ellos": e, "tu": t, "igual": e == t})
    return out


def frase(difs, primer=None):
    """1–2 frases en segunda persona con lo que difiere y, si hay `primer`, tu récord con su primer ítem. Sin causas."""
    ds = [d for d in difs if not d["igual"]]
    if not ds:
        txt = "Tu build es igual a la de los onetricks del top."
    else:
        partes = [f"Ellos {VERBO[ds[0]['tema']]} {ds[0]['ellos']}; tú, {ds[0]['tu']}"]
        partes += [f"ellos {VERBO[d['tema']]} {d['ellos']}; tú, {d['tu']}" for d in ds[1:]]
        txt = "; ".join(partes) + "."
    if primer and primer.get("si") and primer["si"][1]:
        txt += f" Con su primer ítem vas {primer['si'][0]}/{primer['si'][1]}."
    return txt


def comparar(campeon, pos=None):
    """{difs, frase} de «Campeón|pos» contra «Campeón|pos|tu» en builds.json, o None si falta algo o el JSON está roto."""
    try:
        d = json.loads((builds.META / "builds.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for k, mejores in d.items():
        if k.count("|") != 1: continue
        c, p = k.split("|", 1)
        if c.lower() != campeon.lower(): continue
        if pos and p.lower() != pos.lower(): continue
        tuya = d.get(k + "|tu")
        if not tuya: return None
        difs = diferencias(mejores, tuya)
        return {"difs": difs, "frase": frase(difs, mejores.get("primer"))}
    return None


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    campeon = sys.argv[1]
    rol = sys.argv[2].lower() if len(sys.argv) > 2 else None
    if rol and rol not in builds.ROLES: sys.exit(f"Rol desconocido: {rol}. Usa: {', '.join(builds.ROLES)}")
    r = comparar(campeon, builds.ROLES.get(rol))
    if not r:
        sys.exit(f"Sin comparación para {campeon}{' (' + rol + ')' if rol else ''}: corre `builds.py --pool` con key, o falta tu build.")
    print(r["frase"])
