"""Pruebas de companion_web.py sin red, sin cliente ni navegador: estado JSON y HTTP servido."""
import io, http.client, http.server, json, pathlib, threading, time, unittest
from unittest import mock

import companion_web as w

FICHA = {"champ": "Sylas", "rival": "Ahri", "pos": "MIDDLE",
         "por_que": {"champ": "Sylas", "est": 0.6, "n_rol": 80, "wr_rol": 0.55, "v": 3, "n": 4, "oro14": 22, "frase": "Sylas va 3-1.", "pocas": True},
         "cuidado": {"rival": "Ahri", "v": 7, "n": 10, "wr": 0.7, "ic": [0.4, 0.9], "oro14": 293, "cs14": 3.2, "xp14": 1, "nivel6": -0.1,
                     "muertes6": 0.5, "ref": {"oro14": -118, "cs14": -3, "nivel6": 0, "muertes6": 0.6}, "notas": [], "pocas": False, "anticipa": ["muertes6"]},
         "reglas": [{"texto": "69+ minions al 10.", "numero": "74%", "n": 90, "pista": False}],
         "counters": {"lista": [{"rival": "Viktor", "v": 1, "n": 3, "ic": [0.06, 0.79], "cs14": -28, "oro14": -570, "pocas": True}], "ref": {"cs14": -7, "oro14": -273}}}
RECS = [("Ahri", {"nombre": "Ahri", "conocido": True, "vs": [{"win": True}, {"win": False}], "en": [{}], "filas": [{"champ": "Sylas", "est": 0.6, "vd": "3-1"}],
                  "avisos": [], "build_dict": None, "ficha": FICHA})]


