"""python -m unittest discover scripts  (sin red ni key)"""
import contextlib, io, json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import companion
companion._METAS = {}  # sin meta automática: estas pruebas no dependen de tus partidas (test_cs_meta.py la prueba)

FIX = pathlib.Path(__file__).parent / "fixtures"


def sesion(nombre): return json.loads((FIX / nombre / "session.json").read_text())


class Rivales(unittest.TestCase):
    def test_rival_de_tu_posicion(self):
        self.assertEqual(companion.rivales(sesion("champselect")), ("MIDDLE", [112]))  # Viktor mid, no Graves

    def test_sin_rol_van_todos_los_elegidos(self):
        self.assertEqual(companion.rivales(sesion("champselect-sin-rol")), ("TOP", [64, 238]))

    def test_nadie_elegido(self):
        self.assertEqual(companion.rivales({"localPlayerCellId": 0, "myTeam": [], "theirTeam": []}), ("MIDDLE", []))

    def test_equipos_y_rol_en_null(self):
        self.assertEqual(companion.rivales({"localPlayerCellId": 0, "myTeam": None, "theirTeam": None}), ("MIDDLE", []))
        s = sesion("champselect")
        for p in s["myTeam"] + s["theirTeam"]: p["assignedPosition"] = None
        self.assertEqual(companion.rivales(s)[0], "MIDDLE")  # sin rol: todos los elegidos, como en normales

    def test_con_roles_espera_a_tu_rival(self):
        s = sesion("champselect")
        for p in s["theirTeam"]:
            if p.get("assignedPosition") == "middle": p["championId"] = 0  # el mid rival aún no elige
        self.assertEqual(companion.rivales(s), ("MIDDLE", []))  # no recomienda contra Graves jungla

    def test_fase_del_fixture(self):
        self.assertEqual(json.loads((FIX / "champselect" / "gameflow-phase.json").read_text()), "ChampSelect")


def foto(): return json.loads((FIX / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))


