"""DS-5 (ronda 4): la pausa del juego (gameTime que no avanza entre fotos) sale de evento(('meta', …)) en companion_web
y congela overlay.partes. Sin red ni ventana. Los t ya vienen int(gameTime), como los manda companion.meta_fase."""
import unittest

import companion_web as w


def meta(t=122, minuto=2):
    """Un meta_fase mínimo para evento(('meta', …)) y overlay.partes."""
    return {"minuto": minuto, "campeon": "Ekko", "nivel": 6, "rival": "Zed", "nivel_rival": 7, "cs": 52, "cs_meta": None,
            "muertes14": None, "objetivos": {"dragon": 400, "baron": None}, "t": t}


class Pausa(unittest.TestCase):
    def setUp(self):
        self.viejo = dict(w.ESTADO)

    def tearDown(self):
        w.ESTADO.clear()
        w.ESTADO.update(self.viejo)

    def _evento(self, t=122, minuto=2):
        w.evento(("meta", meta(t, minuto)))

    def test_122_a_123_es_pausa(self):
        """Un temblor que cruza el segundo entero (122→123) sigue contando como pausa."""
        w.ESTADO["meta"] = meta(122)
        self._evento(123)
        self.assertTrue(w.ESTADO["meta"]["pausa"])

    def test_122_a_122_es_pausa(self):
        w.ESTADO["meta"] = meta(122)
        self._evento(122)
        self.assertTrue(w.ESTADO["meta"]["pausa"])

    def test_122_a_132_no_es_pausa(self):
        w.ESTADO["meta"] = meta(122)
        self._evento(132)
        self.assertFalse(w.ESTADO["meta"]["pausa"])

    def test_primera_foto_no_es_pausa(self):
        w.ESTADO["meta"] = None
        self._evento(122)
        self.assertFalse(w.ESTADO["meta"]["pausa"])

    def test_t_none_no_es_pausa(self):
        w.ESTADO["meta"] = meta(122)
        w.evento(("meta", meta(None)))
        self.assertFalse(w.ESTADO["meta"]["pausa"])



if __name__ == "__main__":
    unittest.main()