class Estado(unittest.TestCase):
    def setUp(self): self.viejo = dict(w.ESTADO)
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def test_draft_sin_partidas_y_con_lineas(self):
        w.evento(("fase", "ChampSelect")); w.evento(("draft", "MIDDLE", RECS))
        s = json.loads(w.estado())
        r = s["draft"]["recs"][0]
        self.assertNotIn("vs", r); self.assertNotIn("en", r)
        self.assertEqual((r["v"], r["n"]), (1, 2))
        self.assertTrue(any("tiende a repetirse" in l for l in r["lineas"]["cuidado"]))
        self.assertEqual(s["fase"], "ChampSelect")

    def test_rival_desconocido_y_version_sube(self):
        v = w.ESTADO["v"]; w.evento(("draft", "MIDDLE", [("Zed", None)]))
        self.assertEqual(w.ESTADO["draft"]["recs"][0], {"rival": "Zed", "conocido": False}); self.assertEqual(w.ESTADO["v"], v + 1)

    def test_champselect_borra_lo_anterior(self):
        w.evento(("aviso", {"texto": "x", "tipo": "consejo", "minuto": 5})); w.evento(("draft", "MIDDLE", RECS)); w.evento(("fase", "ChampSelect"))
        self.assertIsNone(w.ESTADO["draft"]); w.evento(("fase", "Lobby")); self.assertIsNone(w.ESTADO["aviso"])


    def test_demo_recorre_las_fases(self):
        q = []
        with mock.patch.object(w.gui, "recomendaciones", return_value=RECS), mock.patch.object(w.time, "sleep"), \
             mock.patch.object(w.companion, "minions10", return_value=None):
            w.demo(type("Q", (), {"put": lambda _, e: q.append(e)})())
        self.assertEqual([e[1] for e in q if e[0] == "fase"], ["ChampSelect", "InProgress", "EndOfGame"])
        for e in q: w.evento(e)
        s = json.loads(w.estado())
        self.assertEqual(s["fase"], "EndOfGame"); self.assertIn("kda", s["fin"]); self.assertIn("muertes14_25", s["fin"]); self.assertIn("nivel_rival", s["meta"])
        self.assertIn("dragon", s["meta"]["objetivos"])  # el demo trae el panel En vivo (Tu rival / Objetivos)

    def test_minions10_incompleto_es_none(self):
        for cfg in ('{"minions10": {"campeon": "Sylas"}}', '{"minions10": {"minimo": 69}}'):
            with mock.patch.object(w.companion, "CFG") as f:
                f.exists.return_value = True; f.read_text.return_value = cfg
                self.assertIsNone(w.companion.minions10())


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()

    def get(self, path, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("GET", path, headers={"Host": host} if host else {}); r = c.getresponse(); return r.status, r.read()

    def test_pagina_y_estado(self):
        st, b = self.get("/"); self.assertEqual(st, 200); self.assertIn(b"/api/estado", b); self.assertIn("Tu plan con".encode(), b)
        for t in ("Tu rival", "Objetivos", "desde el 20:00"): self.assertIn(t.encode(), b)
        st, b = self.get("/api/estado"); self.assertEqual(st, 200); self.assertIn("fase", json.loads(b))

    def test_vigilar_cuenta_avisa_solo_al_cambiar(self):
        import queue
        c, q, n = w.companion, queue.Queue(), iter(range(6))
        cuentas = ["Uno", "Uno", None, "Dos"]
        def lcu(path):
            if path == "/lol-summoner/v1/current-summoner":
                i = next(n)
                if i >= len(cuentas): raise KeyboardInterrupt
                return {"gameName": cuentas[i], "tagLine": "LAN"} if cuentas[i] else None
            return None
        orig, c.lcu, ts = c.lcu, lcu, w.time.sleep
        w.time.sleep = lambda s: None
        try:  # sin hilos reales: seguirían vivos tras la prueba con el cliente de verdad y bajarían partidas al repo
            with self.assertRaises(KeyboardInterrupt), mock.patch.object(w, "primera_vez"), mock.patch.object(w, "al_dia"): w.vigilar_cuenta(q)
        finally: c.lcu, w.time.sleep = orig, ts
        self.assertEqual([e[1] for e in list(q.queue) if e[0] == "cuenta"], ["Uno#LAN", "Dos#LAN"])

    def test_fuentes_locales(self):  # Mulish/Inter empaquetadas: la CSP las deja cargar solo del mismo origen
        st, b = self.get("/fonts/mulish.woff2"); self.assertEqual((st, b[:4]), (200, b"wOF2"))
        self.assertEqual(self.get("/fonts/otra.woff2")[0], 404)

    def test_crono_de_champ_select(self):  # Draft_Vino: reloj de la fase, leído del cliente (solo lectura)
        w.evento(("crono", {"fase": "BAN_PICK", "ms": 28000, "t": 1.0}))
        self.assertEqual(w.ESTADO["crono"]["ms"], 28000)
        self.assertIn("FASE_CS", self.get("/")[1].decode())

    def test_version_nueva(self):
        self.assertTrue(w.version_mayor("v0.6.1", "0.6.0")); self.assertTrue(w.version_mayor("v1.0.0", "0.9.9"))
        self.assertFalse(w.version_mayor("v0.6.0", "0.6.0")); self.assertFalse(w.version_mayor("beta", "0.6.0"))
        class R(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass
        datos = json.dumps({"tag_name": "v99.0.0", "html_url": "https://github.com/C0z1/racha.gg/releases/tag/v99.0.0"}).encode()
        with mock.patch.object(w.urllib.request, "urlopen", return_value=R(datos)):
            w.buscar_version()
        self.assertEqual(w.ESTADO["nueva"]["version"], "v99.0.0"); w.ESTADO["nueva"] = None
        malo = json.dumps({"tag_name": "v99.0.0", "html_url": "https://evil.example/x"}).encode()
        with mock.patch.object(w.urllib.request, "urlopen", return_value=R(malo)):
            w.buscar_version()
        self.assertIsNone(w.ESTADO["nueva"])  # solo enlaces de GitHub

    def test_primera_vez_hasta_tener_el_historial_completo(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"DATOS_DIR": d}),                 mock.patch.object(w, "descargar_todo") as dt, mock.patch.object(w.gui, "puede_descargar", return_value=True),                 mock.patch.object(w.companion, "lcu", return_value={"gameName": "Amigo"}):  # con el cliente abierto
            w.primera_vez(); self.assertEqual(dt.call_count, 1)
            pathlib.Path(d, "LA1_1.json").write_text("{}"); w.primera_vez(); self.assertEqual(dt.call_count, 2)  # con partidas, sin el historial entero
            pathlib.Path(d, "historial.json").write_text("{}"); w.primera_vez(); self.assertEqual(dt.call_count, 2)  # completo: lo nuevo llega por al_dia
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"DATOS_DIR": d}), mock.patch.object(w, "descargar_todo") as dt,              mock.patch.object(w.companion, "lcu", return_value=None):  # cliente cerrado: se reintenta al abrir LoL
            w.primera_vez(); dt.assert_not_called()

    def test_vistas_previas(self):  # Selección y En vivo no quedan vacías fuera del champ select y de la partida
        import tempfile
        foto = (pathlib.Path(w.__file__).parent / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8")
        r = {"vistas": {"pos": "MIDDLE", "draft": {"MIDDLE": {"frecuentes": [{"rival": "Zed"}]}}}}
        with tempfile.TemporaryDirectory() as d, mock.patch.object(w.companion, "VIVO", pathlib.Path(d)), \
                mock.patch.object(w.gui, "recomendaciones", return_value=[("Zed", None)]) as rec:
            pathlib.Path(d, "20261110-1.jsonl").write_text(json.dumps(json.loads(foto)) + "\n", encoding="utf-8")
            w.vistas_previas(r)
        rec.assert_called_once_with("MIDDLE", ["Zed"])
        self.assertTrue(w.ESTADO["previa"]["previa"]); self.assertEqual(w.ESTADO["ultima"]["campeon"], "Ekko")
        w.vistas_previas({})  # sin vistas ni fotos: nada, sin tronar
        w.ESTADO.update(previa=None, ultima=None)

    def test_api_abrir(self):  # un segundo arranque pide la ventana: solo con X-HTC; /api/ventana (barra propia) ya no existe
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("POST", "/api/abrir", body=b"{}", headers={"Content-Type": "application/json", "Content-Length": "2"})
        self.assertEqual(c.getresponse().status, 403)
        with mock.patch.object(w, "abrir") as a:
            c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
            c.request("POST", "/api/abrir", body=b"{}", headers={"X-HTC": "1", "Content-Type": "application/json", "Content-Length": "2"})
            self.assertEqual(c.getresponse().status, 200); a.assert_called_once()
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("POST", "/api/ventana", body=b'{"accion":"cerrar"}', headers={"X-HTC": "1", "Content-Type": "application/json", "Content-Length": "19"})
        self.assertNotEqual(c.getresponse().status, 200)

    def test_api_actualizar(self):  # botón «Actualizar» de arriba a la derecha (2026-11-13)
        with mock.patch.object(w, "buscar_version") as b:
            c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
            c.request("POST", "/api/actualizar", body=b"{}", headers={"X-HTC": "1", "Content-Type": "application/json", "Content-Length": "2"})
            self.assertEqual(c.getresponse().status, 200); time.sleep(.2); b.assert_called_once()
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("POST", "/api/actualizar", body=b"{}", headers={"Content-Type": "application/json", "Content-Length": "2"})
        self.assertEqual(c.getresponse().status, 403)

    def test_al_dia_y_una_sola_a_la_vez(self):
        with mock.patch.object(w, "_buscar_version"): w.ESTADO["nueva"] = None; w.buscar_version()
        self.assertIsNone(w.ESTADO["nueva"]); self.assertIsNotNone(w.ESTADO["al_dia"])
        with w.ACTUALIZANDO, mock.patch.object(w, "_buscar_version") as b: w.buscar_version(); b.assert_not_called()

    def test_icono(self):
        st, b = self.get("/icono.png"); self.assertEqual(st, 200); self.assertEqual(b[1:4], b"PNG")
        self.assertIn(b'href="/icono.png"', self.get("/")[1])

    def test_perfil_como_el_canvas(self):  # Perfil_Vino + acuerdo 21: anillos con referencia, tilt hoy, cuenta y campeones a la derecha
        t = self.get("/")[1].decode()
        for f in ("function aro(", "Tus campeones ahora", "Tilt hoy", "Win rate de temporada", "function cuentaCab(", 'vista === "perfil" ? perfil(s)'):
            self.assertIn(f, t)

    def test_iconos_y_filas_nuevas(self):  # pedido del usuario: íconos por métrica, sin emoji, y filas con tu dato
        st, b = self.get("/"); t = b.decode()
        for k in ("nivel", "cs", "muertes", "kp", "vision", "oro", "dano", "objetivos", "linea", "tilt", "champselect", "perfil"):
            self.assertRegex(t, rf"\n  {k}: '<")
        for f in ("Tu plan con", "Cumples", "Hasta el nivel 6", "Si te toca contra", "típico", 'aria-hidden="true"', 'role="img"'):
            self.assertIn(f, t)
        for f in ("Cómo jugarlo", "La sueles cumplir", 'class="div"', "Counters de tu"):  # pedido del usuario: fuera lo viejo
            self.assertNotIn(f, t)
        self.assertNotRegex(t, "[\U0001F300-\U0001FAFF]")  # nada de emoji

    def test_vista_partidas(self):
        st, b = self.get("/"); t = b.decode()
        for f in ('id="b-partidas"', "\n  partidas: '<", "function partidas(s)", "Tus partidas", '"partidas", "campeones"'):
            self.assertIn(f, t)

    def test_integracion_de_vistas(self):  # auditoría turno 9 it. 6: Selección en partida, En vivo con cliente, error de vista visible
        st, b = self.get("/"); t = b.decode()
        self.assertIn('vista === "companion" && !s.draft ? (s.previa ? champSelect({...s, draft: s.previa}) : draftV(s))', t)  # Selección ya no cae en Draft; self.assertIn("s.draft ? champSelect(s)", t)
        self.assertNotIn('s.fase === "ChampSelect" && s.draft ? champSelect', t)
        for f in ("Aún no estás en partida", "Esta vista falló", "console.error(e)"): self.assertIn(f, t)
        # pantalla de carga, reconexión y espera de stats también son «en partida» (turno 9 it. 7)
        for f in ('"GameStart"', '"Reconnect"', '"WaitingForStats"', "EN_PARTIDA.includes(s.fase)"): self.assertIn(f, t)
        self.assertNotIn("FASES_CLIENTE", t)

    def test_csp_no_deja_cargar_de_fuera(self):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5); c.request("GET", "/")
        self.assertIn("default-src 'none'", c.getresponse().getheader("Content-Security-Policy"))

    def test_host_ajeno_403(self):
        self.assertEqual(self.get("/api/estado", host="evil.example")[0], 403)

    def test_imagen_valida_el_nombre(self):
        with mock.patch.object(w, "imagen", return_value=b"PNG") as im:
            self.assertEqual(self.get("/img/champion/Ahri.png"), (200, b"PNG")); im.assert_called_with("champion", "Ahri")
            self.assertEqual(self.get("/img/champion/..%2F..%2Fx.png")[0], 404)
            self.assertEqual(self.get("/img/otra/Ahri.png")[0], 404)
            self.assertEqual(im.call_count, 1)

    def test_imagen_nunu_por_prefijo(self):
        import builds, tempfile, pathlib
        d = {"nunu": ("Nunu", 20, "Tank"), "vi": ("Vi", 254, "Fighter"), "viego": ("Viego", 234, "Fighter")}
        with tempfile.TemporaryDirectory() as t, mock.patch.object(builds, "ddragon", return_value=({}, {}, d)), mock.patch.object(w, "IMG", pathlib.Path(t)):
            for f in ("Nunu", "Viego"): (pathlib.Path(t) / "champion").mkdir(exist_ok=True); (pathlib.Path(t) / "champion" / f"{f}.png").write_bytes(f.encode())
            self.assertEqual(w.imagen("champion", "NunuWillump"), b"Nunu")
            self.assertEqual(w.imagen("champion", "Viego"), b"Viego")  # exacto gana al prefijo «vi»
            self.assertIsNone(w.imagen("champion", "Zzz"))


