"""Pruebas de DeepSeek para score.tilt() (turno 6, iteración 4). Sin red ni key.

Cubre los bordes que pidió Opus: 0 partidas, dos partidas a exactamente 90 min (el corte de sesión es `>`)
y una sesión que cruza la medianoche (hoy solo trae las de hoy, pero la racha cuenta la misma sesión)."""
import pathlib, sys, unittest
from datetime import date, datetime
from unittest import mock

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import score


def ts(y, mo, d, h, mi):
    return datetime(y, mo, d, h, mi).timestamp() * 1000  # naive = hora local


def g(t, win, champ="Ekko", sc=50.0):
    return dict(t=t, win=win, champ=champ, score=sc)


class Tilt(unittest.TestCase):
    def _tilt(self, gs, hoy=date(2026, 11, 8)):
        with mock.patch.object(score, "partidas", return_value=(gs, None, None)):
            return score.tilt(hoy=hoy)

    def test_sin_partidas_no_truena(self):
        t = self._tilt([])
        self.assertEqual(t["hoy"], [])
        self.assertEqual((t["tras2"]["n"], t["tras2"]["wr"], t["tras2"]["ic"]), (0, None, (0.0, 0.0)))
        self.assertEqual((t["base"]["n"], t["base"]["wr"]), (0, None))
        self.assertEqual((t["racha"], t["llegas"]), (0, 0))
        self.assertTrue(t["pocas"])  # n=0 < 20

    def test_dos_a_90_min_exactos_son_la_misma_sesion(self):
        t0 = ts(2026, 11, 8, 12, 0)
        t = self._tilt([g(t0, False), g(t0 + score.SESION, False)])  # corte es `>`, no `>=`
        self.assertEqual((t["llegas"], t["racha"]), (1, 2))  # misma sesión: llegaste a 2 seguidas

    def test_sesion_que_cruza_la_medianoche(self):
        gs = [g(ts(2026, 11, 7, 23, 50), False), g(ts(2026, 11, 8, 0, 10), False), g(ts(2026, 11, 8, 0, 30), False)]
        t = self._tilt(gs)
        self.assertEqual(len(t["hoy"]), 2)   # hoy solo trae las de hoy
        self.assertEqual(t["racha"], 3)      # la racha cuenta la de ayer: es la misma sesión (bien)


if __name__ == "__main__":
    unittest.main()
