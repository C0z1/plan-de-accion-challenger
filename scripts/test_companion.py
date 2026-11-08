"""python -m unittest discover scripts  (sin red ni key)"""
import json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import companion

FIX = pathlib.Path(__file__).parent / "fixtures"


def sesion(nombre): return json.loads((FIX / nombre / "session.json").read_text())


class Rivales(unittest.TestCase):
    def test_rival_de_tu_posicion(self):
        self.assertEqual(companion.rivales(sesion("champselect")), ("MIDDLE", [112]))  # Viktor mid, no Graves

    def test_sin_rol_van_todos_los_elegidos(self):
        self.assertEqual(companion.rivales(sesion("champselect-sin-rol")), ("TOP", [64, 238]))

    def test_nadie_elegido(self):
        self.assertEqual(companion.rivales({"localPlayerCellId": 0, "myTeam": [], "theirTeam": []}), ("MIDDLE", []))

    def test_fase_del_fixture(self):
        self.assertEqual(json.loads((FIX / "champselect" / "gameflow-phase.json").read_text()), "ChampSelect")


class PostPartida(unittest.TestCase):
    def setUp(self):
        self.orig = companion.lcu, companion.post_partida, companion.time.sleep, companion.subprocess.run

    def tearDown(self):
        companion.lcu, companion.post_partida, companion.time.sleep, companion.subprocess.run = self.orig

    def test_end_of_game_dispara_una_vez(self):
        fases = iter(["InProgress", "PreEndOfGame", "EndOfGame", "EndOfGame", "Lobby"])
        llamadas = []
        companion.lcu = lambda path: next(fases)  # al acabarse las fases, StopIteration corta el bucle
        companion.post_partida = lambda: llamadas.append(1)
        companion.time.sleep = lambda _: None
        with self.assertRaises(StopIteration): companion.main()
        self.assertEqual(llamadas, [1])  # PreEndOfGame → EndOfGame no repite la descarga

    def corre(self, codigos):
        cmds = []
        companion.time.sleep = lambda _: None
        companion.subprocess.run = lambda cmd: (cmds.append(pathlib.Path(cmd[1]).name), type("R", (), {"returncode": codigos.pop(0)}))[1]
        companion.post_partida()
        return cmds

    def test_key_caducada_no_revisa(self):
        self.assertEqual(self.corre([2]), ["descargar.py"])

    def test_descarga_bien_revisa(self):
        self.assertEqual(self.corre([0, 0]), ["descargar.py", "revision.py"])


if __name__ == "__main__": unittest.main()