class CacheRendimiento(unittest.TestCase):
    def test_usa_cache_y_la_invalida_al_cambiar_partidas(self):
        import pathlib, tempfile
        with tempfile.TemporaryDirectory() as d:
            raw, cache = pathlib.Path(d, "raw"), pathlib.Path(d, "c.json"); raw.mkdir()
            (raw / "LA1_1.json").write_text("{}")
            with mock.patch.object(w, "rendimiento", return_value={"x": 1}) as r:
                self.assertEqual(w.rendimiento_rapido(raw, cache), {"x": 1})
                self.assertEqual(w.rendimiento_rapido(raw, cache), {"x": 1})
                self.assertEqual(r.call_count, 1)  # la segunda sale de la caché
                (raw / "LA1_2.json").write_text("{}")
                w.rendimiento_rapido(raw, cache)
                self.assertEqual(r.call_count, 2)  # partida nueva: se recalcula


class RapidoSinRaw(unittest.TestCase):
    def test_sin_raw_pide_rendimiento_con_none(self):  # con la ruta resuelta, rendimiento() no agregaba las vistas
        import pathlib, tempfile
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(w, "rendimiento", return_value={"x": 1}) as r, mock.patch.dict("os.environ", {"DATOS_DIR": d}):
                w.rendimiento_rapido(None, pathlib.Path(d, "c.json"))
            r.assert_called_once_with(None)


