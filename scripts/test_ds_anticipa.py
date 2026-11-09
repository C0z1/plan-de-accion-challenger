"""Pruebas de DeepSeek para companion_gui.lineas_ficha() con `anticipa` (turno 6, iteración 12).

Sin red ni ventana. Cubre los bordes que dejó Opus:
(a) anticipa=["muertes6"] con muertes6 None → no sale renglón «se repite» ni truena.
(b) anticipa con las 4 medidas → no sale renglón «no se repite»."""
import pathlib, sys, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import companion_gui as g


class LineasFichaAnticipa(unittest.TestCase):
    REF = dict(n=50, oro14=-118, cs14=-3, xp14=-50, nivel6=0.0, muertes6=0.6)

    def ficha(self, **med):
        c = dict(rival="Viktor", n=8, v=1, ic=[0.02, 0.47], pocas=False,
                 oro14=-120, cs14=-17, xp14=None, nivel6=-0.04, muertes6=None,
                 ref=self.REF, notas=[], anticipa=["muertes6"])
        c.update(med)
        return dict(rival="Viktor", cuidado=c, counters=dict(lista=[], ref=self.REF))

    def test_anticipa_muertes6_pero_sin_medida_no_repite_ni_truena(self):
        # (a) la medida que anticipa falta: no debe salir «se repite», y las demás sí «no se repite»
        cu, _ = g.lineas_ficha(self.ficha())
        self.assertFalse(any("tiende a repetirse" in l for l in cu))
        self.assertTrue(any("no se repite" in l for l in cu))

    def test_anticipa_todas_no_hay_renglon_no_se_repite(self):
        # (b) todo anticipa: cada medida sale marcada «se repite» y no queda renglón «no se repite»
        cu, _ = g.lineas_ficha(self.ficha(muertes6=1.4, anticipa=["muertes6", "oro14", "cs14", "nivel6"]))
        self.assertFalse(any("no se repite" in l for l in cu))
        self.assertTrue(any("tiende a repetirse" in l for l in cu))

    def test_anticipa_vacio_marca_todo_como_no_se_repite(self):
        # sin anticipa (dict viejo), todo va al renglón «no se repite»
        cu, _ = g.lineas_ficha(self.ficha(muertes6=1.4, anticipa=[]))
        self.assertFalse(any("tiende a repetirse" in l for l in cu))
        self.assertTrue(any("no se repite" in l for l in cu))


if __name__ == "__main__":
    unittest.main()
