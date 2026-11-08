"""Pruebas de builds.py sin red: la build de una partida (undo, botas, orden de habilidades), el resumen, la búsqueda
de los mejores con la Riot API simulada (urlopen falso, caché en carpeta temporal) y lo que lee draft.py."""
import io, json, os, pathlib, sys, tempfile, time, unittest, urllib.error
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import builds  # noqa: E402

ITEMS = {"1001": dict(name="Botas", gold=dict(total=300), into=["3006"], tags=["Boots"]),
         "3006": dict(name="Grebas", gold=dict(total=1100), into=["3172"], tags=["Boots"]),
         "1055": dict(name="Espada de Doran", gold=dict(total=450), tags=[]),
         "3153": dict(name="Rey Arruinado", gold=dict(total=3200), tags=[]),
         "6673": dict(name="Arcoescudo", gold=dict(total=3000), tags=[]),
         "3031": dict(name="Filo", gold=dict(total=3400), tags=[])}
PERKS = dict(styles=[dict(style=8000, selections=[dict(perk=8008), dict(perk=9111), dict(perk=9104), dict(perk=8299)]),
                     dict(style=8400, selections=[dict(perk=8444), dict(perk=8453)])])


def partida(puuid="yo", champ="Yone", pos="MIDDLE", win=True, mid="KR_1", compras=("1055", "3153", "1001", "3006", "6673", "3031")):
    ps = [dict(puuid=puuid, participantId=1, championName=champ, teamPosition=pos, win=win, perks=PERKS)] + \
         [dict(puuid=f"x{i}", participantId=i, championName="Ahri", teamPosition="TOP", win=not win, perks=PERKS) for i in range(2, 11)]
    ev = [dict(type="ITEM_PURCHASED", participantId=1, itemId=int(i)) for i in compras]
    ev.insert(1, dict(type="ITEM_PURCHASED", participantId=1, itemId=3031))  # comprado y deshecho: no cuenta
    ev.insert(2, dict(type="ITEM_UNDO", participantId=1, beforeId=3031, afterId=0))
    ev += [dict(type="SKILL_LEVEL_UP", participantId=1, skillSlot=s, levelUpType="NORMAL") for s in (1, 3, 2, 1, 1, 4, 3, 1, 3)]
    ev += [dict(type="ITEM_PURCHASED", participantId=2, itemId=3031)]  # de otro jugador
    return (dict(metadata=dict(matchId=mid), info=dict(participants=ps, gameDuration=1800)),
            dict(info=dict(participants=[dict(participantId=p["participantId"], puuid=p["puuid"]) for p in ps], frames=[dict(events=ev)])))


class Build(unittest.TestCase):
    def test_build_de(self):
        b = builds.build_de(*partida(), "yo", ITEMS)
        self.assertEqual(b["core"], ["3153", "6673", "3031"])  # el Filo deshecho no va primero
        self.assertEqual(b["botas"], "3006")
        self.assertEqual(b["skills"], "Q>E>W")
        self.assertEqual(b["runas"][1], 8008)

    def test_resumir_y_lineas(self):
        bs = [builds.build_de(*partida(win=w), "yo", ITEMS) for w in (True, True, False)]
        r = builds.resumir(bs, ITEMS, {8008: "Ritmo Letal"})
        self.assertEqual((r["n"], round(r["wr"], 2), r["core"][0][0], r["botas"][0]), (3, 0.67, "Rey Arruinado", "Grebas"))
        ls = builds.lineas(json.loads(json.dumps(r)), "Los mejores")  # como sale de builds.json
        self.assertEqual(len(ls), 3); self.assertIn("Rey Arruinado (100%) → Arcoescudo", ls[0]); self.assertIn("Ritmo Letal", ls[1])
        self.assertIsNone(builds.resumir([], ITEMS, {}))