class AvisoNivel(unittest.TestCase):
    def test_abajo_de_tu_rival_de_linea(self):  # Ekko 5 contra Zed 6; Graves (aliado, 6) y Lee Sin (4) no cuentan
        txt = companion.aviso_nivel(foto())
        self.assertIn("1 nivel abajo de Zed (5 contra 6)", txt); self.assertIn("no tradear hasta igualar", txt)

    def test_nivel_igual_o_arriba_no_avisa(self):
        for lvl in (6, 7):
            d = foto(); d["allPlayers"][0]["level"] = lvl
            self.assertIsNone(companion.aviso_nivel(d))

    def test_fuera_del_minuto_5_al_7_no_avisa(self):
        for t in (299.0, 421.0):
            d = foto(); d["gameData"]["gameTime"] = t
            self.assertIsNone(companion.aviso_nivel(d))

    def test_sin_position_o_sin_datos_no_avisa(self):
        d = foto()
        for p in d["allPlayers"]: p["position"] = ""  # normales: no se sabe tu rival
        for x in (d, None, {}, {"gameData": {"gameTime": 360}}): self.assertIsNone(companion.aviso_nivel(x))

    def test_solo_summonerName_y_plural(self):
        d = foto(); del d["activePlayer"]["riotId"]
        for p in d["allPlayers"]: p.pop("riotId")
        d["allPlayers"][2]["level"] = 7
        self.assertIn("2 niveles abajo de Zed", companion.aviso_nivel(d))

    def test_minions_al_10(self):
        m10 = {"campeon": "Ekko", "minimo": 69}
        d = foto(); d["gameData"]["gameTime"] = 610; d["allPlayers"][0]["scores"]["creepScore"] = 60
        self.assertIn("llevas 60 de CS con Ekko (tu meta: 69)", companion.aviso_minions(d, m10))
        d["allPlayers"][0]["scores"]["creepScore"] = 69
        self.assertIsNone(companion.aviso_minions(d, m10))  # en la meta: no avisa
        d["allPlayers"][0]["scores"]["creepScore"] = None
        self.assertIn("llevas 0", companion.aviso_minions(d, m10))  # null no truena
        for t in (599, 661, None): d["gameData"]["gameTime"] = t; self.assertIsNone(companion.aviso_minions(d, m10))
        d["gameData"]["gameTime"] = 610
        self.assertIsNone(companion.aviso_minions(d, {"campeon": "Sylas", "minimo": 69}))  # otro campeón
        for x in (None, {}): self.assertIsNone(companion.aviso_minions(x, m10))

    def test_muertes_del_14_al_25(self):
        d = foto(); d["gameData"]["gameTime"] = 1000
        kill = lambda t, v: {"EventName": "ChampionKill", "EventTime": t, "VictimName": v, "KillerName": "Rival1"}
        d["events"]["Events"] += [kill(500, "Jugador"), kill(900, "Jugador"), kill(950, "Rival1#LAN")]  # antes del 14 y la de otro no cuentan
        self.assertEqual(companion.muertes14(d), 1); self.assertIsNone(companion.aviso_muertes(d))
        d["events"]["Events"].append(kill(990, "Jugador#LAN"))  # con o sin #tag
        self.assertIn("2 muertes desde el 14", companion.aviso_muertes(d))
        self.assertEqual(companion.meta_fase(d, {})["muertes14"], 2)
        for t in (839, 1500, None): d["gameData"]["gameTime"] = t; self.assertIsNone(companion.aviso_muertes(d))
        d["gameData"]["gameTime"] = 600; self.assertIsNone(companion.meta_fase(d, {})["muertes14"])
        d["gameData"]["gameTime"] = 1000; d["events"] = None; self.assertIsNone(companion.aviso_muertes(d))  # null no truena
        for x in (None, {}): self.assertIsNone(companion.aviso_muertes(x))

    def test_rival_y_objetivos(self):  # formato de eventos tomado de una partida real (KillerName sin tag, torres por dueño)
        d = foto(); d["gameData"]["gameTime"] = 1000
        d["allPlayers"][2]["items"] = [{"itemID": 3142, "displayName": "Espada fantasma", "slot": 0}, {"itemID": 2003, "consumable": True, "slot": 1}, {"itemID": 3340, "slot": 6}]
        d["allPlayers"][2]["scores"] = {"kills": 2, "deaths": 1, "assists": 0, "creepScore": 90}
        ev = lambda n, t, k, **x: {"EventName": n, "EventTime": t, "KillerName": k, **x}
        d["events"]["Events"] += [ev("DragonKill", 500, "Rival2"), ev("DragonKill", 800, "Aliado1"), ev("HordeKill", 400, "Rival2"),
            ev("HeraldKill", 900, "Desconocido"),  # no se sabe de quién: no cuenta
            ev("TurretKilled", 950, "Minion_T100L1S1", TurretKilled="Turret_TChaos_L1_P3_1_0"),  # torre rival caída = tuya
            ev("TurretKilled", 960, "Rival1", TurretKilled="Turret_TOrder_L0_P3_2_0")]
        m = companion.meta_fase(d, {}); o = m["objetivos"]
        self.assertEqual((m["rival_kda"], m["rival_cs"], m["rival_items"]), ("2/1/0", 90, [[3142, "Espada fantasma"]]))  # sin poción ni trinket
        self.assertEqual(o["tuyos"], {"kills": 0, "torres": 1, "dragones": 1, "larvas": 0, "heraldo": 0, "baron": 0})
        self.assertEqual(o["rival"], {"kills": 2, "torres": 1, "dragones": 1, "larvas": 1, "heraldo": 0, "baron": 0})
        self.assertEqual((o["dragon"], o["baron"]), (100, 200))  # 800 + 300 − 1000; barón al 20:00
        d["gameData"]["gameTime"] = 1250; self.assertIsNone(companion.meta_fase(d, {})["objetivos"]["dragon"])  # ya salió
        d = foto(); d["allPlayers"] = d["allPlayers"][:2]; m = companion.meta_fase(d, {})  # sin rival de línea
        self.assertEqual((m["rival_kda"], m["rival_items"]), (None, []))

    def test_linea_al_terminar(self):
        d = foto(); d["gameData"]["gameTime"] = 1860
        kill = lambda t: {"EventName": "ChampionKill", "EventTime": t, "VictimName": "Jugador"}
        d["events"]["Events"] += [kill(t) for t in (500, 900, 1000, 1499, 1500, 1700)]  # 900, 1000, 1499: del 14 al 25
        r = companion.resumen_fin(d)
        self.assertEqual((r["minuto"], r["kda"], r["muertes14_25"], r["muertes14"]), (31, "0/0/0", 3, 5))
        self.assertEqual(companion.linea_fin(r), "Min 31 · Ekko 0/0/0 contra Zed · CS 38 · muertes del 14 al 25: 3 (meta ≤ 2) ✕")
        d["gameData"]["gameTime"] = 700; d["allPlayers"][0]["scores"] = None  # acabó antes del 14, scores null
        self.assertEqual(companion.linea_fin(companion.resumen_fin(d)), "Min 11 · Ekko 0/0/0 contra Zed · CS ?")
        for x in (None, {}): self.assertIsNone(companion.linea_fin(companion.resumen_fin(x)))

    def test_cotejo_de_muertes_y_homonimo(self):
        d = foto(); d["gameData"]["gameTime"] = 1860; me = d["allPlayers"][0]
        me["riotId"] = "Jugador#LAN"; me["scores"] = {"deaths": 2}
        kill = lambda t, v: {"EventName": "ChampionKill", "EventTime": t, "VictimName": v}
        d["events"]["Events"] += [kill(900, "Otro"), kill(1000, "Otro")]  # VictimName en un formato que no reconoce
        r = companion.resumen_fin(d)
        self.assertIs(r["cotejo"], False); self.assertIn("no cuadran tus muertes", companion.linea_fin(r))
        d["events"]["Events"] += [kill(950, "Jugador")]  # sin #tag y nadie más lo comparte: cuenta
        self.assertTrue(companion.resumen_fin(d)["cotejo"])
        d["allPlayers"][1]["riotId"] = "Jugador#KR"  # homónimo en el otro equipo: el nombre corto ya no cuenta
        self.assertEqual(companion.muertes14(d), 0)
        d["events"]["Events"].append(kill(960, "Jugador#LAN"))
        self.assertEqual(companion.muertes14(d), 1)
        d["allPlayers"][1]["riotId"] = "Otro2#KR"; me["summonerName"] = "Jugador"
        d["allPlayers"][1]["summonerName"] = "Jugador"  # homónimo solo por summonerName: tampoco cuenta
        self.assertEqual(companion.muertes14(d), 1)
        self.assertIsNone(companion.rango({"queues": [None, "x", {"queueType": "RANKED_SOLO_5x5", "tier": "MASTER"}]})["division"])

    def test_el_bucle_da_la_linea_al_terminar(self):
        orig = companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.post_partida
        fases = iter(["InProgress", "InProgress", "EndOfGame", "EndOfGame"])
        fotos = iter([foto(), None])  # la segunda falla (partida cerrándose): queda la anterior
        companion.lcu = lambda path: next(fases); companion.vivo = lambda: next(fotos)
        companion.capturar = lambda a, d: a; companion.time.sleep = lambda _: None; companion.post_partida = lambda: None
        out = io.StringIO()
        try:
            with self.assertRaises(StopIteration), contextlib.redirect_stdout(out): companion.main([])
        finally: companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.post_partida = orig
        self.assertEqual(out.getvalue().count("Min 6 · Ekko 0/0/0 contra Zed"), 1)

    def test_el_bucle_avisa_una_vez_por_partida(self):
        orig = companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.time.time
        fases = iter(["InProgress"] * 3 + ["Lobby", "InProgress"])
        reloj = iter(range(0, 10_000, 100))  # cada sondeo, 100 s después: siempre toca foto
        companion.lcu = lambda path: next(fases)
        companion.vivo = foto; companion.capturar = lambda a, d: a
        companion.time.sleep = lambda _: None; companion.time.time = lambda: next(reloj)
        out = io.StringIO()
        try:
            with self.assertRaises(StopIteration), contextlib.redirect_stdout(out): companion.main([])
        finally: companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.time.time = orig
        self.assertEqual(out.getvalue().count("no tradear hasta igualar"), 2)  # 1 en la primera partida, 1 en la segunda


