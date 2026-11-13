"""Tablero de Draft: bans y picks como en el cliente, sin identidad de nadie ni hovers del rival (política de Riot)."""
import json, unittest

import companion

M = {64: "LeeSin", 245: "Ekko", 222: "Jinx", 412: "Thresh", 104: "Graves", 112: "Viktor", 1: "Annie", 2: "Olaf", 3: "Galio"}


def sesion():
    return {"localPlayerCellId": 2, "timer": {"phase": "BAN_PICK"},
            "myTeam": [{"cellId": 0, "championId": 64, "assignedPosition": "jungle", "summonerId": 111, "puuid": "x", "gameName": "Aliado"},
                       {"cellId": 2, "championId": 0, "championPickIntent": 245, "assignedPosition": "middle", "summonerId": 222}],
            "theirTeam": [{"cellId": 5, "championId": 104, "summonerId": 333, "puuid": "y", "gameName": "Rival"},
                          {"cellId": 6, "championId": 112}],  # 6: hover del rival, todavía sin fijar
            "bans": {"myTeamBans": [1], "theirTeamBans": []},
            "actions": [[{"actorCellId": 0, "type": "ban", "championId": 1, "completed": True, "isAllyAction": True},
                         {"actorCellId": 5, "type": "ban", "championId": 2, "completed": True, "isAllyAction": False}],
                        [{"actorCellId": 0, "type": "pick", "championId": 64, "completed": True, "isAllyAction": True},
                         {"actorCellId": 5, "type": "pick", "championId": 104, "completed": True, "isAllyAction": False},
                         {"actorCellId": 6, "type": "pick", "championId": 112, "completed": False, "isInProgress": True, "isAllyAction": False}]]}


class TestTablero(unittest.TestCase):
    def test_tablero(self):
        t = companion.tablero(sesion(), M)
        self.assertEqual(t["bans"], {"mios": ["Annie"], "suyos": ["Olaf"]})  # suyos vacío en bans: salen de las acciones
        yo = next(p for p in t["mio"] if p["yo"])
        self.assertEqual((yo["campeon"], yo["fijo"], yo["pos"]), ("Ekko", False, "MIDDLE"))  # mi hover
        self.assertEqual([(p["campeon"], p["eligiendo"]) for p in t["suyo"]], [("Graves", False), (None, True)])  # sin el hover rival
        self.assertEqual(t["turno"], {"tipo": "pick", "mio": False, "aliado": False})

    def test_sin_identidad(self):
        txt = json.dumps(companion.tablero(sesion(), M))
        for x in ("summonerId", "puuid", "gameName", "Aliado", "Rival", "111", "333"): self.assertNotIn(x, txt)

    def test_claves_null(self):
        self.assertIsNone(companion.tablero(None, M))
        t = companion.tablero({"myTeam": None, "theirTeam": None, "actions": None, "bans": None}, M)
        self.assertEqual(t, {"turno": None, "bans": {"mios": [], "suyos": []}, "mio": [], "suyo": [], "draft": False})

    def test_fixture_sin_acciones(self):  # sesión vieja sin actions: lo fijado por championId, como antes
        s = json.loads((companion.DIR / "fixtures" / "champselect" / "session.json").read_text(encoding="utf-8"))
        t = companion.tablero(s, M)
        self.assertEqual([p["campeon"] for p in t["suyo"]], ["Graves", "Viktor", None, None, None])

    def test_sesion_real_flex(self):  # grabada en la PC del usuario (2026-11-12, sin identidad): bans vacíos, salen de las acciones
        s = json.loads((companion.DIR / "fixtures" / "champselect" / "session-real-flex.json").read_text(encoding="utf-8"))
        t = companion.tablero(s, {**M, 1: "Annie"} | {a["championId"]: f"c{a['championId']}" for g in s["actions"] for a in g if a.get("championId")})
        self.assertEqual((len(t["bans"]["mios"]), len(t["bans"]["suyos"])), (5, 5))
        self.assertTrue(next(p for p in t["mio"] if p["yo"])["fijo"])
        self.assertTrue(all(p["campeon"] is None for p in t["suyo"]))  # el rival todavía no muestra nada
        self.assertEqual(t["turno"], {"tipo": "pick", "mio": False, "aliado": False})


if __name__ == "__main__":
    unittest.main()
