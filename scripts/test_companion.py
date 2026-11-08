"""python -m unittest discover scripts  (sin red ni key)"""
import contextlib, io, json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import companion

FIX = pathlib.Path(__file__).parent / "fixtures"


def sesion(nombre): return json.loads((FIX / nombre / "session.json").read_text())


class Rivales(unittest.TestCase):
    def test_rival_de_tu_posicion(self):
        self.assertEqual(companion.rivales(sesion("champselect")), ("MIDDLE", [112]))  # Viktor mid, no Graves

    def test_sin_rol_van_todos_los_elegidos(self):
        self.assertEqual(companion.rivales(sesion("champselect-sin-rol")), ("TOP", [64, 238]))

    def test_nadie_elegido(self):
        self.assertEqual(companion.rivales({"localPlayerCellId": 0, "myTeam": [], "theirTeam": []}), ("MIDDLE", []))

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
        self.assertIn("1 nivel abajo de Zed (5 contra 6)", txt); self.assertIn("No tradees hasta igualar", txt)

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
        self.assertEqual(out.getvalue().count("No tradees"), 2)  # 1 en la primera partida, 1 en la segunda


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
        self.assertEqual(out.count("No tradees"), 1)  # el aviso no se repite tras el reinicio
        self.assertEqual(self.posts, [1])  # reinicio en EndOfGame: no baja la partida dos veces
        self.assertEqual(self.esperas, [3, 6, 12, 24, 3, 3, 6, 3, 3])

    def test_un_error_no_tumba_el_bucle(self):
        orig = companion.aviso_nivel
        companion.aviso_nivel = lambda d: 1 / 0
        try: out = self.bucle(["InProgress", "InProgress"])
        finally: companion.aviso_nivel = orig
        self.assertEqual(out.count("Error (sigo)"), 2)


if __name__ == "__main__": unittest.main()
