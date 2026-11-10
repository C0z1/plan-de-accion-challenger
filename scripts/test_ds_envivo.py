"""Pruebas de DeepSeek de En vivo (turno 9 iter 10): tarea de Opus — rival_items sin displayName, borde del timer y
que rival_items solo se lea como pares [id, nombre]. Sin red ni ventanas."""
import json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import companion

FIX = pathlib.Path(__file__).parent / "fixtures"
HTML = (pathlib.Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")


def foto(): return json.loads((FIX / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))


class RivalItems(unittest.TestCase):
    def test_item_sin_displayname_da_id_y_vacio(self):
        d = foto(); d["allPlayers"][2]["items"] = [{"itemID": 3142, "slot": 0}]  # sin displayName
        self.assertEqual(companion.meta_fase(d, {})["rival_items"], [[3142, ""]])

    def test_rival_items_se_lee_como_pares_no_enteros(self):
        # único consumidor en la página: desestructura [id, nombre]; nadie lo lee como lista de enteros
        self.assertIn('rival_items.map(([id, n]) => img("item", id, "item", n))', HTML)


class Timer(unittest.TestCase):
    def test_borde_60_segundos(self):
        # cuenta(t) tiñe de ámbar con t < 60; 59 tiñe y 60 ya no (el borde es estricto)
        self.assertIn("const cuenta = t => t < 60 ?", HTML)