class Fondo(unittest.TestCase):
    def setUp(self): self.prev = (dict(w.ESTADO), w.FONDO[0], w.VIVO[0]); w.URL[0] = "http://127.0.0.1:1/"
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.prev[0]); w.FONDO[0], w.VIVO[0] = self.prev[1], self.prev[2]

    def test_abre_la_ventana_al_abrir_el_cliente(self):
        import time
        w.FONDO[0], w.VIVO[0] = True, time.time() - 60
        with mock.patch.object(w, "abrir") as a, mock.patch.object(w.gui, "perfil", return_value="x"):
            w.evento(("fase", None)); a.assert_not_called()          # cliente cerrado: nada
            w.evento(("fase", "Lobby")); a.assert_called_once()      # se abrió el cliente: abre HTC
            w.evento(("fase", "Matchmaking")); a.assert_called_once()  # ya abierto: no repite

    def test_no_abre_si_la_ventana_ya_esta_o_sin_fondo(self):
        import time
        with mock.patch.object(w, "abrir") as a, mock.patch.object(w.gui, "perfil", return_value="x"):
            w.FONDO[0], w.VIVO[0] = True, time.time(); w.ESTADO["fase"] = None
            w.evento(("fase", "Lobby")); a.assert_not_called()       # la ventana sigue preguntando
            w.FONDO[0], w.VIVO[0] = False, 0; w.ESTADO["fase"] = None
            w.evento(("fase", "Lobby")); a.assert_not_called()       # sin --fondo nunca abre sola

    def test_fondo_con_el_cliente_ya_abierto_abre_la_ventana(self):
        # bug real: arrancar --fondo con LoL abierto no abría nada (la primera fase llegaba en < 6 s del arranque)
        import tempfile
        class Fin(Exception): pass
        with tempfile.TemporaryDirectory() as d, mock.patch.object(w, "otro_htc", return_value=None), \
                mock.patch.object(w, "PUERTO", pathlib.Path(d) / "htc.port"), mock.patch.object(w, "autoarranque"), \
                mock.patch.object(w, "refrescar"), mock.patch.object(w.gui, "trabajador"), \
                mock.patch.object(w.time, "sleep", side_effect=Fin), mock.patch.object(w, "abrir") as a, \
                mock.patch.object(w.gui, "perfil", return_value="x"), mock.patch.object(w, "vigilar_cuenta"),                 mock.patch.object(w, "buscar_version"), mock.patch.object(w, "primera_vez"):
            with self.assertRaises(Fin): w.main(["--fondo", "--sin-overlay"])
            a.assert_not_called()                                      # --fondo no abre al arrancar...
            w.ESTADO["fase"] = "inicio"; w.evento(("fase", "Lobby")); a.assert_called_once()  # ...sino con la primera fase


