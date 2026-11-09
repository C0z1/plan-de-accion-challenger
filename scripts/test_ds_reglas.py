"""Pruebas de DeepSeek para draft.reglas()/ficha()["reglas"] (turno 6, iteración 3). Sin red ni key.

Cubre los bordes que pidió Opus: campeón fuera de la tabla en top (las 3 generales), nivel6 = 0/None
(la del 6 no sube) y que el `contra` solo aparezca con 3+ partidas contra el rival."""
import pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import draft


class Reglas(unittest.TestCase):
    def test_campeon_fuera_de_la_tabla_en_top_da_las_3_generales(self):
        r = draft.reglas("Riven", "TOP")
        self.assertEqual([x["fuente"] for x in r], ["muertes6.py", "midgame.py", "nivel6.py"])

    def test_nivel6_cero_o_none_no_sube_la_del_6(self):
        for nv in (0, None):
            r = draft.reglas("Sylas", "MIDDLE", nv)
            self.assertEqual([x["fuente"] for x in r], ["early.py", "muertes6.py", "midgame.py"])
            self.assertFalse(any("contra" in x for x in r))

    def test_nivel6_negativo_sube_la_del_6_con_contra_al_frente(self):
        r = draft.reglas("Sylas", "MIDDLE", -0.4)
        self.assertEqual([x["fuente"] for x in r], ["muertes6.py", "early.py", "midgame.py"])
        self.assertIn("-0.4", r[0]["contra"])

    def test_ficha_con_menos_de_3_partidas_no_mete_contra(self):
        def g(champ, win, opp, **med):
            d = dict(win=win, champ=champ, pos="MIDDLE", opp=opp, enemies={opp}, gd14=None, t=0)
            d.update(med); return d
        js = [g("Sylas", True, "Zed", nivel6=-1) for _ in range(2)] + [g("Sylas", i < 5, "Ahri") for i in range(8)]
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(draft, "games", js), \
                mock.patch.object(draft, "base", .5), mock.patch.object(draft, "NOTAS", pathlib.Path(tmp) / "n.json"):
            f = draft.ficha("Zed", "MIDDLE")
        self.assertFalse(any("contra" in x for x in f["reglas"]))


if __name__ == "__main__":
    unittest.main()
