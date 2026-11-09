"""Pruebas de DeepSeek para companion.muertes_en()/cotejo (turno 6, iteración 8). Sin red ni key.

Cubre las tareas que dejó Opus: (a) homónimo cuando tu game name es el summonerName de otro,
(b) muerte por torre/minion, (c) scores.deaths 0 con eventos tuyos → cotejo None, (d) un solo
jugador en allPlayers. Nombres y datos inventados."""
import pathlib, sys, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import companion


def me(**kw):
    p = {"riotId": "a#1", "summonerName": "a", "riotIdGameName": "Foo",
         "position": "MIDDLE", "team": "ORDER", "championName": "Sylas", "level": 6,
         "scores": {"kills": 1, "deaths": 2, "assists": 3}}
    p.update(kw)
    return p


def foto(eventos, todos=None, gameTime=950):
    return {"activePlayer": {"riotId": "a#1", "summonerName": "a"},
            "allPlayers": todos if todos is not None else [me()],
            "events": {"Events": eventos},
            "gameData": {"gameTime": gameTime}}


class Cotejo(unittest.TestCase):
    def test_homonimo_por_summoner_name_del_otro_equipo_no_cuenta(self):
        # (a) tu riotIdGameName "Foo" == summonerName del otro: el nombre corto es ambiguo y no cuenta;
        # el riotId completo siempre vale. Comportamiento conservador: mejor un «no cuadran» falso que
        # contar muertes ajenas como tuyas.
        mi = me()
        otro = me(riotId="b#2", summonerName="Foo", riotIdGameName="b", team="CHAOS", championName="Zed")
        d = foto([{"EventName": "ChampionKill", "VictimName": "Foo", "EventTime": 900}], todos=[mi, otro])
        self.assertEqual(companion.muertes_en(d, mi, 840, 1500), 0)
        d2 = foto([{"EventName": "ChampionKill", "VictimName": "a#1", "EventTime": 900}], todos=[mi, otro])
        self.assertEqual(companion.muertes_en(d2, mi, 840, 1500), 1)

    def test_muerte_por_torre_sigue_siendo_championkill(self):
        # (b) muertes_en mira VictimName, no KillerName: si la API emite ChampionKill por una ejecución,
        # cuenta como tuya (es una muerte tuya). Si la API no emite ese evento para torre/minion, el
        # conteo se queda corto; no se puede cotejar sin una partida real en datos/vivo.
        mi = me()
        d = foto([{"EventName": "ChampionKill", "VictimName": "a#1", "KillerName": "Turret", "EventTime": 900}], todos=[mi])
        self.assertEqual(companion.muertes_en(d, mi, 840, 1500), 1)

    def test_cotejo_none_cuando_deaths_0(self):
        # (c) scores.deaths 0 (falsy) → cotejo None aunque haya eventos con tu nombre.
        mi = me(scores={"kills": 0, "deaths": 0, "assists": 0})
        d = foto([{"EventName": "ChampionKill", "VictimName": "a#1", "EventTime": 900}], todos=[mi])
        self.assertIsNone(companion.resumen_fin(d)["cotejo"])

    def test_solo_tu_jugador_el_corto_cuenta(self):
        # (d) allPlayers con un solo jugador (tú): el nombre corto vale (no hay con quién confundirse).
        mi = me()
        d = foto([{"EventName": "ChampionKill", "VictimName": "a", "EventTime": 900}], todos=[mi])
        self.assertEqual(companion.muertes_en(d, mi, 840, 1500), 1)

    def test_cotejo_true_y_false(self):
        mi = me()  # deaths 2
        ok = foto([{"EventName": "ChampionKill", "VictimName": "a#1", "EventTime": 900}], todos=[mi])
        self.assertIs(companion.resumen_fin(ok)["cotejo"], True)
        mal = foto([{"EventName": "ChampionKill", "VictimName": "b#2", "EventTime": 900}], todos=[mi])
        self.assertIs(companion.resumen_fin(mal)["cotejo"], False)
        self.assertIn("no cuadran tus muertes con los eventos", companion.linea_fin(companion.resumen_fin(mal)))


if __name__ == "__main__":
    unittest.main()