class Post(unittest.TestCase):
    def setUp(self):
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H); threading.Thread(target=self.srv.serve_forever, daemon=True).start()
    def tearDown(self): self.srv.shutdown(); self.srv.server_close()
    def post(self, cab, cuerpo=b'{"on": true}'):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port); c.request("POST", "/api/autoarranque", cuerpo, cab)
        r = c.getresponse(); return r.status

    def test_sin_cabecera_htc_403(self):  # una web ajena no puede activar el arranque con Windows
        with mock.patch.object(w, "autoarranque") as a:
            self.assertEqual(self.post({"Content-Type": "application/json"}), 403); a.assert_not_called()

    def test_con_cabecera_llama_y_valida(self):
        with mock.patch.object(w, "autoarranque", return_value=True) as a:
            self.assertEqual(self.post({"X-HTC": "1"}), 200); a.assert_called_once_with(True)
            self.assertEqual(self.post({"X-HTC": "1"}, b'{"on": "si"}'), 400)



class MiPick(unittest.TestCase):
    """Al fijar tu campeón: Racha al frente (sin foco) con sus runas; hover, ARAM o solo el rival no la traen."""
    B = {"runa": ["Ritmo letal", .55], "pagina_ids": [8008], "fuente": "tu"}

    def tab(self, draft=True, **yo): return {"draft": draft, "mio": [{"yo": False, "fijo": True, "campeon": "Zed", "pos": "MIDDLE"}, {"yo": True, "pos": "BOTTOM", **yo}]}

    def setUp(self):
        for p in (mock.patch("builds.guardado_dict", return_value=self.B), mock.patch.dict(w.ESTADO, mi_pick=None, tablero=None, draft=None),
                  mock.patch.object(w.companion, "runas_recomendadas", return_value=None)):  # sin cliente: nada de la página de Riot
            p.start(); self.addCleanup(p.stop)
        self.ab = mock.patch.object(w, "abrir").start(); self.addCleanup(mock.patch.stopall)

    def abiertas(self): time.sleep(.1); return self.ab.call_count

    def test_hover_tarjeta_sin_ventana(self):  # en hover ya puedes poner sus runas; la ventana no salta
        w.evento(("tablero", self.tab(fijo=False, campeon="Zeri")))
        self.assertEqual((w.ESTADO["mi_pick"]["champ"], w.ESTADO["mi_pick"]["fijo"]), ("Zeri", False))
        w.evento(("tablero", self.tab(fijo=False, campeon="Jinx"))); self.assertEqual(w.ESTADO["mi_pick"]["champ"], "Jinx")
        w.evento(("tablero", self.tab(fijo=False, campeon=None))); self.assertIsNone(w.ESTADO["mi_pick"])  # intent vacío
        self.assertEqual(self.abiertas(), 0)

    def test_hover_luego_fijo_una_vez_sin_foco(self):
        w.evento(("tablero", self.tab(fijo=False, campeon="Zeri"))); self.assertEqual(self.abiertas(), 0)
        w.evento(("tablero", self.tab(fijo=True, campeon="Zeri")))
        self.assertEqual((w.ESTADO["mi_pick"]["champ"], w.ESTADO["mi_pick"]["pos"], w.ESTADO["mi_pick"]["build"]), ("Zeri", "BOTTOM", self.B))
        w.evento(("tablero", self.tab(fijo=True, campeon="Zeri")))
        self.assertEqual(self.abiertas(), 1); self.assertEqual(self.ab.call_args[0][1], False)  # sin robar el foco

    def test_aram_no_dispara(self):
        w.evento(("tablero", self.tab(draft=False, fijo=True, campeon="Zeri")))
        self.assertIsNone(w.ESTADO["mi_pick"]); self.assertEqual(self.abiertas(), 0)

    def test_trade_actualiza(self):
        w.evento(("tablero", self.tab(fijo=True, campeon="Zeri"))); w.evento(("tablero", self.tab(fijo=True, campeon="Jinx")))
        self.assertEqual(w.ESTADO["mi_pick"]["champ"], "Jinx"); self.assertEqual(self.abiertas(), 2)

    def test_sin_build_no_trae_ventana(self):
        with mock.patch("builds.guardado_dict", return_value=None):
            w.evento(("tablero", self.tab(fijo=True, campeon="Zeri")))
        self.assertEqual(w.ESTADO["mi_pick"]["champ"], "Zeri"); self.assertEqual(self.abiertas(), 0)

    def test_rival_trae_matchup_sin_reabrir(self):
        w.evento(("tablero", self.tab(fijo=True, campeon="Zeri")))
        mu = {"runa": {"nombre": "Cadencia letal", "wr": .54, "n": 160}, "n": 420, "pagina": {"x": 1}}
        with mock.patch("matchups.para_ficha", return_value=mu), mock.patch.object(w, "draft_json", return_value={"pos": "BOTTOM", "recs": [{"rival": "MissFortune"}]}):
            w.evento(("draft", "BOTTOM", []))
        self.assertEqual(w.ESTADO["mi_pick"]["rival"], "MissFortune"); self.assertEqual(w.ESTADO["mi_pick"]["matchup"]["n"], 420)
        self.assertEqual(self.abiertas(), 1)



