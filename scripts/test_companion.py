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


if __name__ == "__main__": unittest.main()
