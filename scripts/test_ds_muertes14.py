"""Pruebas de DeepSeek para companion.muertes14()/aviso_muertes() (turno 6, iteración 2). Sin red ni key.

Cubre los bordes que pidió Opus: eventos sin EventTime o VictimName, un jugador con el mismo
nombre de juego en el otro equipo (desde 0e8f464 ya no cuenta como tuya) y el borde 24:59/25:00."""
import pathlib, sys, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import companion


def foto(gameTime, eventos):
    return {
        "activePlayer": {"riotId": "cozi#1134", "summonerName": "cozi"},
        "allPlayers": [
            {"riotId": "cozi#1134", "summonerName": "cozi", "riotIdGameName": "cozi",
             "position": "MIDDLE", "team": "ORDER", "championName": "Sylas", "level": 6},
        ],
        "events": {"Events": eventos},
        "gameData": {"gameTime": gameTime},
    }


class Muertes14(unittest.TestCase):
    def test_eventos_sin_time_o_victim_no_truenan_ni_cuentan(self):
        d = foto(900, [
            {"EventName": "ChampionKill", "VictimName": "cozi#1134", "EventTime": 850},
            {"EventName": "ChampionKill", "VictimName": None, "EventTime": 860},
            {"EventName": "ChampionKill", "VictimName": "cozi#1134", "EventTime": None},
        ])
        self.assertEqual(companion.muertes14(d), 1)

    def test_homonimo_del_otro_equipo_ya_no_cuenta(self):
        # 0e8f464: el nombre sin #tag solo vale si nadie más lo comparte. El otro «cozi» muere y
        # la API da VictimName sin #tag: ya no cuenta como tuya (antes sí).
        d = {
            "activePlayer": {"riotId": "cozi#1134", "summonerName": "cozi"},
            "allPlayers": [
                {"riotId": "cozi#1134", "summonerName": "cozi", "riotIdGameName": "cozi",
                 "position": "MIDDLE", "team": "ORDER", "championName": "Sylas", "level": 6},
                {"riotId": "cozi#7777", "summonerName": "cozi", "riotIdGameName": "cozi",
                 "position": "MIDDLE", "team": "CHAOS", "championName": "Zed", "level": 6},
            ],
            "events": {"Events": [{"EventName": "ChampionKill", "VictimName": "cozi", "EventTime": 900}]},
            "gameData": {"gameTime": 950},
        }
        self.assertEqual(companion.muertes14(d), 0)

    def test_aviso_2449_si_y_2500_no(self):
        muertes = [{"EventName": "ChampionKill", "VictimName": "cozi#1134", "EventTime": 900 + i} for i in range(2)]
        self.assertIsNotNone(companion.aviso_muertes(foto(1499, muertes)))  # 24:59 avisa
        self.assertIsNone(companion.aviso_muertes(foto(1500, muertes)))     # 25:00 ya no


if __name__ == "__main__":
    unittest.main()