class Rango(unittest.TestCase):
    def test_rango_del_cliente(self):
        solo = {"queueType": "RANKED_SOLO_5x5", "tier": "MASTER", "division": "NA", "leaguePoints": 15, "wins": 120, "losses": 100}
        r = {"tier": "MASTER", "division": None, "lp": 15, "wins": 120, "losses": 100, "n": 220, "wr": 55}
        self.assertEqual(companion.rango({"queueMap": {"RANKED_SOLO_5x5": solo}}), r)
        self.assertEqual(companion.rango({"queues": [{"queueType": "RANKED_FLEX_SR", "tier": "GOLD"}, solo]}), r)  # sin queueMap
        self.assertEqual(companion.rango({"queueMap": {"RANKED_SOLO_5x5": {**solo, "tier": "DIAMOND", "division": "II", "wins": 0, "losses": 0}}})["division"], "II")
        for x in (None, {}, {"queueMap": None}, {"queueMap": {"RANKED_SOLO_5x5": {**solo, "tier": "NONE"}}}): self.assertIsNone(companion.rango(x))


class ConfigRoto(unittest.TestCase):
    def test_config_roto_no_tumba_la_partida(self):
        import tempfile
        orig = companion.CFG
        with tempfile.TemporaryDirectory() as t:
            companion.CFG = pathlib.Path(t) / "config.json"
            try:
                for txt in ('{"minions10": ', "[1]", '{"minions10": 5}'):
                    companion.CFG.write_text(txt, encoding="utf-8")
                    self.assertIsNone(companion.minions10())
                    self.assertIsNotNone(companion.meta_fase(foto())); self.assertIsNone(companion.aviso_minions(foto()))
                companion.CFG.write_text('{"minions10": {"campeon": "Ekko", "minimo": 69}}', encoding="utf-8")
                self.assertEqual(companion.meta_fase(foto())["cs_meta"], 69)
            finally: companion.CFG = orig


