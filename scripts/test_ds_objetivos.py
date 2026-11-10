"""Pruebas de companion.objetivos (turno 9 iter 5): eventos rotos y homónimos, sin red ni cliente."""
import pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import companion


def d(events=None, t=1000, players=None):
    ps = players if players is not None else [
        {"riotIdGameName": "A1", "summonerName": "A1", "team": "ORDER", "scores": {"kills": 2, "deaths": 0, "assists": 1}},
        {"riotIdGameName": "A2", "summonerName": "A2", "team": "ORDER", "scores": {"kills": 1}},
        {"riotIdGameName": "R1", "summonerName": "R1", "team": "CHAOS", "scores": {"kills": 3}},
    ]
    return {"allPlayers": ps, "events": events if events is not None else {"Events": []}, "gameData": {"gameTime": t}}


class Objetivos(unittest.TestCase):
    def test_kills_cuadran_con_scores(self):  # tarea (c): kills del equipo = suma de scores.kills
        me = {"team": "ORDER"}
        o = companion.objetivos(d(), me)
        self.assertEqual(o["tuyos"]["kills"], 3)   # 2 + 1
        self.assertEqual(o["rival"]["kills"], 3)

    def test_events_null_killername_null_y_turret_sin_nombre(self):  # tarea (a): no tronar ni contar
        me = {"team": "ORDER"}
        for ev in (None, {"Events": None}, {"Events": [
            {"EventName": "DragonKill", "EventTime": 500, "KillerName": None},
            {"EventName": "TurretKilled", "EventTime": 500, "KillerName": None},  # sin campo TurretKilled
            {"EventName": "HeraldKill", "EventTime": 500, "KillerName": "Desconocido"},
        ]}):
            o = companion.objetivos(d(events=ev), me)
            for k in ("torres", "dragones", "larvas", "heraldo", "baron"):
                self.assertEqual(o["tuyos"][k], 0, (ev, k))
                self.assertEqual(o["rival"][k], 0, (ev, k))

    def test_turret_por_dueno_no_por_killer(self):  # torre TOrder caída = la tomó el rival (CHAOS)
        ev = {"Events": [
            {"EventName": "TurretKilled", "EventTime": 900, "KillerName": "R1", "TurretKilled": "Turret_TOrder_L1_0_0_0"},
            {"EventName": "TurretKilled", "EventTime": 910, "KillerName": "A1", "TurretKilled": "Turret_TChaos_L1_0_0_0"},
        ]}
        o = companion.objetivos(d(events=ev), {"team": "ORDER"})
        self.assertEqual(o["tuyos"]["torres"], 1)   # cayó la torre rival (TChaos)
        self.assertEqual(o["rival"]["torres"], 1)   # cayó la tuya (TOrder)

    def test_homonimo_ultimo_gana(self):  # tarea (b): eq asigna el nombre al último de allPlayers (solo eventos)
        ps = [
            {"riotIdGameName": "Dup", "summonerName": "Dup", "team": "ORDER", "scores": {"kills": 0}},
            {"riotIdGameName": "Dup", "summonerName": "Dup", "team": "CHAOS", "scores": {"kills": 0}},
        ]
        ev = {"Events": [{"EventName": "DragonKill", "EventTime": 500, "KillerName": "Dup"}]}
        o = companion.objetivos(d(events=ev, players=ps), {"team": "ORDER"})
        self.assertEqual(o["tuyos"]["dragones"], 0)   # hoy cae en el rival (el último «Dup» es CHAOS)
        self.assertEqual(o["rival"]["dragones"], 1)


if __name__ == "__main__":
    unittest.main()
