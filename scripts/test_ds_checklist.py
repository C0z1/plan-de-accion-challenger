"""Pruebas de DeepSeek del checklist de prueba en partida (turno 9 iter 9): coteja cada texto citado entre «» contra la página,
y verifica el estado de EndOfGame sin key y la primera meta en partida. Sin red ni ventanas."""
import pathlib, queue, unittest
from unittest import mock

import companion_gui as gui
import companion_web as w

HTML = (pathlib.Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


class ChecklistTextos(unittest.TestCase):
    """(a) Los textos del checklist de PIZARRON «Para el usuario» existen tal cual en la página."""
    TEXTOS = [
        "Cliente conectado",
        "Esperando su pick…",
        "Hasta el nivel 6",
        "Tu plan con",
        "Cumples",
        "Cargando partida",
        "Esperando los datos en vivo",
        "Muertes desde el 14",
        "Muertes del 14 al 25",
        "Tu rival",
        "Objetivos",
        "Al terminar (foto en vivo)",
        "No cuadran tus muertes con los eventos",
        "Esta vista falló",
    ]

    def test_todos_los_textos_estan(self):
        for t in self.TEXTOS:
            self.assertIn(t, HTML, f"«{t}» no está en index.html")


class EndOfGameSinKey(unittest.TestCase):
    """(b) En EndOfGame sin key, revision queda None y fin se llena; la vista es En vivo (router)."""
    def setUp(self):
        self.prev = dict(w.ESTADO)

    def tearDown(self):
        w.ESTADO.clear(); w.ESTADO.update(self.prev)

    def test_revision_none_y_fin_puesto(self):
        w.ESTADO.update({"fase": "inicio", "revision": None, "fin": None})
        w.evento(("fase", "EndOfGame"))  # sin key: post_partida no produce evento "revision"
        w.evento(("fin", {"minuto": 31, "campeon": "Sylas", "kda": "5/4/7", "rival": "Zed", "cs": 245,
                          "muertes14_25": 3, "cotejo": True}))
        self.assertIsNone(w.ESTADO["revision"])
        self.assertIsNotNone(w.ESTADO["fin"])
        self.assertEqual(w.ESTADO["fin"]["campeon"], "Sylas")

    def test_end_of_game_va_a_en_vivo(self):
        # router: EN_PARTIDA incluye EndOfGame y (fase en partida | fin | revision) -> "envivo"
        self.assertIn('const EN_PARTIDA = ["GameStart", "InProgress", "Reconnect", "WaitingForStats", "PreEndOfGame", "EndOfGame"]', HTML)
        self.assertIn('EN_PARTIDA.includes(s.fase) || s.fin || s.revision ? "envivo"', HTML)


class PrimeraMetaEnPartida(unittest.TestCase):
    """(c) La primera meta llega en la primera vuelta de InProgress (con ult=0 no espera los 30 s)."""
    def test_meta_en_la_primera_vuelta(self):
        q = queue.Queue()
        meta = {"minuto": 10, "campeon": "Sylas", "nivel": 5, "rival": "Zed", "nivel_rival": 6, "cs": 69, "cs_meta": None, "muertes14": 0}
        with mock.patch.object(gui.companion, "lcu", return_value="InProgress"), \
                mock.patch.object(gui.companion, "vivo", return_value={"gameData": {"gameTime": 600}}), \
                mock.patch.object(gui.companion, "meta_fase", return_value=meta), \
                mock.patch.object(gui.companion, "capturar", return_value=("x", 0)), \
                mock.patch.object(gui.companion, "aviso_nivel", return_value=None), \
                mock.patch.object(gui.companion, "aviso_minions", return_value=None), \
                mock.patch.object(gui.companion, "aviso_muertes", return_value=None), \
                mock.patch.object(gui.companion, "espera", return_value=0), \
                mock.patch.object(gui.time, "sleep", side_effect=SystemExit):  # una vuelta y fuera
            with self.assertRaises(SystemExit):
                gui.trabajador(q)
        self.assertIn("meta", [q.get()[0] for _ in range(q.qsize())])