class Argumentos(unittest.TestCase):
    def test_help_y_argumento_raro_no_arrancan_el_bucle(self):
        for args in (["--help"], ["--algo"]):
            with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                companion.main(args)  # antes, cualquier argumento entraba al modo en vivo


class PostPartida(unittest.TestCase):
    def setUp(self):
        self.orig = companion.lcu, companion.post_partida, companion.time.sleep, companion.subprocess.run

    def tearDown(self):
        companion.lcu, companion.post_partida, companion.time.sleep, companion.subprocess.run = self.orig

    def test_end_of_game_dispara_una_vez(self):
        fases = iter(["InProgress", "PreEndOfGame", "EndOfGame", "EndOfGame", "Lobby"])
        llamadas = []
        companion.lcu = lambda path: next(fases)  # al acabarse las fases, StopIteration corta el bucle
        companion.post_partida = lambda: llamadas.append(1)
        companion.time.sleep = lambda _: None
        orig = companion.capturar, companion.vivo
        companion.capturar = lambda a, d: llamadas.append("vivo") or a; companion.vivo = lambda: None
        try:
            with self.assertRaises(StopIteration): companion.main([])
        finally: companion.capturar, companion.vivo = orig
        self.assertEqual(llamadas, ["vivo", 1])  # captura en InProgress; PreEndOfGame → EndOfGame no repite la descarga

    def test_capturar_agrega_fotos_al_mismo_archivo(self):
        import tempfile
        orig = companion.VIVO
        with tempfile.TemporaryDirectory() as t:
            try:
                companion.VIVO = pathlib.Path(t) / "vivo"
                self.assertIsNone(companion.capturar(None, None))  # sin partida no crea nada
                d = {"gameData": {"gameTime": 30.0}}
                a = companion.capturar(None, d)
                self.assertEqual(companion.capturar(a, d), a)
                self.assertEqual([json.loads(l)["gameData"]["gameTime"] for l in a.read_text(encoding="utf-8").splitlines()], [30.0, 30.0])
            finally: companion.VIVO = orig

    def corre(self, codigos):
        cmds = []
        companion.time.sleep = lambda _: None
        companion.subprocess.run = lambda cmd: (cmds.append(pathlib.Path(cmd[1]).name), type("R", (), {"returncode": codigos.pop(0)}))[1]
        companion.post_partida()
        return cmds

    def test_key_caducada_no_revisa(self):
        self.assertEqual(self.corre([2]), ["descargar.py"])

    def test_partida_sin_publicar_no_revisa_la_anterior(self):
        self.assertEqual(self.corre([3]), ["descargar.py"])

    def test_descarga_bien_revisa(self):
        self.assertEqual(self.corre([0, 0]), ["descargar.py", "revision.py"])


