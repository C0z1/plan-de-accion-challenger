"""Pruebas de DeepSeek para draft.ficha() (turno 6, iteración 1). Sin red ni key.

Cubre los bordes que pidió Opus: rival con alias o apóstrofo en las notas y en `rival`,
un `champ` fuera del pool del rol (cae al recomendado) y partidas sin timeline mezcladas
con otras con timeline (las medias salen solo de las que tienen la medida)."""
import pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import draft


def g(champ, win, opp="Zed", pos="MIDDLE", **med):
    d = dict(win=win, champ=champ, pos=pos, opp=opp, enemies={opp}, gd14=None, t=0)
    d.update(med)
    return d


class Ficha(unittest.TestCase):
    def ficha(self, juegos, rival, champ=None, notas=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(draft, "games", juegos), \
                mock.patch.object(draft, "base", .5), mock.patch.object(draft, "NOTAS", pathlib.Path(tmp) / "notas.json"):
            if notas is not None: draft.NOTAS.write_text(notas, encoding="utf-8")
            return draft.ficha(rival, "MIDDLE", champ)

    def test_alias_y_apostrofo_en_rival_y_notas(self):
        # Riot llama MonkeyKing a Wukong y Kai'Sa lleva apóstrofo: el rival «wukong»/«Kai'Sa»
        # debe casar con el opp y con las claves de notas vía key() (alias + alfanumérico).
        js = [g("Ekko", True, "MonkeyKing") for _ in range(5)] + [g("Ekko", i < 3, "Kai'Sa") for i in range(4)]
        notas = '{"Wukong": "no pelees al 6", "Kai\'Sa": ["cuidado con la R", "empuja lento"]}'
        fw = self.ficha(js, "wukong", notas=notas)
        fk = self.ficha(js, "Kai'Sa", notas=notas)
        self.assertEqual(fw["rival"], "MonkeyKing")
        self.assertEqual(fw["cuidado"]["notas"], ["no pelees al 6"])
        self.assertEqual(fk["rival"], "Kai'Sa")
        self.assertEqual(fk["cuidado"]["notas"], ["cuidado con la R", "empuja lento"])

    def test_champ_fuera_del_pool_cae_al_recomendado(self):
        js = [g("Ekko", i < 4) for i in range(6)] + [g("Yone", i < 3) for i in range(5)]
        f = self.ficha(js, "Zed", champ="Riven")  # Riven no está en tu pool: debe caer al mejor estimado
        self.assertEqual(f["champ"], "Ekko")

    def test_medias_solo_con_las_que_tienen_timeline(self):
        # 5 partidas contra Zed, 3 con timeline y 2 sin él: n=5, pero las medidas salen de las 3.
        js = [g("Ekko", i < 2, "Zed", gd14=100, cs14=5, xp14=50, nivel6=1, muertes6=0) for i in range(3)]
        js += [g("Ekko", False, "Zed"), g("Ekko", True, "Zed")]  # sin timeline: gd14 None y sin el resto
        c = self.ficha(js, "Zed")["cuidado"]
        self.assertEqual(c["n"], 5)
        self.assertEqual((c["oro14"], c["cs14"], c["xp14"], c["nivel6"], c["muertes6"]), (100.0, 5.0, 50.0, 1.0, 0.0))


if __name__ == "__main__":
    unittest.main()