class Riot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(builds, "META", pathlib.Path(self.tmp.name)); p.start(); self.addCleanup(p.stop)
        p = mock.patch.object(builds.time, "sleep"); p.start(); self.addCleanup(p.stop)
        self.urls = []

    def falso(self, ahora):
        lad = dict(entries=[dict(puuid="viejo", leaguePoints=2000), dict(puuid="nunca", leaguePoints=1900),
                            dict(puuid="top1", leaguePoints=1800), dict(puuid="top2", leaguePoints=1700), dict(puuid="top3", leaguePoints=1600)])
        resp = {"challengerleagues": lad, "grandmasterleagues": dict(entries=[]),
                "by-puuid/viejo/by-champion": dict(lastPlayTime=(ahora - 30 * 86400) * 1000),
                "by-puuid/top1/by-champion": dict(lastPlayTime=ahora * 1000), "by-puuid/top2/by-champion": dict(lastPlayTime=ahora * 1000),
                "accounts/by-puuid/top1": dict(gameName="Uno", tagLine="KR1"), "accounts/by-puuid/top2": dict(gameName="Dos", tagLine="KR2"),
                "top1/ids": ["M1", "M2"], "top2/ids": ["M3"]}
        mt = {"M1": partida("top1"), "M2": partida("top1", champ="Ahri"), "M3": partida("top2", pos="TOP")}

        def urlopen(req, timeout=None):
            u = req.full_url; self.urls.append(u)
            assert req.get_header("X-riot-token") == "falsa"
            for k, v in mt.items():
                if u.endswith(f"/matches/{k}"): return io.BytesIO(json.dumps(v[0]).encode())
                if u.endswith(f"/matches/{k}/timeline"): return io.BytesIO(json.dumps(v[1]).encode())
            for k, v in resp.items():
                if k in u: return io.BytesIO(json.dumps(v).encode())
            raise urllib.error.HTTPError(u, 404, "no", {}, None)
        return urlopen

    def test_mejores_con_api_simulada(self):
        ahora = time.time()
        with mock.patch.dict(os.environ, RIOT_KEY="falsa"), mock.patch.object(builds.urllib.request, "urlopen", self.falso(ahora)):
            top = builds.mejores(777, "Yone", "MIDDLE", ahora=ahora)
            n = len(self.urls)
            otra = builds.mejores(777, "Yone", "MIDDLE", ahora=ahora)
        # top1 (M1 con Yone mid; M2 es Ahri), top2 (M3 es top: no entra), «viejo» (30 días) y «nunca» (404) fuera
        self.assertEqual([(m["metadata"]["matchId"], q) for m, _, _, q in top], [("KR_1", "Uno#KR1 (la1, 1800 LP)"), ("KR_1", "Uno#KR1 (kr, 1800 LP)")])
        self.assertEqual(len(self.urls), n)  # la segunda vez, todo de la caché
        self.assertEqual(len(otra), len(top))
        self.assertFalse(any("falsa" in f.read_text() for f in pathlib.Path(self.tmp.name).rglob("*.json")))  # la key no se guarda

    def test_sin_key(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(builds.SinKey):
            builds.mejores(777, "Yone")

    def test_401(self):
        def urlopen(req, timeout=None): raise urllib.error.HTTPError(req.full_url, 401, "no", {}, None)
        with mock.patch.dict(os.environ, RIOT_KEY="falsa"), mock.patch.object(builds.urllib.request, "urlopen", urlopen), \
                self.assertRaises(builds.SinKey):
            builds.mejores(777, "Yone")
        self.assertFalse(list(pathlib.Path(self.tmp.name).rglob("*.json")))  # un 401 no queda en caché

    def test_429_sostenido_no_cachea(self):  # antes: UnboundLocalError al escribir la caché (revisión de DeepSeek)
        def urlopen(req, timeout=None): raise urllib.error.HTTPError(req.full_url, 429, "lento", {"Retry-After": "1"}, None)
        with mock.patch.dict(os.environ, RIOT_KEY="falsa"), mock.patch.object(builds.urllib.request, "urlopen", urlopen), \
                self.assertRaises(urllib.error.HTTPError):
            builds.get("https://la1.api.riotgames.com/x", riot=True)
        self.assertFalse(list(pathlib.Path(self.tmp.name).rglob("*.json")))

    def test_guardado_para_draft(self):
        self.assertEqual(builds.guardado("Yone", "MIDDLE"), [])
        r = builds.resumir([builds.build_de(*partida(), "yo", ITEMS)], ITEMS, {})
        (pathlib.Path(self.tmp.name) / "builds.json").write_text(json.dumps({"Yone|MIDDLE": r}), encoding="utf-8")
        self.assertEqual(len(builds.guardado("Yone", "MIDDLE")), 3)
        self.assertEqual(builds.guardado("Yone", "TOP"), [])

    def test_guardado_sin_los_mejores_da_la_tuya(self):
        r = builds.resumir([builds.build_de(*partida(), "yo", ITEMS)], ITEMS, {})
        f = pathlib.Path(self.tmp.name) / "builds.json"
        f.write_text(json.dumps({"Yone|MIDDLE|tu": r}), encoding="utf-8")
        ls = builds.guardado("Yone", "MIDDLE")
        self.assertEqual(len(ls), 3); self.assertTrue(ls[0].startswith("Tu build"))
        f.write_text(json.dumps({"Yone|MIDDLE": r, "Yone|MIDDLE|tu": r}), encoding="utf-8")
        self.assertTrue(builds.guardado("Yone", "MIDDLE")[0].startswith("Los mejores"))  # la de los mejores manda


if __name__ == "__main__":
    unittest.main()
