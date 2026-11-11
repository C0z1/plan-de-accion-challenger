"""Pruebas de DeepSeek para companion.aviso_nivel (turno 4). Sin red ni cliente."""
import json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import companion

FIX = pathlib.Path(__file__).parent / "fixtures" / "vivo" / "allgamedata.json"


def foto():
    return json.loads(FIX.read_text(encoding="utf-8"))


class AvisoNivelBordes(unittest.TestCase):
    def test_limites_300_y_420_si_avisan(self):
        for t in (300.0, 420.0):
            d = foto(); d["gameData"]["gameTime"] = t
            self.assertIn("no tradear hasta igualar", companion.aviso_nivel(d))

    def test_dos_rivales_misma_position_toma_el_primero(self):
        d = foto()
        dup = dict(d["allPlayers"][2]); dup["championName"] = "Katarina"; dup["level"] = 9
        d["allPlayers"].append(dup)  # segundo MIDDLE en CHAOS: no debe pisar a Zed (nivel 6)
        self.assertIn("1 nivel abajo de Zed (5 contra 6)", companion.aviso_nivel(d))

    def test_level_ausente_no_truena_y_pone_interrogacion(self):
        d = foto(); del d["allPlayers"][0]["level"]
        self.assertIn("6 niveles abajo de Zed (? contra 6)", companion.aviso_nivel(d))

    def test_level_null_no_truena(self):
        # JSON a medias: la API puede mandar un campo null (no solo ausente).
        d = foto(); d["allPlayers"][0]["level"] = None
        self.assertIn("abajo de Zed", companion.aviso_nivel(d))

    def test_gametime_null_no_truena(self):
        d = foto(); d["gameData"]["gameTime"] = None
        self.assertIsNone(companion.aviso_nivel(d))


if __name__ == "__main__":
    unittest.main()