class Robusto(unittest.TestCase):
    """Cliente que se reinicia, lockfile nuevo o a medias, timeouts y JSON cortado (urlopen simulado, sin red)."""
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory(); self.lock = pathlib.Path(self.tmp.name) / "lockfile"
        self.orig = companion.LOCK, companion.urllib.request.urlopen
        companion.LOCK = self.lock; self.urls = []

    def tearDown(self):
        companion.LOCK, companion.urllib.request.urlopen = self.orig; self.tmp.cleanup()

    def responde(self, cuerpo=None, error=None):
        def urlopen(req, **kw):
            self.urls.append(getattr(req, "full_url", req))
            if error: raise error
            return io.BytesIO(cuerpo)
        companion.urllib.request.urlopen = urlopen

    def test_lockfile_ausente_o_a_medias(self):
        self.responde(b'"Lobby"')
        self.assertIsNone(companion.lcu("/x"))  # sin lockfile
        self.lock.write_text("LeagueClient:1234")  # el cliente aún lo está escribiendo
        self.assertIsNone(companion.lcu("/x")); self.assertEqual(self.urls, [])

    def test_lockfile_nuevo_tras_reinicio(self):
        self.responde(b'"Lobby"')
        self.lock.write_text("LeagueClient:1:50001:pw1:https"); self.assertEqual(companion.lcu("/x"), "Lobby")
        self.lock.write_text("LeagueClient:2:50002:pw2:https"); self.assertEqual(companion.lcu("/x"), "Lobby")
        self.assertEqual([u.split("/")[2] for u in self.urls], ["127.0.0.1:50001", "127.0.0.1:50002"])

    def test_timeout_y_json_cortado_dan_none(self):
        import http.client
        self.lock.write_text("LeagueClient:1:50001:pw:https")
        for kw in ({"error": TimeoutError()}, {"error": ConnectionResetError()}, {"cuerpo": b'{"gameData": {"gameTi'}):
            self.responde(**kw); self.assertIsNone(companion.lcu("/x")); self.assertIsNone(companion.vivo())
        class Roto(io.BytesIO):
            def read(self, *a): raise http.client.IncompleteRead(b"{")  # el cliente se cae a media respuesta
        companion.urllib.request.urlopen = lambda req, **kw: Roto()
        self.assertIsNone(companion.lcu("/x")); self.assertIsNone(companion.vivo())  # antes tumbaba el companion

    def test_espera_creciente(self):
        self.assertEqual([companion.espera(f) for f in range(6)], [3, 6, 12, 24, 30, 30])

    def bucle(self, fases):
        orig = companion.lcu, companion.vivo, companion.capturar, companion.post_partida, companion.time.sleep, companion.time.time
        fases, reloj, self.esperas, self.archivos, self.posts = iter(fases), iter(range(100, 10_000, 100)), [], [], []
        companion.lcu = lambda path: next(fases)
        companion.vivo = foto
        companion.capturar = lambda a, d: self.archivos.append(a or f"archivo{len(self.archivos)}") or self.archivos[-1]
        companion.post_partida = lambda: self.posts.append(1)
        companion.time.sleep = self.esperas.append; companion.time.time = lambda: next(reloj)
        out = io.StringIO()
        try:
            with self.assertRaises(StopIteration), contextlib.redirect_stdout(out): companion.main([])
        finally: companion.lcu, companion.vivo, companion.capturar, companion.post_partida, companion.time.sleep, companion.time.time = orig
        return out.getvalue()

    def test_reinicio_a_media_partida_sigue_la_misma(self):
        out = self.bucle(["InProgress", None, None, None, "InProgress", "EndOfGame", None, "EndOfGame", "Lobby"])
        self.assertEqual(set(self.archivos[:5]), {"archivo0"})  # sigue grabando en el mismo archivo con el cliente caído
        self.assertEqual(out.count("no tradear hasta igualar"), 1)  # el aviso no se repite tras el reinicio
        self.assertEqual(self.posts, [1])  # reinicio en EndOfGame: no baja la partida dos veces
        self.assertEqual(self.esperas, [3, 6, 12, 24, 3, 3, 6, 3, 3])

    def test_un_error_no_tumba_el_bucle(self):
        orig = companion.aviso_nivel
        companion.aviso_nivel = lambda d: 1 / 0
        try: out = self.bucle(["InProgress", "InProgress"])
        finally: companion.aviso_nivel = orig
        self.assertEqual(out.count("Error (sigo)"), 2)


