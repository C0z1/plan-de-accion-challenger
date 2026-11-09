"""Pruebas de DeepSeek para draft.reglas()/ficha()["reglas"] (turno 6, iteración 11). Sin red ni key.

Tras corte6.py, la regla del 6 dejó de subir al frente con «contra este rival…» (era ruido):
reglas(champ, pos) ya no recibe nivel6 y ninguna regla trae «contra»."""
import pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import draft


class Reglas(unittest.TestCase):
    def test_campeon_fuera_de_la_tabla_en_top_da_las_3_generales(self):
        r = draft.reglas("Riven", "TOP")
        self.assertEqual([x["fuente"] for x in r], ["muertes6.py", "midgame.py", "nivel6.py"])
        self.assertFalse(any("contra" in x for x in r))

    def test_reglas_sin_nivel6_y_sin_contra(self):
        r = draft.reglas("Sylas", "MIDDLE")
        self.assertEqual([x["fuente"] for x in r], ["early.py", "muertes6.py", "midgame.py"])
        self.assertFalse(any("contra" in x for x in r))

    def test_ficha_con_nivel6_negativo_no_cambia_el_orden(self):
        def g(champ, win, opp, **med):
            d = dict(win=win, champ=champ, pos="MIDDLE", opp=opp, enemies={opp}, gd14=None, t=0)
            d.update(med); return d
        # 3+ contra Zed con nivel6 −1: antes subía la del 6 con «contra»; ahora no cambia nada.
        js = [g("Sylas", i < 2, "Zed", nivel6=-1) for i in range(3)] + [g("Sylas", i < 5, "Ahri") for i in range(8)]
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(draft, "games", js), \
                mock.patch.object(draft, "base", .5), mock.patch.object(draft, "NOTAS", pathlib.Path(tmp) / "n.json"):
            f = draft.ficha("Zed", "MIDDLE")
        self.assertEqual([x["fuente"] for x in f["reglas"]], ["early.py", "muertes6.py", "midgame.py"])
        self.assertFalse(any("contra" in x for x in f["reglas"]))


if __name__ == "__main__":
    unittest.main()
