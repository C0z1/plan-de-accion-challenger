"""Racha comenta el draft (draft.comentario): frases de dato con tu historial, nunca órdenes ni hovers rivales."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")
import draft


def g(champ, win, opp="Zed", pos="MIDDLE", enemigos=()):
    return dict(win=win, champ=champ, pos=pos, opp=opp, enemies={opp, *enemigos}, gd14=-300, t=0)


JS = [g("Ahri", w) for w in (1, 0, 0, 0, 0, 1, 0)] + [g("Ahri", 1, "Lux") for _ in range(20)] + [g("Ekko", 1, "Lux", enemigos=("Leona",)) for _ in range(4)]


def tab(yo="Ahri", fijo=False, suyo=("Zed",), bans=()):
    return {"turno": None, "bans": {"mios": list(bans), "suyos": []},
            "mio": [{"celda": 0, "pos": "MIDDLE", "campeon": yo, "fijo": fijo, "yo": True, "eligiendo": False},
                    {"celda": 1, "pos": "UTILITY", "campeon": "Thresh", "fijo": False, "yo": False, "eligiendo": True}],
            "suyo": [{"celda": 5, "campeon": c, "eligiendo": False} for c in suyo] + [{"celda": 9, "campeon": None, "eligiendo": True}]}


class Comentario(unittest.TestCase):
    def com(self, t, rival=None):
        with mock.patch.object(draft, "games", JS), mock.patch.object(draft, "base", .6):
            return draft.comentario(t, "MIDDLE", rival)

    def test_vacio(self):
        self.assertEqual(self.com(None), []); self.assertEqual(self.com({}), [])

    def test_frases(self):
        c = {x["clave"]: x["texto"] for x in self.com(tab(fijo=True, bans=("Zed",)), "Zed")}
        self.assertEqual(c["cruce:Ahri:Zed"], "Con Ahri contra Zed: 2-5, oro al 14 -300")
        self.assertIn("Tu Ahri en mid", c["tuyo:Ahri"])
        self.assertEqual(c["ban_cruce:Zed"], "Zed está en los bans: vas 2-5 contra Zed en mid")

    def test_rival_fijado_y_umbral(self):
        c = {x["clave"]: x["texto"] for x in self.com(tab(suyo=("Zed", "Leona")))}
        self.assertEqual(c["rival:Zed"], "Contra Zed en el equipo rival: 2-5")
        self.assertIn("rival:Leona", c)  # 4 partidas con Leona enfrente
        self.assertNotIn("rival:Thresh", c)  # aliado en hover: no se comenta

    def test_pool_baneado(self):
        c = {x["clave"] for x in self.com(tab(yo=None, suyo=(), bans=("Ahri",)))}
        self.assertIn("ban_pool:Ahri", c)

    def test_sin_ordenes_ni_hovers(self):
        for t in (tab(fijo=True, bans=("Zed", "Ahri"), suyo=("Zed", "Leona", "Lux")), tab()):
            r = self.com(t, "Zed")
            self.assertLessEqual(len(r), 4); self.assertEqual(len({x["clave"] for x in r}), len(r))
            for x in r:
                for v in ("banea ", "elige", "cambia", "evita", "pickea", "Alternativa", "None"): self.assertNotIn(v, x["texto"])

    def test_estable(self):
        self.assertEqual(self.com(tab(), "Zed"), self.com(tab(), "Zed"))


if __name__ == "__main__":
    unittest.main()
