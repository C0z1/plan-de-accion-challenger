"""ARAM y modos sin líneas (v0.5): sin rival de línea, sin dragón/barón ni avisos de la Grieta; marcador y amenazas."""
import unittest

import companion
import companion_gui as g
import overlay


def jugador(nombre, campeon, equipo, k, d, a, nivel=18):
    return {"riotId": f"{nombre}#X", "riotIdGameName": nombre, "summonerName": nombre, "championName": campeon, "team": equipo,
            "position": "NONE", "level": nivel, "scores": {"kills": k, "deaths": d, "assists": a, "creepScore": 50}, "items": []}


FOTO = {"activePlayer": {"riotId": "yo#X", "summonerName": "yo"},
        "gameData": {"gameMode": "ARAM", "mapNumber": 12, "gameTime": 1000},
        "allPlayers": [jugador("yo", "Zeri", "ORDER", 6, 8, 10), jugador("a", "Lux", "ORDER", 3, 2, 9),
                       jugador("b", "Lillia", "CHAOS", 14, 3, 9), jugador("c", "Shen", "CHAOS", 4, 6, 20), jugador("e", "Caitlyn", "CHAOS", 14, 5, 2)],
        "events": {"Events": [{"EventName": "ChampionKill", "KillerName": "yo", "VictimName": "b", "EventTime": 100},
                              {"EventName": "ChampionKill", "KillerName": "b", "VictimName": "yo", "EventTime": 200},
                              {"EventName": "ChampionKill", "KillerName": "e", "VictimName": "a", "EventTime": 300}]}}


class TestAram(unittest.TestCase):
    def test_none_no_es_una_linea(self):
        me, rival = companion.yo_rival(FOTO)
        self.assertEqual((me["championName"], rival), ("Zeri", None))

    def test_meta_marcador_y_amenazas(self):
        m = companion.meta_fase(FOTO, m10={})
        self.assertEqual((m["modo"], m["kda"], m["kills"]), ("ARAM", "6/8/10", [9, 32]))
        self.assertEqual([a["campeon"] for a in m["amenazas"]], ["Lillia", "Caitlyn", "Shen"])  # 14/3 antes que 14/5 (asistencias)
        self.assertNotIn("objetivos", m)

    def test_sin_avisos_de_la_grieta(self):
        self.assertFalse(companion.grieta(FOTO)); self.assertTrue(companion.grieta({"gameData": {"gameMode": "CLASSIC"}}))
        f = {**FOTO, "gameData": {**FOTO["gameData"], "gameTime": 1000}}
        self.assertIsNone(companion.aviso_muertes(f)); self.assertIsNone(companion.aviso_nivel(f))
        self.assertIsNone(companion.aviso_minions({**f, "gameData": {**f["gameData"], "gameTime": 630}}, {"campeon": "Zeri", "minimo": 69}))

    def test_overlay_y_texto(self):
        m = companion.meta_fase(FOTO, m10={})
        self.assertEqual([t for t, _ in overlay.partes(m, 0)], ["▼ Kills 9 vs 32", "Cuidado Lillia 14/3/9", "Tu KDA 6/8/10"])
        self.assertEqual(g.texto_meta(m), "Min 16 · Kills 9–32 · Tu KDA 6/8/10 · Cuidado con Lillia 14/3/9")


if __name__ == "__main__":
    unittest.main()
