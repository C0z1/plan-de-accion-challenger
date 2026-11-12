"""Pruebas del hallazgo 24 (DeepSeek, ronda 4): al salir de InProgress/Reconnect, evento(('fase', X)) lanza un hilo
con vistas_previas(ESTADO['rendimiento']) para que «Tu última partida» sea la que acaba de terminar.
Sin red, sin cliente de LoL ni key: vistas_previas y threading.Thread van mockeados (el hilo corre síncrono)."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixtures de draft

import companion_web as w  # noqa: E402


class Ultima(unittest.TestCase):
    def setUp(self):
        self.viejo = dict(w.ESTADO); self.cuenta = w.gui.CUENTA[0]

    def tearDown(self):
        w.ESTADO.clear(); w.ESTADO.update(self.viejo); w.gui.CUENTA[0] = self.cuenta

    def evento_fase(self, antes, despues):
        w.ESTADO["fase"] = antes
        w.ESTADO["rendimiento"] = "R"
        hilos = []
        def hilo(target, args=(), daemon=False):
            hilos.append((target, args, daemon)); target(*args); return mock.Mock()  # síncrono: sin esperar al hilo real
        with mock.patch.object(w, "vistas_previas") as vp, \
             mock.patch.object(w.companion, "pantalla_completa", return_value=False), \
             mock.patch.object(w.threading, "Thread", hilo):
            w.evento(("fase", despues))
        return vp, hilos

    def test_inprogress_a_none_llama_1(self):
        vp, hilos = self.evento_fase("InProgress", None)
        self.assertEqual(vp.call_count, 1)
        self.assertEqual(hilos, [(vp, ("R",), True)])

    def test_reconnect_a_none_llama_1(self):
        vp, hilos = self.evento_fase("Reconnect", None)
        self.assertEqual(vp.call_count, 1)
        self.assertEqual(hilos, [(vp, ("R",), True)])

    def test_inprogress_a_reconnect_0(self):
        vp, hilos = self.evento_fase("InProgress", "Reconnect")
        self.assertEqual(vp.call_count, 0)
        self.assertEqual(hilos, [])

    def test_none_a_champselect_0(self):
        vp, hilos = self.evento_fase(None, "ChampSelect")
        self.assertEqual(vp.call_count, 0)
        self.assertEqual(hilos, [])

    def test_inprogress_a_endofgame_1(self):
        vp, hilos = self.evento_fase("InProgress", "EndOfGame")
        self.assertEqual(vp.call_count, 1)
        self.assertEqual(hilos, [(vp, ("R",), True)])


if __name__ == "__main__":
    unittest.main()
