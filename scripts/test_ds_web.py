"""Pruebas de companion_web.py (Turno 7): el servidor local escucha solo en 127.0.0.1 y sirve
el estado de la página sin red ni ventanas. No toca el cliente de LoL ni descarga imágenes."""
import http.server, json, queue, threading, unittest, urllib.error, urllib.request
from pathlib import Path
from unittest import mock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import companion_web as web  # noqa: E402


class Servidor:
    def __init__(self):
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), web.H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def get(self, path, host=None):
        req = urllib.request.Request(self.url + path, headers={} if host is None else {"Host": host})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.headers.get("Content-Type"), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type"), b""

    def stop(self):
        self.srv.shutdown()


class TestServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor()

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()

    def test_escucha_solo_loopback(self):
        self.assertEqual(self.s.srv.server_address[0], "127.0.0.1")

    def test_index_html(self):
        code, tipo, cuerpo = self.s.get("/")
        self.assertEqual(code, 200)
        self.assertIn("text/html", tipo)
        self.assertIn(b"HTC", cuerpo)

    def test_pie_wr_al_95_sin_el_viejo_11(self):
        code, _, cuerpo = self.s.get("/")
        self.assertEqual(code, 200)
        self.assertIn(b"(95%)", cuerpo)
        self.assertNotIn(b"\xc2\xb111", cuerpo)  # «±11» (1 SE) ya no debe aparecer

    def test_sin_partidas_etiqueta_presente(self):
        _, _, cuerpo = self.s.get("/")
        self.assertIn("Sin partidas".encode(), cuerpo)

    def test_sin_partidas_todavia_en_que_esta_fallando(self):
        _, _, cuerpo = self.s.get("/")
        self.assertIn("Sin partidas todavía.".encode("utf-8"), cuerpo)

    def test_estado_es_json(self):
        code, tipo, cuerpo = self.s.get("/api/estado")
        self.assertEqual(code, 200)
        self.assertIn("application/json", tipo)
        d = json.loads(cuerpo)
        for k in ("fase", "draft", "meta", "fin", "revision", "rango", "aviso", "v"):
            self.assertIn(k, d)

    def test_host_local_sirve(self):
        for host in ("127.0.0.1", "localhost", "localhost:9999", "127.0.0.1:1"):
            code, _, _ = self.s.get("/api/estado", host=host)
            self.assertEqual(code, 200, host)

    def test_host_ajeno_403(self):
        code, _, _ = self.s.get("/api/estado", host="malo.ejemplo")
        self.assertEqual(code, 403)

    def test_ruta_desconocida_404(self):
        code, _, _ = self.s.get("/no-existe")
        self.assertEqual(code, 404)

    def test_imagen_nombre_muy_largo_404(self):
        code, _, _ = self.s.get("/img/champion/" + "a" * 41 + ".png")
        self.assertEqual(code, 404)

    def test_boton_partidas_con_aria_label(self):  # iter 15 (b): el nav trae la vista Partidas etiquetada
        _, _, cuerpo = self.s.get("/")
        self.assertIn(b'id="b-partidas" aria-label="Tus partidas"', cuerpo)

    def test_inicio_es_la_vista_por_defecto(self):  # turno 8: la casa es el botón activo y el fallback fuera de partida
        _, _, cuerpo = self.s.get("/")
        self.assertIn(b'id="b-inicio" aria-label="Inicio" aria-current="page"', cuerpo)
        self.assertIn(b'vista === "inicio" ? inicio(s)', cuerpo)
        self.assertIn(b': "inicio"', cuerpo)  # la fase por defecto (fuera de champ select/partida) cae en Inicio

    def test_seleccion_sin_cosas_viejas(self):  # turno 9 (c): fuera «Cómo jugarlo», la barra divergente y los counters viejos
        _, _, cuerpo = self.s.get("/")
        for viejo in ("Cómo jugarlo", 'class="div"', "La sueles cumplir", "Counters de tu"):
            self.assertNotIn(viejo.encode("utf-8"), cuerpo)

    def test_plan_sin_tu_al_final_y_sin_dato_tuyo(self):  # turno 9 (a): reglas sin dato van al final con «sin dato tuyo»
        _, _, cuerpo = self.s.get("/")
        self.assertIn(b"(a.n ? a.ok / a.n : 2)", cuerpo)  # 2 = centinela que manda «sin dato» al final (ok/n en 0..1)
        self.assertIn(b"n: r.tu ? r.tu.n : 0", cuerpo)
        self.assertIn("sin dato tuyo".encode("utf-8"), cuerpo)

    def test_fallo_unidades_vacio_y_componente_desconocido(self):  # turno 9 (b): sin unidades cae a «contra tu rol» con z
        _, _, cuerpo = self.s.get("/")
        self.assertIn("contra tu rol".encode("utf-8"), cuerpo)
        self.assertIn(b"signo(z, 2)", cuerpo)                      # sin unidades: muestra la desviación z
        self.assertIn(b'COMP[c] || [c, "alerta", v => v, "", ""]', cuerpo)  # componente fuera de COMP no truena
        self.assertIn(b"DEC[c] ?? 1", cuerpo)

    def test_fallo_muertes_signo_alineado(self):  # turno 9 iter 4 (b): el número de Muertes lleva el signo de la flecha
        _, _, cuerpo = self.s.get("/")
        self.assertIn(b'(c === "muertes" ? -1 : 1)', cuerpo)  # menos es mejor: se niega para seguir a ▼/▲
        self.assertIn(b"muertes: 1", cuerpo)                  # 1 decimal → «−2.0» y no «−2»
        self.assertIn(b'v < 0 ? "\xe2\x88\x92"', cuerpo)      # signo usa el menos unario − (U+2212)


