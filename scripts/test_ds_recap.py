"""Recap 0.19 «tu partida en una estela» (postpartida.estela / estela_vivo), con partidas sintéticas."""
import unittest

import postpartida as P
from test_postpartida import MIN, dragon_rival, match, muere, tl


def partida(dur=1800, win=True, modo="CLASSIC"):
    m = match(); m["info"].update(gameDuration=dur, gameMode=modo); m["info"]["participants"][0]["win"] = win
    return m


class Estela(unittest.TestCase):
    def test_forma(self):
        e = P.estela(partida(), tl([muere(10 * MIN), dragon_rival(10 * MIN + 40_000)], [(0, 500, 500), (1, 900, 600), (2, 1200, 1500)]), "yo")
        self.assertEqual((e["dur"], e["win"], e["oro"]), (1800, True, [0, 300, -300]))
        self.assertEqual([(m["t"], m["tipo"]) for m in e["momentos"]], [(120, "oro"), (600, "muerte")])  # +300 a -300: vuelco de 600
        self.assertTrue(all(0 <= m["t"] <= e["dur"] and set(m) == {"t", "tipo", "texto", "tuyo"} for m in e["momentos"]))

    def test_sin_datos_o_aram(self):
        self.assertIsNone(P.estela(partida(), None, "yo"))
        self.assertIsNone(P.estela(partida(), tl([]), "otro"))
        self.assertIsNone(P.estela(partida(modo="ARAM"), tl([]), "yo"))

    def test_sin_rival_estela_plana(self):
        m = partida(); m["info"]["participants"][1]["teamPosition"] = "TOP"
        self.assertEqual(P.estela(m, tl([]), "yo")["oro"], [])

    def test_vivo_sin_oro(self):
        self.assertIsNone(P.estela_vivo(None))
        self.assertIsNone(P.estela_vivo({"gameData": {"gameMode": "ARAM"}}))

    def test_textos_sin_ordenes(self):  # Riot: dato, no órdenes
        e = P.estela(partida(), tl([muere(5 * MIN), muere(10 * MIN), dragon_rival(10 * MIN + 30_000)], [(0, 500, 500), (1, 500, 1200)]), "yo")
        for m in e["momentos"]: self.assertNotRegex(m["texto"], r"(?i)\b(debes|deberías|juega|no pelees|ve a)\b")


if __name__ == "__main__":
    unittest.main()
