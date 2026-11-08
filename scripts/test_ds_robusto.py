"""Pruebas de DeepSeek para companion_gui.trabajador (turno 4, iteración 3). Sin red, cliente ni ventana."""
import pathlib, queue, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import companion_gui as g


def lcu_de(*fases):
    """lcu() que devuelve cada fase y, al acabarse, corta con KeyboardInterrupt (no lo atrapa el except Exception)."""
    it = iter(fases)
    def lcu(path):
        try: return next(it)
        except StopIteration: raise KeyboardInterrupt
    return lcu


class TrabajadorRobusto(unittest.TestCase):
    def setUp(self):
        c = g.companion
        self.orig = c.lcu, c.vivo, c.capturar, c.aviso_nivel, g.time.sleep, g.time.time, g.post_partida

    def tearDown(self):
        c = g.companion
        c.lcu, c.vivo, c.capturar, c.aviso_nivel, g.time.sleep, g.time.time, g.post_partida = self.orig

    def test_reinicio_a_media_partida_mismo_archivo_y_un_aviso(self):
        c = g.companion
        reloj = iter(range(0, 10000, 100))
        archivos = []
        descargas = []
        c.lcu = lcu_de("InProgress", None, None, "InProgress")
        c.vivo = lambda: {"gameData": {"gameTime": 360}}
        c.aviso_nivel = lambda d: "vas abajo de nivel"
        def capturar(a, f):
            r = a if a is not None else ["archivo"]  # como companion.capturar: crea solo si viene None
            archivos.append(r); return r
        c.capturar = capturar
        g.time.sleep = lambda s: None
        g.time.time = lambda: next(reloj)
        g.post_partida = lambda q: descargas.append(1)
        q = queue.Queue()
        with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        self.assertEqual(descargas, [])
        self.assertEqual(len([e for e in list(q.queue) if e[0] == "aviso"]), 1)
        self.assertGreaterEqual(len(archivos), 2)
        self.assertTrue(all(a is archivos[0] for a in archivos))

    def test_reinicio_en_endofgame_no_duplica_la_descarga(self):
        c = g.companion
        descargas = []
        c.lcu = lcu_de("EndOfGame", None, "EndOfGame")
        g.time.sleep = lambda s: None
        g.post_partida = lambda q: descargas.append(1)
        q = queue.Queue()
        with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        self.assertEqual(descargas, [1])

    def test_esperas_crecen_3_6_12_con_cliente_caido(self):
        c = g.companion
        esperas = []
        c.lcu = lcu_de("Lobby", None, None)
        g.time.sleep = lambda s: esperas.append(s)
        q = queue.Queue()
        with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        self.assertEqual(esperas, [3, 6, 12])


if __name__ == "__main__":
    unittest.main()
