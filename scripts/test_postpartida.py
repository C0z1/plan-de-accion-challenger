"""Pruebas de postpartida.py con partidas sintéticas (sin red ni datos reales)."""
import pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import postpartida as P  # noqa: E402

MIN = 60_000


def match():
    ps = [dict(puuid="yo", participantId=1, teamId=100, teamPosition="MIDDLE"),
          dict(puuid="rival", participantId=6, teamId=200, teamPosition="MIDDLE")]
    return dict(info=dict(participants=ps))


def tl(eventos, oro=None):
    """oro: lista de (minuto, mi_oro, oro_rival); un frame por minuto."""
    frames = [dict(timestamp=m * MIN, events=[], participantFrames={"1": dict(totalGold=a), "6": dict(totalGold=b)}) for m, a, b in (oro or [(0, 500, 500)])]
    frames[0]["events"] = eventos
    return dict(info=dict(frames=frames))


muere = lambda t: dict(type="CHAMPION_KILL", timestamp=t, victimId=1, killerId=6)
dragon_rival = lambda t: dict(type="ELITE_MONSTER_KILL", timestamp=t, monsterType="DRAGON", killerTeamId=200)


class Momentos(unittest.TestCase):
    def test_top3_por_impacto(self):
        ev = [muere(5 * MIN),  # libre: impacto 2
              muere(10 * MIN), dragon_rival(10 * MIN + 40_000),  # muerte con dragón: 6
              dict(type="ELITE_MONSTER_KILL", timestamp=20 * MIN, monsterType="BARON_NASHOR", killerTeamId=200),  # barón perdido: 7
              dict(type="ELITE_MONSTER_KILL", timestamp=25 * MIN, monsterType="HORDE", killerTeamId=100)]  # larvas propias: 2
        r = P.momentos(match(), tl(ev), "yo")
        self.assertEqual([m["t"] for m in r], [300, 600, 1200])  # la muerte libre (2) gana a las larvas (2) por ser más antigua
        self.assertEqual(r[2]["impacto"], 7)

    def test_orden_cronologico_y_sin_duplicar(self):
        ev = [muere(10 * MIN), dragon_rival(10 * MIN + 40_000), muere(30 * MIN), muere(2 * MIN)]
        r = P.momentos(match(), tl(ev), "yo")
        self.assertEqual([m["t"] for m in r], [120, 600, 1800])
        self.assertIn("Después el rival tomó el dragón", r[1]["texto"])  # con la causa probable delante
        self.assertEqual(sum(m["tipo"] == "objetivo" for m in r), 0)  # el dragón va dentro de la muerte

    def test_vuelco_de_oro(self):
        r = P.momentos(match(), tl([], [(0, 500, 500), (1, 500, 1100)]), "yo")
        self.assertEqual(r[0]["tipo"], "oro")
        self.assertIn("-600", r[0]["texto"])

    def test_sin_timeline_o_roto(self):
        self.assertEqual(P.momentos(match(), None, "yo"), [])
        self.assertEqual(P.momentos(match(), {}, "yo"), [])
        self.assertEqual(P.momentos({}, tl([]), "yo"), [])
        self.assertEqual(P.momentos(match(), tl([]), "otro"), [])


class SinObjetivo(unittest.TestCase):  # 0.28: «sin objetivo» = tu equipo no la cambió por un objetivo grande (antes: el rival no sacó nada)
    def test_sin_cambio_aunque_el_rival_tome_algo(self):
        ev = [muere(5 * MIN), muere(10 * MIN), dragon_rival(10 * MIN + 59_000), muere(20 * MIN)]
        r = P.muertes_sin_objetivo(match(), tl(ev), "yo")
        self.assertEqual((r["n"], r["total"], r["ratio"], r["por_tipo"]), (3, 3, 1.0, {"1v1": 3}))
        self.assertEqual([x["t"] for x in r["lista"]], [300, 600, 1200])

    def test_objetivo_propio_es_un_buen_cambio(self):
        propio = dict(type="ELITE_MONSTER_KILL", timestamp=5 * MIN + 10_000, monsterType="DRAGON", killerTeamId=100)
        r = P.muertes_sin_objetivo(match(), tl([muere(5 * MIN), propio]), "yo")
        self.assertEqual((r["n"], r["por_tipo"]), (0, {"trade": 1}))

    def test_torre_no_es_cambio(self):  # las torres caen solas: no cuentan como trade
        torre = dict(type="BUILDING_KILL", timestamp=5 * MIN + 10_000, buildingType="TOWER_BUILDING", teamId=200)
        self.assertEqual(P.muertes_sin_objetivo(match(), tl([muere(5 * MIN), torre]), "yo")["n"], 1)

    def test_sin_timeline(self):
        self.assertEqual(P.muertes_sin_objetivo(match(), None, "yo"), dict(n=0, total=0, ratio=None, por_tipo={}, lista=[]))


