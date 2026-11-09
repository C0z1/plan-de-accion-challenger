"""Pruebas de DeepSeek para companion_gui.lineas_ficha() (turno 6, iteración 5). Sin red ni key.

Cubre los bordes que pidió Opus: ref sin medidas (rol sin timeline), counter sin cs14/oro14, ic con n=0
(¿wilson(0,0)?) con notas, y el redondeo bancario de −0.04/−0.5 (sin «−0»)."""
import pathlib, sys, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import companion_gui as g
import draft


def ref(**k):
    d = dict(n=0, oro14=None, cs14=None, xp14=None, nivel6=None, muertes6=None)
    d.update(k); return d


def cuidado(**k):
    d = dict(rival="Zed", v=0, n=0, ic=[0.0, 0.0], pocas=True,
             oro14=None, cs14=None, xp14=None, nivel6=None, muertes6=None, notas=[], ref=ref())
    d.update(k); return d


class LineasFicha(unittest.TestCase):
    def test_ref_sin_medidas_sin_media_ni_tronar(self):
        c = cuidado(n=2, v=1, ic=[0.05, 0.85], oro14=-120, cs14=-17, nivel6=-0.4, muertes6=0.5)
        cu, _ = g.lineas_ficha(dict(cuidado=c, counters=dict(ref=ref(), lista=[])))
        self.assertTrue(any("Oro al 14 −120" in x for x in cu), cu)   # el dato se muestra
        self.assertFalse(any("tu media" in x for x in cu), cu)        # sin ref, sin «(tu media …)»

    def test_counter_sin_cs_ni_oro_solo_record_y_wilson(self):
        x = dict(rival="Diana", v=0, n=3, ic=[0.0, 0.56], pocas=True, cs14=None, oro14=None)
        _, co = g.lineas_ficha(dict(cuidado=cuidado(), counters=dict(ref=ref(cs14=1, oro14=-166), lista=[x])))
        self.assertEqual(co, ["Diana 0-3 (Wilson 0%–56%); pista"])    # sin renglones de CS ni oro

    def test_n0_con_notas_solo_notas_y_wilson_00(self):
        self.assertEqual(draft.wilson(0, 0), (0.0, 0.0))  # el ic de n=0 que llega a lineas_ficha
        c = cuidado(n=0, ic=[0.0, 0.0], notas=["cuidado con la R"])
        cu, _ = g.lineas_ficha(dict(cuidado=c, counters=dict(ref=ref(), lista=[])))
        self.assertEqual(cu, ["Tu nota: cuidado con la R"])  # sin «Tú contra …» (no hay n)

    def test_menos_cero_redondeo_sin_menos(self):
        c = cuidado(n=1, v=0, ic=[0.0, 1.0], oro14=-0.5, nivel6=-0.04, ref=ref(oro14=-118, nivel6=0.1))
        cu, _ = g.lineas_ficha(dict(cuidado=c, counters=dict(ref=ref(), lista=[])))
        self.assertTrue(any("Oro al 14 +0 (tu media −118)" in x for x in cu), cu)   # −0.5 → «+0», no «−0»
        self.assertTrue(any("Nivel al 6 +0.0 (tu media +0.1)" in x for x in cu), cu)
        self.assertFalse(any("−0" in x for x in cu), cu)


if __name__ == "__main__":
    unittest.main()
