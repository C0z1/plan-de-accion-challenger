"""Pruebas de DeepSeek para score.py (turno 5). Sin red: la fórmula de z_partida/de sobre partidas sintéticas."""
import pathlib, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import score  # noqa: E402


def jug(puuid, team, pos, win, kills=0, assists=0, deaths=0, dano=0, oro=0, obj=0, vision=0, cs=0, mon=0):
    return dict(puuid=puuid, teamId=team, teamPosition=pos, win=win, kills=kills, assists=assists,
                deaths=deaths, totalDamageDealtToChampions=dano, goldEarned=oro,
                damageDealtToObjectives=obj, visionScore=vision, totalMinionsKilled=cs,
                neutralMinionsKilled=mon)


def partida(ps, dur=1800):
    return dict(mapId=11, gameDuration=dur, participants=ps)


POS = ("MIDDLE", "TOP", "JUNGLE", "BOTTOM", "UTILITY")


class Score(unittest.TestCase):
    def test_equipo_sin_kills_no_divide_entre_cero(self):
        # equipo 200 sin kills: KP crudo 0 (el `or 1` evita el ZeroDivisionError) y sus 5 z de kp quedan iguales
        ps = [jug(f"a{i}", 100, p, True, kills=k) for i, (p, k) in
              enumerate(zip(POS, (2, 1, 1, 1, 0)))]
        ps += [jug(f"b{i}", 200, p, False) for i, p in enumerate(POS)]
        zs = score.z_partida(partida(ps))
        self.assertEqual(len(zs), 10)
        kp_b = [z["kp"] for _, _, eq, _, z in zs if eq == 200]
        self.assertEqual(len(set(kp_b)), 1)      # los 5 sin kills tienen el mismo KP (0)
        self.assertLess(kp_b[0], 0)              # y es el más bajo de la partida
        kp_a0 = next(z["kp"] for puuid, _, _, _, z in zs if puuid == "a0")
        self.assertGreater(kp_a0, 0)

    def test_afk_sale_ultimo(self):
        # 9 jugadores normales + 1 AFK (todo 0, 1 muerte): debe salir 10.º de 10
        ps = [jug(f"p{i}", 100, POS[i], True, kills=3, assists=1, deaths=0,
                  dano=8000, oro=10000, obj=3000, vision=12, cs=160) for i in range(5)]
        ps += [jug("afk", 200, "MIDDLE", False, deaths=1)]
        ps += [jug(f"q{i}", 200, POS[i], False, kills=3, assists=1, deaths=0,
                   dano=8000, oro=10000, obj=3000, vision=12, cs=160) for i in range(1, 5)]
        zs = score.z_partida(partida(ps))
        self.assertEqual(len(zs), 10)
        r = score.de(zs, "afk", {})
        self.assertEqual(r["puesto"], 10)
        self.assertLess(r["score"], 40)

    def test_de_con_puuid_ajeno_es_none(self):
        ps = [jug(f"p{i}", 100 if i < 5 else 200, POS[i % 5], i < 5, kills=1, oro=5000) for i in range(10)]
        zs = score.z_partida(partida(ps))
        self.assertIsNone(score.de(zs, "no-existe", {}))


if __name__ == "__main__":
    unittest.main()
