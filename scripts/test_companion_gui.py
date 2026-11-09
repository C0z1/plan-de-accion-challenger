"""python -m unittest discover scripts  (sin red, sin cliente y sin abrir ventana)"""
import json, os, pathlib, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import companion_gui as g

SALIDA = """# Revisión
## Partida por partida (más reciente primero)

| Fecha | Campeón | | Oro @14 | CS @14 | Muertes <14 | Muertes 14–25 | Control wards |
|---|---|---|---|---|---|---|---|
| 11-07 21:36 | Veigar (fuera del pool) | D | -789 | -8 | 3 | 5 | 0 |
| 11-07 21:06 | Ekko | V | +120 | - | 0 | 0 | 1 |
"""


class TestParsear(unittest.TestCase):
    def test_toma_la_mas_reciente(self):
        r = g.parsear_revision(SALIDA)
        self.assertEqual((r["champ"], r["pool"], r["win"], r["oro"], r["m25"]), ("Veigar", False, False, "-789", "5"))

    def test_sin_tabla(self):
        self.assertIsNone(g.parsear_revision("nada"))


class TestPerfil(unittest.TestCase):
    def test_rango_del_cliente_gana_al_perfil_viejo(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            orig, g.RAW = g.RAW, pathlib.Path(t)
            try:
                (g.RAW / "perfil.json").write_text(json.dumps({"account": {"gameName": "Jugador", "tagLine": "LAN"},
                    "league": [{"queueType": "RANKED_SOLO_5x5", "tier": "MASTER", "rank": "I", "leaguePoints": 15}]}))
                self.assertEqual(g.perfil(), "Jugador#LAN · Master 15 LP")
                r = {"tier": "MASTER", "division": None, "lp": 42, "wins": 120, "losses": 100, "n": 220, "wr": 55}
                self.assertEqual(g.perfil(r), "Jugador#LAN · Master 42 LP · 120-100 (55%)")
                self.assertEqual(g.perfil({**r, "tier": "DIAMOND", "division": "II", "n": 0}), "Jugador#LAN · Diamond II 42 LP")
            finally: g.RAW = orig


class TestLineasFicha(unittest.TestCase):
    REF = dict(n=50, oro14=-118, cs14=-3, xp14=-50, nivel6=0.0, muertes6=0.6)

    def ficha(self, n=8, notas=(), lista=()):
        c = dict(rival="Viktor", n=n, v=1 if n else 0, ic=[0.02, 0.47], pocas=n < 5, oro14=-120 if n else None, cs14=-17 if n else None,
                 xp14=None, nivel6=-0.04 if n else None, muertes6=None, ref=self.REF, notas=list(notas))
        return dict(rival="Viktor", cuidado=c, counters=dict(lista=list(lista), ref=self.REF))

    def test_cuidado_y_counters(self):
        x = dict(rival="Diana", n=3, v=0, ic=[0, 0.56], pocas=True, cs14=7, oro14=None)
        cu, co = g.lineas_ficha(self.ficha(notas=["pega al 3"], lista=[x]))
        self.assertEqual(cu[0], "Tú contra Viktor (cualquier campeón): 1-7 (Wilson 2%–47%)")
        self.assertIn("CS al 14 −17 (tu media −3)", cu)
        self.assertIn("Nivel al 6 +0.0 (tu media +0.0)", cu)  # sin «−0.0»
        self.assertFalse(any("Muertes" in l for l in cu))  # sin medida, sin renglón
        self.assertEqual(cu[-1], "Tu nota: pega al 3")
        self.assertEqual(co, ["Diana 0-3 (Wilson 0%–56%) · CS al 14 +7 (tu media −3); pista"])

    def test_sin_partidas_ni_ficha(self):
        self.assertEqual(g.lineas_ficha(self.ficha(n=0)), ([], []))
        self.assertEqual(g.lineas_ficha(self.ficha(n=0, notas=["x"]))[0], ["Tu nota: x"])
        self.assertEqual(g.lineas_ficha(None), ([], []))


class TestTrabajador(unittest.TestCase):
    def test_banner_de_nivel_una_vez(self):
        import json, queue
        c = g.companion
        d = json.loads((AQUI / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))
        orig = c.lcu, c.vivo, c.capturar, g.time.sleep, g.time.time
        vueltas = iter(range(3))
        def dormir(_):  # el bucle no termina solo: KeyboardInterrupt no lo atrapa su except Exception
            if next(vueltas, None) is None: raise KeyboardInterrupt
        reloj = iter(range(0, 10_000, 100))
        c.lcu, c.vivo, c.capturar = (lambda path: "InProgress"), (lambda: d), (lambda a, f: a)
        g.time.sleep, g.time.time = dormir, (lambda: next(reloj))
        q = queue.Queue()
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, c.vivo, c.capturar, g.time.sleep, g.time.time = orig
        avisos = [e[1] for e in list(q.queue) if e[0] == "aviso"]
        self.assertEqual(len(avisos), 1); self.assertIn("abajo de Zed", avisos[0]["texto"])
        self.assertEqual((avisos[0]["tipo"], avisos[0]["minuto"]), ("consejo", int(d["gameData"]["gameTime"] // 60)))
        metas = [e[1] for e in list(q.queue) if e[0] == "meta"]
        self.assertTrue(metas); self.assertEqual((metas[0]["nivel"], metas[0]["nivel_rival"], metas[0]["rival"]), (5, 6, "Zed"))

    def test_rango_al_entrar_a_champ_select(self):
        import queue
        c = g.companion
        orig = c.lcu, g.time.sleep
        vueltas = iter(range(2))
        def dormir(_):
            if next(vueltas, None) is None: raise KeyboardInterrupt
        stats = {"queueMap": {"RANKED_SOLO_5x5": {"tier": "MASTER", "division": "NA", "leaguePoints": 42, "wins": 1, "losses": 1}}}
        c.lcu = lambda path: stats if "ranked" in path else (None if "session" in path else "ChampSelect")
        g.time.sleep = dormir
        q = queue.Queue()
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, g.time.sleep = orig
        rangos = [e[1] for e in list(q.queue) if e[0] == "rango"]
        self.assertEqual([r["lp"] for r in rangos], [42])  # una vez al entrar, no en cada vuelta

    def test_meta_fase_y_texto(self):
        import json, copy
        c = g.companion
        d = json.loads((AQUI / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))
        mf = c.meta_fase(d, m10={"campeon": "Ekko", "minimo": 69})
        self.assertEqual((mf["minuto"], mf["campeon"], mf["cs_meta"]), (int(d["gameData"]["gameTime"] // 60), "Ekko", 69))
        self.assertIn("contra 6 (Zed)", g.texto_meta(mf)); self.assertIn("meta 69 al 10", g.texto_meta(mf))
        self.assertIsNone(c.meta_fase(d, m10={"campeon": "Sylas", "minimo": 69})["cs_meta"])
        self.assertNotIn("Muertes", g.texto_meta(mf))  # min 6: aún no cuenta
        self.assertIn("Muertes desde el 14: 2 (meta ≤ 2)", g.texto_meta({**mf, "minuto": 18, "muertes14": 2}))
        sin = copy.deepcopy(d)  # normales: sin position no hay rival, pero sí tus números
        for p in sin["allPlayers"]: p["position"] = ""
        mf = c.meta_fase(sin, m10={}); self.assertIsNone(mf["rival"]); self.assertNotIn("contra", g.texto_meta(mf))
        self.assertIsNone(c.meta_fase(None)); self.assertIsNone(c.meta_fase({"gameData": {"gameTime": None}}))
        nulos = {"activePlayer": None, "allPlayers": None, "gameData": None}  # la API los trae null mientras carga
        self.assertIsNone(c.meta_fase(nulos)); self.assertIsNone(c.aviso_nivel(nulos)); self.assertIsNone(c.aviso_minions(nulos, {"campeon": "Ekko", "minimo": 69}))
        sin_gd = dict(copy.deepcopy(d), gameData=None)  # tu jugador está pero gameData null → minuto 0, sin meta mal formada
        self.assertEqual(c.meta_fase(sin_gd, m10={"campeon": "Ekko"})["minuto"], 0)

    def test_error_es_tipo_error(self):
        import queue
        c, q = g.companion, queue.Queue()
        orig = c.lcu, g.time.sleep
        def dormir(_): raise KeyboardInterrupt
        c.lcu, g.time.sleep = (lambda path: 1 / 0), dormir
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, g.time.sleep = orig
        e = q.get_nowait()
        self.assertEqual(e[0], "aviso"); self.assertEqual((e[1]["tipo"], e[1]["minuto"]), ("error", None))
        self.assertIn("ZeroDivisionError", e[1]["texto"])

    def test_fin_con_la_ultima_foto(self):
        import queue
        c, q = g.companion, queue.Queue()
        orig = c.lcu, c.vivo, c.capturar, g.time.sleep, g.post_partida
        fases = iter(["InProgress", "EndOfGame", "EndOfGame"])
        def lcu(path):
            if (f := next(fases, None)) is None: raise KeyboardInterrupt
            return f
        d = json.loads((pathlib.Path(__file__).parent / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))
        c.lcu, c.vivo, c.capturar, g.time.sleep, g.post_partida = lcu, (lambda: d), (lambda a, x: a), (lambda _: None), (lambda q: None)
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, c.vivo, c.capturar, g.time.sleep, g.post_partida = orig
        fin = [e[1] for e in list(q.queue) if e[0] == "fin"]
        self.assertEqual(len(fin), 1); self.assertEqual((fin[0]["campeon"], fin[0]["kda"]), ("Ekko", "0/0/0"))  # una vez por partida

    def test_error_repetido_sale_una_vez(self):
        import queue
        c, q = g.companion, queue.Queue()
        orig = c.lcu, c.vivo, g.time.sleep
        vueltas = iter(range(3))
        def dormir(_):
            if next(vueltas, None) is None: raise KeyboardInterrupt
        c.lcu, c.vivo, g.time.sleep = (lambda path: "InProgress"), (lambda: 1 / 0), dormir  # la foto en vivo truena cada vuelta
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, c.vivo, g.time.sleep = orig
        tipos = [e[0] for e in list(q.queue)]
        self.assertEqual((tipos.count("aviso"), tipos.count("fase")), (1, 1))  # antes: 4 y 4 (uno por vuelta)


class TestPostPartida(unittest.TestCase):
    def test_no_bloquea_ni_se_duplica(self):
        import queue, threading
        sigue, llamadas, orig = threading.Event(), [], g._post_partida
        g._post_partida = lambda q: (llamadas.append(1), sigue.wait(5))
        try:
            q = queue.Queue()
            g.post_partida(q); g.post_partida(q)  # la 2.ª llega con la 1.ª aún corriendo: no lanza otra
            self.assertTrue(g.POST[0].is_alive())
            sigue.set(); g.POST[0].join(5)
            self.assertEqual(llamadas, [1])
        finally: g._post_partida = orig

    def test_revision_en_champ_select_espera_a_la_partida(self):
        vistas = []
        app = g.App.__new__(g.App)  # sin ventana: solo el enrutado de eventos
        app.fase, app.pendiente = "ChampSelect", None
        app.vista_revision, app.espera = vistas.append, lambda t: vistas.append("espera")
        app.pill = app.sub = app.key = type("W", (), {"config": lambda self, **k: None})()
        app.evento(("post_espera", "Esperando…")); app.evento(("revision", {"champ": "Ekko"}))
        self.assertEqual(vistas, [])  # no tapa el draft
        app.evento(("fase", "InProgress"))
        self.assertEqual(vistas, [{"champ": "Ekko"}])


if __name__ == "__main__":
    unittest.main()
