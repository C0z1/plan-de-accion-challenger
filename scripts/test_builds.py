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


class PaginaIds(unittest.TestCase):  # A5: la página completa (estilos, 6 runas y 3 fragmentos) para importarla al cliente
    def test_pagina_ids(self):
        m, t = partida()
        for x in m["info"]["participants"]: x["perks"] = dict(PERKS, statPerks=dict(offense=5005, flex=5008, defense=5011))
        r = builds.resumir([builds.build_de(m, t, "yo", ITEMS)], ITEMS, {})
        self.assertEqual(r["pagina_ids"], dict(primaryStyleId=8000, subStyleId=8400,
                                               selectedPerkIds=[8008, 9111, 9104, 8299, 8444, 8453, 5005, 5008, 5011]))
        self.assertIsNone(builds.resumir([builds.build_de(*partida(), "yo", ITEMS)], ITEMS, {})["pagina_ids"])  # sin fragmentos: no se inventan


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
        with mock.patch.dict(os.environ, RIOT_KEY="falsa"), mock.patch.object(builds.urllib.request, "urlopen", self.falso(ahora)),                 mock.patch.object(builds, "REGIONES", {"la1": "americas", "kr": "asia"}):
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

    def test_subir_y_bajar_del_backend(self):  # v0.8: el admin sube las de los mejores; los amigos sin key las bajan
        f = pathlib.Path(self.tmp.name) / "builds.json"
        r = builds.resumir([builds.build_de(*partida(), "yo", ITEMS)], ITEMS, {})
        f.write_text(json.dumps({"Yone|MIDDLE": r, "Yone|MIDDLE|tu": r}), encoding="utf-8")
        llamadas = []
        with mock.patch.object(builds, "_backend", lambda m, ruta, c=None: llamadas.append((m, ruta, c))):
            self.assertEqual(builds.subir(), 1)
        self.assertEqual(list(llamadas[0][2]), ["Yone|MIDDLE"])  # «tu build» no se sube
        servidor = {"/v1/builds/_todas": [{"clave": "Yone|MIDDLE", "ts": 5, "datos": dict(r, n=1)}, {"clave": "Ahri|MIDDLE", "ts": 5, "datos": dict(r, n=99)}]}
        pedidas = []
        def falso(m, ruta, c=None): pedidas.append(ruta); return servidor.get(ruta)
        with mock.patch.object(builds, "_backend", falso):
            self.assertEqual(builds.bajar(), 1)  # Yone ya la calculaste tú: no se pisa
            self.assertEqual(builds.bajar(), 0)  # ya al día: no se vuelve a pedir
        self.assertEqual(set(pedidas), {"/v1/builds/_todas"})  # una sola consulta, no una por clave
        d = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual((d["Ahri|MIDDLE"]["n"], d["Yone|MIDDLE"]["n"]), (99, r["n"]))
        self.assertEqual(builds.guardado_dict("Ahri", "MIDDLE")["fuente"], "mejores")
        def caido(m, ruta, c=None): raise urllib.error.URLError("sin red")
        with mock.patch.object(builds, "_backend", caido): self.assertEqual(builds.bajar(), 0)

    def test_guardado_dict_y_primer_item(self):
        self.assertIsNone(builds.guardado_dict("Yone", "MIDDLE"))
        r = builds.resumir([builds.build_de(*partida(), "yo", ITEMS)], ITEMS, {})
        f = pathlib.Path(self.tmp.name) / "builds.json"
        f.write_text(json.dumps({"Yone|MIDDLE|tu": r}), encoding="utf-8")
        d = builds.guardado_dict("Yone", "MIDDLE")
        self.assertEqual((d["fuente"], d["core"][0][0]), ("tu", "Rey Arruinado"))
        top = dict(r, primer=dict(item="Rey Arruinado", si=[7, 10], no=[2, 6]))
        f.write_text(json.dumps({"Yone|MIDDLE": top}), encoding="utf-8")
        self.assertEqual(builds.guardado_dict("Yone", "MIDDLE")["fuente"], "mejores")
        ls = builds.guardado("Yone", "MIDDLE")
        self.assertEqual(len(ls), 4); self.assertIn("7/10 = 70%", ls[3]); self.assertIn("2/6 = 33%", ls[3])
        f.write_text(json.dumps({"Yone|MIDDLE": dict(r, primer=dict(item="X", si=[3, 3], no=[0, 0]))}), encoding="utf-8")
        self.assertEqual(len(builds.guardado("Yone", "MIDDLE")), 3)  # sin partidas con otro ítem no hay comparación
        f.write_text('{"Yone|MIDDLE": {"n"', encoding="utf-8")  # cortado a media escritura
        self.assertEqual(builds.guardado("Yone", "MIDDLE"), [])

    def test_informe_guarda_primer(self):
        mt, tl = partida("top1")
        with mock.patch.object(builds, "ddragon", return_value=(ITEMS, {}, {"yone": ("Yone", 777)})), \
                mock.patch.object(builds, "mejores", return_value=[(mt, tl, "top1", "Uno#KR1")]), \
                mock.patch.object(builds, "tuyas", return_value=[(*partida(win=True), "yo"), (*partida(win=False, compras=("6673", "3153")), "yo")]):
            _, rt, _ = builds.informe("Yone", "MIDDLE")
        self.assertEqual(rt["primer"], dict(item="Rey Arruinado", si=[1, 1], no=[0, 1]))

    def test_por_primer(self):
        b = lambda c, w: dict(core=c, win=w)
        bs = [b(["1"], True)] * 5 + [b(["2"], False)] * 6 + [b(["3"], True)] * 4 + [b([], True)]
        pp = builds.por_primer(bs, {"1": {"name": "Uno"}})
        self.assertEqual([(nm, len(v), sum(x["win"] for x in v)) for nm, v in pp], [("2", 6, 0), ("Uno", 5, 5)])
        self.assertEqual(builds.por_primer([], {}), [])

    def test_por_clase_y_rival(self):
        mt, tl = partida()
        for i, x in enumerate(mt["info"]["participants"]): x["teamId"] = 100 if i < 5 else 200
        mt["info"]["participants"][7]["teamPosition"] = "MIDDLE"; mt["info"]["participants"][7]["championName"] = "Zed"
        self.assertEqual(builds.build_de(mt, tl, "yo", ITEMS)["rival"], "Zed")
        self.assertIsNone(builds.build_de(*partida(), "yo", ITEMS)["rival"])  # sin teamId ni rival de su posición
        b = lambda c, r, w: dict(core=[c], rival=r, win=w)
        cl = {"Zed": "Assassin", "Lux": "Mage", "Ahri": "Mage"}
        bs = [b("1", "Lux", True)] * 5 + [b("2", "Ahri", False)] * 5 + [b("1", "Zed", True)] * 3 + [b("2", None, True)] * 9
        c, pp = builds.por_clase(bs, ITEMS, cl)
        self.assertEqual((c, [(nm, len(v), sum(x["win"] for x in v)) for nm, v in pp]), ("Mage", [("1", 5, 5), ("2", 5, 0)]))
        self.assertIsNone(builds.por_clase(bs[:5], ITEMS, cl))  # un solo ítem en la clase: no hay comparación
        self.assertIsNone(builds.por_clase([b("1", None, True)], ITEMS, cl))