class Lobby(unittest.TestCase):
    """Los 10 de la partida: tu equipo primero, sin bots ni puuid en la página, rango fila a fila."""
    G = {"participants": [{"puuid": "yo" * 20, "teamId": 100, "championId": 222, "riotId": "Yo#1", "perks": {"perkIds": [8008]}},
                          {"puuid": "b" * 40, "teamId": 200, "championId": 21, "riotId": "Rival#2", "perks": {"perkIds": [8021]}},
                          {"puuid": "c" * 40, "teamId": 100, "championId": 1, "bot": True},
                          {"puuid": "d" * 40, "teamId": 200, "championId": 1, "riotId": "Otro#3"}]}

    def test_puro(self):
        js = w.companion.lobby(self.G, "yo" * 20, {222: "Jinx", 21: "MissFortune"}, {8008: "Ritmo letal"})
        self.assertEqual([(j["equipo"], j["yo"], j["campeon"], j["runa"]) for j in js],
                         [("mio", True, "Jinx", "Ritmo letal"), ("suyo", False, "MissFortune", None), ("suyo", False, None, None)])
        self.assertIsNone(w.companion.lobby({"participants": []}, "x", {}, {}))
        self.assertIsNone(w.companion.lobby(self.G, "otro" * 10, {}, {}))  # no estás en esa partida

    def test_armar(self):
        r = {"tier": "GOLD", "division": "II", "lp": 40, "wins": 6, "losses": 4, "n": 10, "wr": 60}
        with mock.patch.dict(w.ESTADO, fase="InProgress", plataforma="la1", lobby=None),              mock.patch.object(w.companion, "lcu", return_value={"puuid": "yo" * 20}), mock.patch.object(w.companion, "nombres_lcu", return_value={}),              mock.patch.object(w.companion, "backend", return_value=self.G) as be, mock.patch.object(w, "rango_api", side_effect=[r, None, None]):
            w.armar_lobby(intentos=1)
            L = w.ESTADO["lobby"]
        self.assertEqual(len(L), 3); self.assertEqual(L[0]["rango"], r); self.assertIsNone(L[1]["rango"])
        self.assertFalse(any("puuid" in j for j in L)); self.assertIn("/lol/spectator/v5/active-games/by-summoner/", be.call_args[0][1])

    def test_sin_partida_reintenta_y_se_rinde(self):
        import urllib.error
        e = urllib.error.HTTPError("u", 404, "no", {}, None)
        with mock.patch.dict(w.ESTADO, fase="InProgress", plataforma="la1", lobby=None), mock.patch.object(w.companion, "lcu", return_value={"puuid": "yo" * 20}),              mock.patch.object(w.companion, "nombres_lcu", return_value={}), mock.patch.object(w.companion, "backend", side_effect=e) as be:
            w.armar_lobby(intentos=2, espera=0)
            self.assertIsNone(w.ESTADO["lobby"]); self.assertEqual(be.call_count, 2)



