"""Matchups de muchas partidas (PLAN-MATCHUPS.md): filas, agregado, frases y lectura. Partidas sintéticas, sin red."""
import json, pathlib, re, tempfile, unittest

import matchups as M

MIN = 60000


def partida(pos_a="MIDDLE", win=True, dur=1800, modo="CLASSIC", pos_b=None, runa=8112):
    ps = [{"puuid": "yo", "participantId": 1, "teamId": 100, "teamPosition": pos_a, "championName": "Zeri", "win": win,
           "perks": {"styles": [{"style": 8100, "selections": [{"perk": runa}, {"perk": 8139}, {"perk": 8138}, {"perk": 8135}]},
                                {"style": 8000, "selections": [{"perk": 9111}, {"perk": 8017}]}],
                     "statPerks": {"offense": 5005, "flex": 5008, "defense": 5001}}, "item0": 3032, "item1": 3006},
          {"puuid": "el", "participantId": 6, "teamId": 200, "teamPosition": pos_b or pos_a, "championName": "MissFortune", "win": not win},
          {"puuid": "sup", "participantId": 5, "teamId": 100, "teamPosition": "UTILITY", "championName": "Thresh"},
          {"puuid": "sup2", "participantId": 10, "teamId": 200, "teamPosition": "UTILITY", "championName": "Leona"}]
    return {"info": {"gameMode": modo, "gameDuration": dur, "gameVersion": "16.22.1.123", "participants": ps}}


def timeline(eventos, ups_a=(), ups_b=()):
    pfs = lambda oa, ob: {"1": {"totalGold": oa, "xp": oa, "minionsKilled": 10, "jungleMinionsKilled": 0},
                          "6": {"totalGold": ob, "xp": ob, "minionsKilled": 8, "jungleMinionsKilled": 0}}
    frames = [{"timestamp": m * MIN, "events": [], "participantFrames": pfs(500 + 300 * m, 500 + 250 * m)} for m in range(16)]
    frames[0]["events"] = ([{"type": "LEVEL_UP", "participantId": 1, "timestamp": t} for t in ups_a]
                           + [{"type": "LEVEL_UP", "participantId": 6, "timestamp": t} for t in ups_b] + list(eventos))
    return {"info": {"frames": frames}}


mata = lambda t, killer, victim, asist=(): {"type": "CHAMPION_KILL", "timestamp": t, "killerId": killer, "victimId": victim, "assistingParticipantIds": list(asist)}
UPS_A = [m * MIN for m in (1, 2, 3, 4, 5, 6)]  # nivel 7 al minuto 6
UPS_B = [m * MIN + 30000 for m in (1, 2, 3, 4, 5, 6)]


class Fila(unittest.TestCase):
    def test_muertes_de_linea_y_niveles(self):
        f = M.fila(partida(), timeline([mata(5 * MIN + 45000, 1, 6), mata(3 * MIN, 6, 1, [7]), mata(15 * MIN, 1, 6)], UPS_A, UPS_B), "yo")
        self.assertEqual([(m["gana"], m["na"], m["nb"], m["solo"]) for m in f["muertes"]], [("A", 6, 6, True), ("B", 4, 3, False)])  # la del 15 no cuenta; niveles desde LEVEL_UP
        self.assertEqual((f["A"], f["B"], f["pos"], f["parche"], f["gd"][14]), ("Zeri", "MissFortune", "MIDDLE", "16.22", 14 * 50))
        self.assertTrue(f["primero6"])  # A llegó a 6 antes
        self.assertEqual((f["runa"], len(f["pagina"])), (8112, 11))

    def test_bot_cuenta_al_support(self):
        f = M.fila(partida("BOTTOM"), timeline([mata(4 * MIN, 1, 10), mata(5 * MIN, 5, 6), mata(6 * MIN, 10, 5)]), "yo")
        self.assertEqual([m["gana"] for m in f["muertes"]], ["A", "A", "B"])  # víctima support rival; asesino support mío; víctima mi support

    def test_no_aplica(self):
        self.assertIsNone(M.fila(partida(dur=200), timeline([]), "yo"))  # remake
        self.assertIsNone(M.fila(partida(modo="ARAM"), timeline([]), "yo"))
        self.assertIsNone(M.fila(partida(pos_a=""), timeline([]), "yo"))  # sin posición (DeepSeek)
        self.assertIsNone(M.fila(partida(pos_b="TOP"), timeline([]), "yo"))  # sin rival de línea
        self.assertIsNone(M.fila(partida(), {}, "yo"))


