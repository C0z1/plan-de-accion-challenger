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
        self.assertIn("40 s después", r[1]["texto"])
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


class SinObjetivo(unittest.TestCase):
    def test_libre_vs_con_objetivo(self):
        ev = [muere(5 * MIN), muere(10 * MIN), dragon_rival(10 * MIN + 59_000), muere(20 * MIN), dragon_rival(20 * MIN + 61_000)]
        r = P.muertes_sin_objetivo(match(), tl(ev), "yo")
        self.assertEqual((r["n"], r["total"], r["ratio"]), (2, 3, 0.67))
        self.assertEqual([x["t"] for x in r["lista"]], [300, 1200])

    def test_objetivo_propio_no_cuenta(self):
        propio = dict(type="ELITE_MONSTER_KILL", timestamp=5 * MIN + 10_000, monsterType="DRAGON", killerTeamId=100)
        self.assertEqual(P.muertes_sin_objetivo(match(), tl([muere(5 * MIN), propio]), "yo")["n"], 1)

    def test_torre_rival_cuenta(self):
        torre = dict(type="BUILDING_KILL", timestamp=5 * MIN + 10_000, buildingType="TOWER_BUILDING", teamId=100)  # cae una torre tuya
        self.assertEqual(P.muertes_sin_objetivo(match(), tl([muere(5 * MIN), torre]), "yo")["n"], 0)

    def test_sin_timeline(self):
        self.assertEqual(P.muertes_sin_objetivo(match(), None, "yo"), dict(n=0, total=0, ratio=None, lista=[]))

if __name__ == "__main__":
    unittest.main()
