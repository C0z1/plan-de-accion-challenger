"""Pruebas de DeepSeek para companion.meta_fase y companion_gui.texto_meta (turno 5, iteración 8). Sin red ni ventana.

Cubre los bordes que pidió Opus: activePlayer que no está en allPlayers (→ None), nivel y CS null (→ «?» sin tronar)
y la meta al 10 que desaparece del texto desde el minuto 11."""
import pathlib, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import companion      # noqa: E402
import companion_gui  # noqa: E402


def foto(t=300, nivel=None, scores=None, campeon="Ekko", pos="MIDDLE", team="ORDER"):
    yo = {"riotId": "Yo#NA1", "summonerName": "Yo#NA1"}
    ps = [{"championName": campeon, "level": nivel, "position": pos, "team": team,
           "riotId": "Yo#NA1", "summonerName": "Yo#NA1", "scores": scores}]
    return {"activePlayer": yo, "allPlayers": ps, "gameData": {"gameTime": t}}


class Meta(unittest.TestCase):
    def test_meta_fase_sin_tu_jugador(self):
        d = {"activePlayer": {"riotId": "Nadie#NA1"}, "allPlayers": [{"riotId": "Otro#NA1", "position": "MIDDLE"}],
             "gameData": {"gameTime": 300}}
        self.assertIsNone(companion.meta_fase(d, m10={}))

    def test_texto_meta_con_nivel_y_cs_null(self):
        mf = companion.meta_fase(foto(nivel=None, scores=None), m10={})
        self.assertIsNone(mf["nivel"]); self.assertIsNone(mf["cs"])
        self.assertIn("?", companion_gui.texto_meta(mf))  # no truena y usa «?»

    def test_meta_al_10_desaparece_desde_el_minuto_11(self):
        d = foto(t=660, nivel=9, scores={"creepScore": 70})
        d["allPlayers"].append({"championName": "Zed", "level": 9, "position": "MIDDLE", "team": "CHAOS",
                                "riotId": "R#NA1", "summonerName": "R#NA1", "scores": {"creepScore": 70}})
        mf = companion.meta_fase(d, m10={"campeon": "Ekko", "minimo": 69})
        self.assertEqual((mf["minuto"], mf["cs_meta"]), (11, 69))
        self.assertNotIn("meta 69", companion_gui.texto_meta(mf))


if __name__ == "__main__":
    unittest.main()