def filas_sinteticas(n=200, gana_6=0.7):
    out = []
    for i in range(n):
        g6 = i < n * gana_6
        ev = [mata(6 * MIN + 10000, 1, 6) if g6 else mata(6 * MIN + 10000, 6, 1), mata(2 * MIN, 6, 1) if i % 2 else mata(2 * MIN, 1, 6)]
        out.append(M.fila(partida(win=i % 3 != 0), timeline(ev, UPS_A, UPS_B), "yo"))
    return out


class Agregar(unittest.TestCase):
    def test_ventanas_y_base(self):
        d = M.agregar(filas_sinteticas())
        m = d["Zeri|MIDDLE|MissFortune"]
        self.assertEqual((m["n"], m["ventanas"]["6-8"], m["ventanas"]["1-3"]), (200, [140, 60], [100, 100]))
        self.assertAlmostEqual(m["wr"], 133 / 200, places=3); self.assertEqual(m["wr_base_a"], m["wr"])
        self.assertEqual(d["_parches"], ["16.22"])
        self.assertNotIn("MissFortune|MIDDLE|Zeri", d)  # A vs B no es B vs A

    def test_runa_alternativa_solo_si_el_piso_supera(self):
        r = M._mas_ganadora([(1, True)] * 30 + [(1, False)] * 30 + [(2, True)] * 45 + [(2, False)] * 5)
        self.assertEqual((r["id"], r.get("alternativa")), (1, 2))  # 2: 90 % con n=50, piso de Wilson > 50 %
        self.assertNotIn("alternativa", M._mas_ganadora([(1, True)] * 40 + [(1, False)] * 30 + [(2, True)] * 18 + [(2, False)] * 12))
        self.assertIsNone(M._mas_ganadora([(1, True)] * 10))  # n < 30


class Frases(unittest.TestCase):
    NEGRA = r"(?i)\b(pelea|peleá|all-in|tradea|juega|debes|compra|vuelve)\b"

    def test_frases_con_n_y_sin_ordenes(self):
        m = M.agregar(filas_sinteticas())["Zeri|MIDDLE|MissFortune"]
        fs = M.frases(m, "Zeri", "Miss Fortune")
        self.assertEqual(fs[0], "Zeri gana el nivel 6-8 contra Miss Fortune: 70 % de las muertes de línea (n=200)")
        self.assertLessEqual(len(fs), 3)
        for f in fs: self.assertRegex(f, r"\(n=\d+\)"); self.assertNotRegex(f, self.NEGRA)
        self.assertFalse(any("1-3" in f for f in fs))  # 50/50: el intervalo cruza el 50 %

    def test_pocos_datos_sin_frase(self):
        self.assertEqual(M.frases(M.agregar(filas_sinteticas(80))["Zeri|MIDDLE|MissFortune"], "Zeri", "MF"), [])  # < 100 partidas
        self.assertEqual(M.frases(None, "a", "b"), [])

    def test_guardado(self):
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t, "m.json")
            self.assertIsNone(M.guardado("Zeri", "MIDDLE", "MissFortune", p))  # ausente
            p.write_text('{"Zeri|MIDDLE|MissFortune": {"n": 2', encoding="utf-8"); self.assertIsNone(M.guardado("Zeri", "MIDDLE", "MissFortune", p))  # cortado
            p.write_text(json.dumps({"Zeri|MIDDLE|MissFortune": {"n": 150}}), encoding="utf-8")
            self.assertEqual(M.guardado("Zeri", "MIDDLE", "MissFortune", p)["n"], 150)


if __name__ == "__main__":
    unittest.main()