if __name__ == "__main__": unittest.main()


class TestHistorialCliente(unittest.TestCase):  # v0.5: últimas partidas del cliente sin key de Riot
    def test_filtra_remakes_y_eventos_y_ordena(self):
        def g(gid, cola, dur, ts, win, champ=1):
            return {"gameId": gid, "queueId": cola, "gameDuration": dur, "gameCreation": ts,
                    "participants": [{"championId": champ, "stats": {"win": win, "kills": 3, "deaths": 1, "assists": 4, "totalMinionsKilled": 150, "neutralMinionsKilled": 10}}]}
        h = {"games": {"games": [g(1, 420, 1800, 100, True), g(2, 420, 200, 300, False), g(3, 2400, 1500, 400, True), g(4, 450, 1200, 200, False, 99)]}}
        r = companion.historial(h, {1: "Ahri"})
        self.assertEqual([(x["campeon"], x["cola"], x["win"]) for x in r], [("99", "ARAM", False), ("Ahri", "Solo/Duo", True)])
        self.assertEqual((r[1]["kda"], r[1]["cs"], r[1]["min"]), ("3/1/4", 160, 30))
        self.assertEqual(companion.historial(None, {}), [])


class UnirEventosOtraPartida(unittest.TestCase):  # Racha no vio el fin: la partida nueva (gameTime menor) no hereda eventos
    def test_partida_nueva_no_hereda(self):
        f = lambda t, ev: {"gameData": {"gameTime": t}, "events": {"Events": ev}}
        vieja = f(1800, [{"EventName": "DragonKill", "EventTime": 600}])
        self.assertEqual(companion.unir_eventos(f(30, [{"EventName": "GameStart", "EventTime": 0}]), vieja)["events"]["Events"],
                         [{"EventName": "GameStart", "EventTime": 0}])