class TestEstado(unittest.TestCase):
    def test_evento_fase_resetea_draft(self):
        web.ESTADO.update(fase="inicio", draft={"recs": []}, fin={"texto": "x"}, v=0)
        web.evento(("fase", "ChampSelect"))
        self.assertEqual(web.ESTADO["fase"], "ChampSelect")
        self.assertIsNone(web.ESTADO["draft"])
        self.assertIsNone(web.ESTADO["fin"])
        self.assertIsNone(web.ESTADO["meta"])

    def test_draft_json_quita_partidas_y_cuenta(self):
        ficha = {"cuidado": {"rival": "Zed", "n": 0, "v": 0, "ic": [0.0, 0.0], "notas": [], "ref": {}},
                 "counters": {"lista": [], "ref": {}}}
        recs = [("Zed", {"vs": [{"win": True}, {"win": False}], "en": [1, 2],
                         "filas": [{"champ": "Yone", "est": 0.55, "vd": "3-1"}], "ficha": ficha})]
        d = web.draft_json("MIDDLE", recs)
        self.assertEqual(d["pos"], "MIDDLE")
        r = d["recs"][0]
        self.assertNotIn("vs", r)
        self.assertNotIn("en", r)
        self.assertEqual(r["v"], 1)
        self.assertEqual(r["n"], 2)
        self.assertEqual(r["lineas"], {"cuidado": [], "counters": []})

    def test_draft_json_ficha_none_no_truena(self):
        d = web.draft_json("MIDDLE", [("Zed", {"conocido": True, "vs": [], "en": [], "filas": [], "ficha": None})])
        self.assertEqual(d["recs"][0]["lineas"], {"cuidado": [], "counters": []})

    def test_evento_rango_none_conserva_el_anterior(self):
        r = {"tier": "DIAMOND", "division": "II", "lp": 30, "wins": 100, "losses": 100, "n": 200, "wr": 50}
        web.ESTADO["rango"] = r
        web.evento(("rango", None))
        self.assertIs(web.ESTADO["rango"], r)
        self.assertIn("Diamond II", web.ESTADO["perfil"])

    def test_evento_fin_muertes_none_serializable(self):
        web.evento(("fin", {"minuto": 12, "campeon": "Ekko", "kda": "1/0/2", "cs": 80,
                            "rival": "Zed", "cotejo": None, "muertes14_25": None}))
        d = json.loads(web.estado())
        self.assertIsNone(d["fin"]["muertes14_25"])
        self.assertIsInstance(d["fin"]["texto"], str)

    def test_minions10_vacio_o_json_roto_es_none(self):
        for cfg in ('{"minions10": []}', "{no es json"):
            with mock.patch.object(web.companion, "CFG") as f:
                f.exists.return_value = True
                f.read_text.return_value = cfg
                self.assertIsNone(web.companion.minions10(), cfg)

    def test_imagen_campeon_desconocido_sin_red(self):
        import builds
        with mock.patch.object(builds, "ddragon", return_value=({}, {}, {})):
            self.assertIsNone(web.imagen("champion", "NoExiste"))

    def test_imagen_prefijo_no_confunde_campeones(self):  # turno 9 iter 4 (a): el prefijo no cae en otro campeón
        import builds, pathlib, tempfile
        # claves como builds.ddragon()[2] en es_MX: norm(id) y norm(nombre es_MX) de cada campeón
        pares = [("Nunu", "Nunu y Willump"), ("Bard", "Bardo"), ("MasterYi", "Maestro Yi"),
                 ("MonkeyKing", "Wukong"), ("Renata", "Renata Glasc"), ("Vi", "Vi"),
                 ("Viego", "Viego"), ("Viktor", "Viktor"), ("DrMundo", "Dr. Mundo"),
                 ("JarvanIV", "Jarvan IV"), ("Belveth", "Bel'Veth"), ("KSante", "K'Sante")]
        d = {}
        for cid, nombre in pares:
            d[builds.norm(cid)] = (cid, 0, "Fighter")
            d[builds.norm(nombre)] = (cid, 0, "Fighter")
        casos = {"NunuWillump": "Nunu", "Nunu & Willump": "Nunu", "Nunu y Willump": "Nunu",
                 "Bard": "Bard", "Bardo": "Bard", "MasterYi": "MasterYi", "Maestro Yi": "MasterYi",
                 "Wukong": "MonkeyKing", "RenataGlasc": "Renata", "Renata Glasc": "Renata",
                 "Vi": "Vi", "Viego": "Viego", "Viktor": "Viktor", "DrMundo": "DrMundo",
                 "JarvanIV": "JarvanIV", "BelVeth": "Belveth", "KSante": "KSante", "Zzz": None}
        with tempfile.TemporaryDirectory() as t, mock.patch.object(builds, "ddragon", return_value=({}, {}, d)), \
             mock.patch.object(web, "IMG", pathlib.Path(t)):
            for cid, _ in pares:
                (pathlib.Path(t) / "champion").mkdir(exist_ok=True)
                (pathlib.Path(t) / "champion" / f"{cid}.png").write_bytes(cid.encode())
            for nombre, esperado in casos.items():
                self.assertEqual(web.imagen("champion", nombre), esperado.encode() if esperado else None, nombre)

    def test_demo_sin_foto_vivo_solo_champselect(self):
        q = queue.Queue()
        with mock.patch.object(web.gui, "REPO", Path("__no_repo__")), \
             mock.patch.object(web.companion, "nombres", return_value={}), \
             mock.patch.object(web.gui, "recomendaciones", return_value=[("Zed", {"ficha": None})]):
            web.demo(q)
        evs = [q.get() for _ in range(q.qsize())]
        self.assertEqual([e[0] for e in evs], ["fase", "draft"])

    def test_rendimiento_sin_account_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            Path(d, "perfil.json").write_text('{"sin": "account"}', encoding="utf-8")
            self.assertIsNone(web.rendimiento(raw=d))

    def test_refrescar_sube_v(self):
        fake = {"resumen": {"partidas": []}, "tilt": {"base": {"n": 0}}}
        before = web.ESTADO["v"]
        with mock.patch.object(web, "rendimiento_rapido", return_value=fake):
            web.refrescar()
        self.assertEqual(web.ESTADO["v"], before + 1)
        self.assertIs(web.ESTADO["rendimiento"], fake)
        web.ESTADO["rendimiento"] = None


if __name__ == "__main__":
    unittest.main()