class RunasRiot(unittest.TestCase):
    """Sin build guardada: la página recomendada del cliente (9 ids con fragmentos); forma rara = None."""
    PAG = [{"perks": [{"id": i} for i in (8010, 8009, 9105, 8014, 8451, 8444, 5008, 5008, 5001)], "primaryPerkStyleId": 8000, "secondaryPerkStyleId": 8400}]

    def test_recomendadas(self):
        rutas = []
        r = w.companion.runas_recomendadas(84, "MIDDLE", leer=lambda u: rutas.append(u) or self.PAG)
        self.assertEqual(r["keystone"], 8010); self.assertEqual(r["pagina_ids"]["subStyleId"], 8400)
        self.assertTrue(rutas[0].endswith("/champion/84/position/middle/map/11"))
        for malo in (None, [], [{"perks": [{"id": 1}]}], {"error": 1}, [{"perks": [{"id": "x"}] * 9, "primaryPerkStyleId": 8000, "secondaryPerkStyleId": 8400}]):
            self.assertIsNone(w.companion.runas_recomendadas(84, "MIDDLE", leer=lambda u: malo))

    def test_build_para(self):
        dd = ({}, {8010: "Conquistador"}, {"akali": ("Akali", 84, "Assassin")})
        with mock.patch("builds.guardado_dict", return_value=None), mock.patch("builds.ddragon", return_value=dd),              mock.patch.object(w.companion, "lcu", return_value=self.PAG) as l:
            b = w.build_para("Akali", "MIDDLE")
        self.assertEqual((b["fuente"], b["runa"]), ("riot", ["Conquistador", None])); self.assertEqual(len(b["pagina_ids"]["selectedPerkIds"]), 9)
        with mock.patch("builds.guardado_dict", return_value={"fuente": "tu"}), mock.patch.object(w.companion, "lcu") as l:
            self.assertEqual(w.build_para("Akali", "MIDDLE"), {"fuente": "tu"}); l.assert_not_called()  # la guardada manda


if __name__ == "__main__":
    unittest.main()
