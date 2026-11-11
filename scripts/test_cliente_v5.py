"""Partidas desde tu cliente de LoL (sin key ni invitación): traducción al formato de Racha y descarga."""
import json, pathlib, tempfile, unittest

import cliente_v5

FX = pathlib.Path(__file__).parent / "fixtures" / "lcu" / "partida_cliente.json"
CAMPEONES = {67: "Vayne", 104: "Graves", 799: "Ambessa", 145: "Kaisa", 412: "Thresh", 777: "Yone", 121: "Khazix", 887: "Gwen", 134: "Syndra", 89: "Leona"}


class Adaptador(unittest.TestCase):
    def setUp(self): self.d = json.loads(FX.read_text(encoding="utf-8"))

    def test_posiciones_deducidas(self):  # el lane/role del cliente no sirve (2 junglas, 2 tops): se deducen
        pos = cliente_v5.posiciones(self.d["game"], self.d["timeline"])
        porequipo = {t: sorted(pos[p["participantId"]] for p in self.d["game"]["participants"] if p["teamId"] == t) for t in (100, 200)}
        for t in (100, 200): self.assertEqual(porequipo[t], ["BOTTOM", "JUNGLE", "MIDDLE", "TOP", "UTILITY"])

    def test_formato_v5_sirve_al_analisis(self):
        import score, postpartida
        m, t = cliente_v5.a_v5(self.d["game"], self.d["timeline"], "la1", CAMPEONES)
        self.assertEqual(m["metadata"]["matchId"], "LA1_1761893743")
        self.assertEqual(len(score.z_partida(m["info"])), 10)
        yone = next(p for p in m["info"]["participants"] if p["championName"] == "Yone")
        self.assertEqual((yone["teamPosition"], yone["kills"], yone["deaths"]), ("TOP", 3, 5))
        self.assertEqual([x["t"] for x in postpartida.momentos(m, t, yone["puuid"])], [526, 866, 1286])

    def test_descargar(self):
        g, tl = self.d["game"], self.d["timeline"]
        api = {"/lol-summoner/v1/current-summoner": {"puuid": "puuid-6", "gameName": "J6", "tagLine": "TEST"},
               "/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=20": {"platformId": "LA1", "games": {"games": [{"gameId": g["gameId"]}]}},
               f"/lol-match-history/v1/games/{g['gameId']}": g, f"/lol-match-history/v1/game-timelines/{g['gameId']}": tl}
        with tempfile.TemporaryDirectory() as d:
            n, msg = cliente_v5.descargar(d, api.get)
            self.assertEqual(n, 1); self.assertTrue((pathlib.Path(d) / "LA1_1761893743.json").exists())
            self.assertTrue((pathlib.Path(d) / "timeline" / "LA1_1761893743.json").exists())
            self.assertEqual(cliente_v5.descargar(d, api.get)[0], 0)  # ya estaba
            otro = {**api, "/lol-summoner/v1/current-summoner": {"puuid": "otra-cuenta", "gameName": "Otro", "tagLine": "X"}}
            self.assertIn("otra cuenta", cliente_v5.descargar(d, otro.get)[1])  # no mezcla historiales
        self.assertEqual(cliente_v5.descargar(tempfile.gettempdir(), {}.get)[0], 0)  # sin cliente

    def test_misma_cuenta_con_otro_puuid(self):  # Riot cifra el puuid por key: la API y el cliente dan distinto para ti
        g, tl = self.d["game"], self.d["timeline"]
        api = {"/lol-summoner/v1/current-summoner": {"puuid": "puuid-6", "gameName": "J6", "tagLine": "TEST"},
               "/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=20": {"platformId": "LA1", "games": {"games": [{"gameId": g["gameId"]}]}},
               f"/lol-match-history/v1/games/{g['gameId']}": g, f"/lol-match-history/v1/game-timelines/{g['gameId']}": tl}
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "perfil.json").write_text(json.dumps({"account": {"puuid": "puuid-de-la-api", "gameName": "j6", "tagLine": "test"}}), encoding="utf-8")
            self.assertEqual(cliente_v5.descargar(d, api.get)[0], 1)
            m = json.loads((pathlib.Path(d) / "LA1_1761893743.json").read_text(encoding="utf-8"))
            self.assertIn("puuid-de-la-api", [p["puuid"] for p in m["info"]["participants"]])  # eres tú, con el puuid de tu perfil
            self.assertNotIn("puuid-6", json.dumps(m))


if __name__ == "__main__": unittest.main()