class Ladder(unittest.TestCase):
    """--ladder: builds Master+ de todos los campeones; cada partida da las de todos los del ladder que jugaron."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        m = pathlib.Path(self.tmp.name)
        for p in (mock.patch.object(builds, "META", m), mock.patch.object(builds, "FILAS", m / "builds-filas.jsonl"),
                  mock.patch.object(builds, "ddragon", return_value=(ITEMS, {}, {}))):
            p.start(); self.addCleanup(p.stop)

    def mt(self, puuid, version="15.22.3", **kw):
        m, tl = partida(puuid, **kw); m["info"]["gameVersion"] = version; return m, tl

    def test_parches(self):
        self.assertEqual(builds.parches_validos("15.22.1"), {"15.22", "15.21"})
        self.assertEqual(builds.parches_validos("16.1.1"), {"16.1"})

    def test_fila_solo_ladder_sin_remake(self):
        m, tl = partida("top1")
        self.assertEqual([b["champ"] for b in builds.fila_ladder(m, tl, {"top1", "nadie"}, ITEMS)], ["Yone"])
        self.assertEqual(len(builds.fila_ladder(m, tl, {"top1", "x2", "x3"}, ITEMS)), 3)  # un match, varias builds
        m["info"]["gameDuration"] = 400; self.assertEqual(builds.fila_ladder(m, tl, {"top1"}, ITEMS), [])

    def test_rastrear_reanuda_y_filtra_parche(self):
        lad = dict(entries=[dict(puuid="top1", leaguePoints=900), dict(puuid="top2", leaguePoints=800)])
        mts = {"M1": self.mt("top1"), "M2": self.mt("top1", version="15.10.1"), "M3": self.mt("top2", pos="TOP")}
        pedidas = []
        def get(url, ttl=None, riot=False, guardar=True):
            pedidas.append(url)
            if "versions.json" in url: return ["15.22.1"]
            if "challengerleagues" in url: return lad
            if "leagues" in url: return dict(entries=[])
            if "top1/ids" in url: return ["M1", "M2"]
            if "top2/ids" in url: return ["M1", "M3"]
            mid = url.rsplit("/", 2)[-2] if url.endswith("timeline") else url.rsplit("/", 1)[-1]
            return mts[mid][1] if url.endswith("timeline") else mts[mid][0]
        with mock.patch.object(builds, "get", get):
            self.assertEqual(builds.rastrear_ladder(regiones=["kr"]), 2)  # M1 y M3; M2 es de otro parche
            self.assertEqual(sum("timeline" in u for u in pedidas), 2)
            self.assertEqual(builds.rastrear_ladder(regiones=["kr"]), 0)  # reanuda: nada nuevo
        filas = [json.loads(l) for l in builds.FILAS.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(f["id"], len(f["builds"])) for f in filas], [("M1", 1), ("M2", 0), ("M3", 1)])

    def test_sinkey_guarda_lo_bajado(self):
        def get(url, ttl=None, riot=False, guardar=True):
            if "versions.json" in url: return ["15.22.1"]
            if "challengerleagues" in url: return dict(entries=[dict(puuid="top1", leaguePoints=1)])
            if "leagues" in url: return dict(entries=[])
            if "ids" in url: return ["M1", "M2"]
            if url.endswith("M2"): raise builds.SinKey("caducó")
            return self.mt("top1")[1] if url.endswith("timeline") else self.mt("top1")[0]
        with mock.patch.object(builds, "get", get), self.assertRaises(builds.SinKey): builds.rastrear_ladder(regiones=["kr"])
        self.assertEqual(len(builds.FILAS.read_text(encoding="utf-8").splitlines()), 1)

    def test_agregar_umbral_y_mezclar(self):
        m, tl = partida("top1")
        b = json.loads(json.dumps(builds.build_de(m, tl, "top1", ITEMS)))  # como sale del JSONL: listas, no tuplas
        filas = [dict(id=f"M{i}", parche="15.22", builds=[b]) for i in range(25)] + [dict(id="R", parche="15.22", builds=[dict(b, pos="TOP")])]
        builds.FILAS.write_text(chr(10).join(json.dumps(f) for f in filas), encoding="utf-8")
        a = builds.agregar_ladder()
        self.assertEqual(list(a), ["Yone|MIDDLE"]); self.assertEqual((a["Yone|MIDDLE"]["n"], a["Yone|MIDDLE"]["origen"]), (25, "ladder"))
        self.assertEqual(builds.agregar_ladder(minimo=30), {})
        (builds.META / "builds.json").write_text(json.dumps({"Yone|MIDDLE": {"jugadores": ["Faker"]}, "_bajadas": {"x": 1}}), encoding="utf-8")
        self.assertEqual(builds.mezclar(a), 0)  # el onetrick manda
        d = json.loads((builds.META / "builds.json").read_text(encoding="utf-8"))
        self.assertEqual((d["Yone|MIDDLE"], d["_bajadas"]), ({"jugadores": ["Faker"]}, {"x": 1}))
        self.assertEqual(builds.mezclar(a, pisar_onetricks=True), 1)

    def test_subir_en_trozos(self):
        (builds.META / "builds.json").write_text(json.dumps({f"C{i:03}|TOP": {"n": i} for i in range(250)}), encoding="utf-8")
        envios = []
        with mock.patch.object(builds, "_backend", lambda m, r, c=None: envios.append(len(c))):
            self.assertEqual(builds.subir(), 250)
        self.assertEqual(envios, [100, 100, 50])


if __name__ == "__main__":
    unittest.main()