class Clasificar(unittest.TestCase):
    """La causa probable de cada muerte, para enseñar sin culpar (pedido del usuario)."""
    def m(self):
        ps = [dict(puuid="yo", participantId=1, teamId=100, teamPosition="MIDDLE", championName="Ahri"),
              dict(puuid="j", participantId=2, teamId=100, teamPosition="JUNGLE", championName="Vi"),
              dict(puuid="rival", participantId=6, teamId=200, teamPosition="MIDDLE", championName="Zed"),
              dict(puuid="jg", participantId=7, teamId=200, teamPosition="JUNGLE", championName="Lee")]
        return dict(info=dict(participants=ps))

    def t(self, ev, nivel=(5, 6)):
        fr = [dict(timestamp=m * MIN, events=[], participantFrames={str(i): dict(totalGold=500, level=nivel[0] if i < 6 else nivel[1]) for i in (1, 2, 6, 7)}) for m in range(8)]
        fr[0]["events"] = ev
        return dict(info=dict(frames=fr))

    def uno(self, ev, **kw): return P.muertes(self.m(), self.t(ev, **kw), "yo")[0]

    def test_gank_sin_ward(self):
        e = dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=7, assistingParticipantIds=[6], position=dict(x=7400, y=7400))
        r = self.uno([e])
        self.assertEqual((r["tipo"], r["n"], r["jungla"], r["ward"]), ("gank", 2, True, False))
        self.assertIn("entre 2 con su jungla en", r["texto"]); self.assertIn("No vimos un ward tuyo", r["texto"])

    def test_gank_con_ward_reciente(self):
        w = dict(type="WARD_PLACED", timestamp=5 * MIN, creatorId=1, wardType="YELLOW_TRINKET")
        e = dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=7, assistingParticipantIds=[6])
        self.assertIn("otro camino", self.uno([w, e])["texto"])

    def test_1v1_con_nivel_abajo(self):
        r = self.uno([dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=6)])
        self.assertEqual((r["tipo"], r["dnivel"]), ("1v1", -1)); self.assertIn("con 1 nivel abajo", r["texto"]); self.assertIn("Zed", r["texto"])

    def test_pelea_y_torre_y_trade(self):
        ali = dict(type="CHAMPION_KILL", timestamp=6 * MIN + 5000, victimId=7, killerId=2)  # tu jungla metido: pelea
        e = dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=6, assistingParticipantIds=[7])
        self.assertEqual(self.uno([e, ali])["tipo"], "pelea")
        self.assertEqual(self.uno([dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=0)])["tipo"], "torre")
        d = dict(type="ELITE_MONSTER_KILL", timestamp=6 * MIN + 20_000, monsterType="DRAGON", killerTeamId=100)
        r = self.uno([e, d]); self.assertEqual(r["tipo"], "trade"); self.assertIn("Buen cambio", r["texto"])

    def test_sin_culpa(self):  # ninguna frase juzga
        for ev in ([dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=6)],
                   [dict(type="CHAMPION_KILL", timestamp=6 * MIN, victimId=1, killerId=7, assistingParticipantIds=[6])]):
            tx = self.uno(ev)["texto"].lower()
            self.assertFalse(any(p in tx for p in ("culpa", "mal", "error", "fallaste", "moriste")), tx)


class Vivo(unittest.TestCase):  # F11: los 3 momentos al instante desde la última foto en vivo (sin key)
    def foto(self, eventos):
        return {"activePlayer": {"riotId": "yo#1"}, "gameData": {"gameTime": 2000, "gameMode": "CLASSIC"},
                "allPlayers": [{"riotId": "yo#1", "riotIdGameName": "yo", "position": "MIDDLE", "team": "ORDER"},
                               {"riotId": "el#2", "riotIdGameName": "el", "position": "MIDDLE", "team": "CHAOS"}],
                "events": {"Events": eventos}}

    def test_muerte_con_objetivo_y_edificios(self):
        ev = [{"EventName": "ChampionKill", "EventTime": 900.0, "KillerName": "el", "VictimName": "yo"},
              {"EventName": "DragonKill", "EventTime": 920.0, "KillerName": "el", "DragonType": "Fire"},
              {"EventName": "TurretKilled", "EventTime": 1000.0, "KillerName": "yo", "TurretKilled": "Turret_TChaos_L1_P3_1_0"},
              {"EventName": "DragonKill", "EventTime": 1900.0, "KillerName": "el", "DragonType": "Elder"},
              {"EventName": "ChampionKill", "EventTime": 300.0, "KillerName": "yo", "VictimName": "el"}]
        ms = P.momentos_vivo(self.foto(ev))
        self.assertEqual([m["t"] for m in ms], [900, 1000, 1900])
        self.assertIn("caíste y 20 s después el rival tomó el dragón", ms[0]["texto"])
        self.assertIn("tu equipo tomó una torre", ms[1]["texto"])
        self.assertIn("el dragón anciano", ms[2]["texto"])

    def test_sin_datos(self):
        self.assertEqual(P.momentos_vivo(None), [])
        self.assertEqual(P.momentos_vivo({"allPlayers": []}), [])
        self.assertEqual(P.momentos_vivo(self.foto([])), [])

if __name__ == "__main__":
    unittest.main()
