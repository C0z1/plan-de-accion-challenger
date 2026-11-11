"""v0.8 (todo gratis): métricas anónimas opt-in, reportes privados e invitar amigos desde la app, sin red."""
import hashlib, io, pathlib, tempfile, unittest, urllib.error
from unittest import mock

import companion_web as w


class V08(unittest.TestCase):
    def setUp(self): self.viejo = dict(w.ESTADO); w.PING[0] = None; w.USADO.clear()
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo); w.USADO.clear(); w.BAJADA[0] = 0

    def test_ping_solo_con_metricas_y_una_vez_al_dia(self):
        llamadas = []
        falso = lambda m, ruta, c=None, base=None: llamadas.append((ruta, c)) or {"ok": True}
        with mock.patch.object(w.companion, "backend", falso):
            with mock.patch.object(w.gui, "ajustes", lambda: {"metricas": False}): w.ping()
            self.assertEqual(llamadas, [])  # apagadas por defecto: no sale nada
            w.evento(("fase", "ChampSelect"))
            with mock.patch.object(w.gui, "ajustes", lambda: {"metricas": True}): w.ping(); w.ping()
        self.assertEqual(len(llamadas), 1)
        ruta, c = llamadas[0]
        self.assertEqual((ruta, c["champ_select"], c["revision"], c["version"]), ("/v1/ping", True, False, w.VERSION))
        self.assertEqual(set(c), {"version", "region", "overlay", "champ_select", "revision", "avisos", "sirvio_si", "sirvio_no", "sirvio_no_vi"})  # nada que identifique

    def test_reporte_ok_y_sin_red(self):
        w.ESTADO.update(fase="Lobby", descarga="falló (3)")
        enviado = {}
        with mock.patch.object(w.companion, "backend", lambda m, r, c=None, base=None: enviado.update(c) or {"ok": True}):
            w.reportar("no carga", "ajustes")
        self.assertIn("falló (3)", enviado["texto"]); self.assertEqual(enviado["fase"], "Lobby")
        self.assertIn("llegó", w.ESTADO["reporte"])
        def caido(*a, **k): raise urllib.error.URLError("x")
        with mock.patch.object(w.companion, "backend", caido): w.reportar("otra", "ajustes")
        self.assertIn("No se pudo", w.ESTADO["reporte"])
        def lleno(*a, **k): raise urllib.error.HTTPError("u", 429, "x", {}, None)
        with mock.patch.object(w.companion, "backend", lleno): w.reportar("otra", "ajustes")
        self.assertIn("varios reportes hoy", w.ESTADO["reporte"])

    def test_invitar_muestra_el_codigo_o_el_motivo(self):
        def falso(m, ruta, c=None, base=None):
            if m == "POST": return {"nombre": "carla", "email": None, "codigo": "abc123"}
            return [{"nombre": "carla"}]
        with mock.patch.object(w.companion, "backend", falso), mock.patch("builds.bajar", lambda: 0):
            w.invitar("Carla", "")
        self.assertEqual(w.ESTADO["invitacion"]["codigo"], "abc123"); self.assertEqual(w.ESTADO["admin"], [{"nombre": "carla"}])
        def prohibido(m, ruta, c=None, base=None): raise urllib.error.HTTPError(ruta, 403, "no", {}, None)
        with mock.patch.object(w.companion, "backend", prohibido), mock.patch("builds.bajar", lambda: 0):
            w.invitar("beto", "")
        self.assertIn("Solo quien administra", w.ESTADO["invitacion"]["error"]); self.assertIsNone(w.ESTADO["admin"])



class AutoActualizar(unittest.TestCase):  # v0.9: baja, verifica sha256 y solo instala fuera de partida
    def setUp(self): self.viejo = dict(w.ESTADO)
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)
    BIN = b"MZ instalador de prueba" * 100
    SHA = hashlib.sha256(BIN).hexdigest()

    def release(self, **cambio):
        a = {"name": "Racha-Setup-0.9.0.exe", "browser_download_url": w.DESCARGAS + "v0.9.0/Racha-Setup-0.9.0.exe", "digest": "sha256:" + self.SHA, **cambio}
        return {"tag_name": "v0.9.0", "html_url": "https://github.com/C0z1/racha.gg/releases/tag/v0.9.0", "assets": [a]}

    def test_instalador_de_exige_nombre_url_y_sha(self):
        self.assertEqual(w.instalador_de(self.release()), (w.DESCARGAS + "v0.9.0/Racha-Setup-0.9.0.exe", self.SHA))
        self.assertIsNone(w.instalador_de(self.release(digest=None)))
        self.assertIsNone(w.instalador_de(self.release(browser_download_url="https://evil.example/Racha-Setup-0.9.0.exe")))
        self.assertIsNone(w.instalador_de(self.release(name="otra-cosa.exe")))
        self.assertIsNone(w.instalador_de({}))

    def test_bajar_verificado(self):
        with tempfile.TemporaryDirectory() as t:
            destino = pathlib.Path(t) / "Racha-Setup.exe"
            with mock.patch.object(w.urllib.request, "urlopen", lambda req, timeout=None: io.BytesIO(self.BIN)):
                self.assertTrue(w.bajar_verificado("https://x.test/i.exe", self.SHA, destino))
                self.assertEqual(destino.read_bytes(), self.BIN)
                destino.unlink()
                self.assertFalse(w.bajar_verificado("https://x.test/i.exe", "0" * 64, destino))  # sha distinto: no queda nada que instalar
            self.assertEqual(list(pathlib.Path(t).iterdir()), [])

    def test_espera_a_que_termine_la_partida(self):
        corridas, fases = [], iter(["InProgress", "InProgress", "EndOfGame"])
        def dormir(_): w.ESTADO["fase"] = next(fases)
        w.ESTADO.update(fase="ChampSelect", nueva={"version": "v0.9.0"})
        with mock.patch.object(w, "bajar_verificado", lambda *a: True), mock.patch.object(w.time, "sleep", dormir),                 mock.patch.object(w.subprocess, "Popen", lambda args: corridas.append((w.ESTADO["fase"], args))):
            w.actualizar("v0.9.0", "u", self.SHA)
        self.assertEqual(corridas[0][0], "EndOfGame")
        self.assertIn("/VERYSILENT", corridas[0][1])

    def test_sha_malo_no_instala(self):
        w.ESTADO.update(fase="Lobby", nueva={"version": "v0.9.0"})
        with mock.patch.object(w, "bajar_verificado", lambda *a: False), mock.patch.object(w.subprocess, "Popen") as po:
            w.actualizar("v0.9.0", "u", self.SHA)
        po.assert_not_called(); self.assertIn("a mano", w.ESTADO["nueva"]["estado"])



class Restaurar(unittest.TestCase):  # login en una PC nueva: tus ajustes vuelven de la nube antes de la primera subida
    def test_pc_nueva_restaura_y_pc_con_ajustes_no_toca(self):
        import json, nube
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "ajustes.json"
            nube_aj = {"overlay": False, "metricas": True, "clave_vieja": True, "aviso_nivel": "si"}
            with mock.patch.object(nube.gui, "AJUSTES_F", f), mock.patch.object(nube, "pedir", return_value={"ajustes": nube_aj}):
                self.assertEqual(nube.restaurar("t"), 2)  # lo desconocido o raro no entra (lista blanca)
                a = json.loads(f.read_text(encoding="utf-8"))
                self.assertEqual((a["overlay"], a["metricas"], a["aviso_nivel"]), (False, True, True))
                self.assertEqual(nube.restaurar("t"), 0)  # ya hay ajustes en esta PC: mandan los locales
            with mock.patch.object(nube.gui, "AJUSTES_F", pathlib.Path(d) / "otro.json"), \
                    mock.patch.object(nube, "pedir", side_effect=urllib.error.URLError("x")):
                self.assertEqual(nube.restaurar("t"), 0)



class PickHoy(unittest.TestCase):  # idea 7: el estimado encogido manda, no el WR crudo
    def test_estimado_y_minimo(self):
        try: import vistas
        except Exception as e: self.skipTest(f"vistas necesita datos: {e}")
        def c(champ, v, n, pos="MIDDLE"):  # n partidas, v ganadas
            return [dict(champ=champ, pos=pos, win=i < v, t=i) for i in range(n)]
        gs = c("Ahri", 3, 3) + c("Yone", 28, 40) + c("Zed", 8, 10) + c("Garen", 45, 50, "TOP") + c("Yone", 0, 30, "TOP")
        h = vistas.pick_hoy(gs, "MIDDLE", .5)
        self.assertEqual((h["champ"], h["v"], h["n"]), ("Yone", 28, 40))  # 3-0 no llega al mínimo; Zed 8-2 encoge a 65 %, Yone 28-12 a 66 %; Garen y el Yone top no cuentan
        self.assertEqual(len(h["forma"]), 5)
        self.assertIsNone(vistas.pick_hoy(c("Ahri", 3, 3), "MIDDLE", .5))




class SemanaCompleta(unittest.TestCase):  # con solo las últimas 20 no se compara contra una semana a medias
    def test_cobertura(self):
        import semanal
        from datetime import date, datetime
        ms = lambda y, m, d: int(datetime(y, m, d, 12).timestamp() * 1000)
        g = lambda t, w=True: dict(t=t, win=w, campeon="Yone", rival="Zed")
        hoy = date(2026, 11, 11)  # miércoles; lunes 9, lunes anterior 2
        p = semanal.plan({"partidas": [g(ms(2026, 11, 10)), g(ms(2026, 11, 9))]}, hoy=hoy)
        self.assertEqual((p["completa"], p["wr_prev"], p["partidas"]), (False, None, 2))
        p = semanal.plan({"partidas": [g(ms(2026, 11, 10)), g(ms(2026, 11, 3), False), g(ms(2026, 10, 30))]}, hoy=hoy)
        self.assertEqual((p["completa"], p["wr_prev"]), (True, 0.0))




class SintaxisJS(unittest.TestCase):  # un salto de línea suelto en un texto rompe toda la página y ninguna otra prueba lo ve
    def test_index_html_parsea(self):
        import re, shutil, subprocess
        node = shutil.which("node")
        if not node: self.skipTest("sin node")
        html = (pathlib.Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")
        js = "\n".join(re.findall(r"<script>(.*?)</script>", html, re.S))
        self.assertTrue(js.strip())
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "pagina.js"; f.write_text(js, encoding="utf-8")
            r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])




class Grupo(unittest.TestCase):  # la tabla del grupo llega con la consulta horaria; sin red o sin acceso, nada
    def setUp(self): self.viejo = dict(w.ESTADO); w.BAJADA[0] = 0
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo); w.BAJADA[0] = 0

    def test_grupo_en_estado(self):
        fila = {"riot_id": "Ana#LAN", "yo": False, "semana": [1, 1], "ultimas": [3, 5], "score": 55}
        falso = lambda m, ruta, c=None, base=None: [fila] if ruta == "/v1/grupo" else []
        with mock.patch.object(w.companion, "backend", falso), mock.patch("builds.bajar", lambda: 0):
            w.builds_del_backend()
        self.assertEqual(w.ESTADO["grupo"], [fila])
        def caido(*a, **k): raise urllib.error.URLError("x")
        w.BAJADA[0] = 0
        with mock.patch.object(w.companion, "backend", caido), mock.patch("builds.bajar", lambda: 0):
            w.builds_del_backend()
        self.assertIsNone(w.ESTADO["grupo"])




class OroLineas(unittest.TestCase):  # A1: costo TOTAL de Data Dragon, no el «price» de la Live Client Data
    def test_suma_con_precios_totales(self):
        import companion
        pr = {"3057": 900, "1055": 450, "2003": 50}
        yo = {"team": "ORDER", "items": [{"itemID": 3057, "price": 650}, {"itemID": 2003, "count": 3}]}
        ri = {"team": "CHAOS", "items": [{"itemID": 1055}]}
        otro = {"team": "ORDER", "items": [{"itemID": 1055}]}
        o = companion.oro_lineas({"allPlayers": [yo, ri, otro]}, yo, ri, pr)
        self.assertEqual(o, {"tu": 1050, "rival": 450, "equipo": 1500, "equipo_rival": 450})
        self.assertIsNone(companion.oro_lineas({"allPlayers": [yo]}, yo, None, {}))  # sin Data Dragon: nada
        self.assertIsNone(companion.oro_lineas({"allPlayers": [yo]}, yo, None, pr)["rival"])




class PicoRival(unittest.TestCase):  # A2: un aviso por ítem completo del rival, solo si te saca ventaja en ítems
    def foto(self, mios, suyos, t=720):
        it = lambda ids: [{"itemID": i, "displayName": f"Item{i}"} for i in ids]
        return {"activePlayer": {"riotId": "yo#1"}, "gameData": {"gameTime": t},
                "allPlayers": [{"riotId": "yo#1", "position": "MIDDLE", "team": "ORDER", "items": it(mios)},
                               {"riotId": "el#2", "position": "MIDDLE", "team": "CHAOS", "championName": "Zed", "items": it(suyos)}]}

    def test_avisa_una_vez_por_item(self):
        import companion
        leg = {"6692", "3142"}
        self.assertIsNone(companion.aviso_pico(self.foto([], [1036]), leg))  # componente: nada
        c, txt = companion.aviso_pico(self.foto([], [6692, 1036]), leg)
        self.assertEqual(c, "pico:1:Item6692"); self.assertIn("Zed ya tiene 1 ítem completo (Item6692)", txt); self.assertIn("Min 12", txt)
        self.assertIsNone(companion.aviso_pico(self.foto([3142], [6692]), leg))  # parejos en ítems: sin aviso
        self.assertEqual(companion.aviso_pico(self.foto([3142], [6692, 3142]), leg)[0], "pico:2:Item3142|Item6692")
        self.assertIsNone(companion.aviso_pico({"allPlayers": []}, leg))




class ImportarRunas(unittest.TestCase):  # A5: solo en selección, solo la página de runas, reemplaza la activa si es editable
    PAG = {"primaryStyleId": 8000, "subStyleId": 8400, "selectedPerkIds": [8008, 9111, 9104, 8299, 8444, 8453, 5005, 5008, 5011]}

    def cliente(self, fase="ChampSelect", actual=None):
        llamadas = []
        leer = lambda path: {"/lol-gameflow/v1/gameflow-phase": fase, "/lol-perks/v1/currentpage": actual}.get(path)
        escribir = lambda metodo, path, cuerpo=None: llamadas.append((metodo, path, cuerpo)) or True
        return leer, escribir, llamadas

    def test_crea_y_reemplaza(self):
        import companion
        leer, escribir, ll = self.cliente(actual={"id": 77, "isDeletable": True, "name": "Racha: Ahri"})  # una que creó Racha
        ok, msg = companion.importar_runas("Yone", self.PAG, leer, escribir)
        self.assertTrue(ok); self.assertIn("Listo", msg)
        self.assertEqual([(m, p) for m, p, _ in ll], [("DELETE", "/lol-perks/v1/pages/77"), ("POST", "/lol-perks/v1/pages")])
        self.assertEqual(ll[1][2]["selectedPerkIds"], self.PAG["selectedPerkIds"]); self.assertTrue(ll[1][2]["current"])
        self.assertTrue(all(p.startswith("/lol-perks/") for _, p, _ in ll))  # nada fuera de las runas

    def test_nunca_borra_una_pagina_tuya(self):  # revisión de DeepSeek: una página editable del jugador no se toca
        import companion
        leer, escribir, ll = self.cliente(actual={"id": 5, "isDeletable": True, "name": "Mi página de Yone"})
        self.assertTrue(companion.importar_runas("Yone", self.PAG, leer, escribir)[0])
        self.assertEqual([m for m, _, _ in ll], ["POST"])

    def test_no_borra_paginas_fijas_ni_actua_fuera_de_seleccion(self):
        import companion
        leer, escribir, ll = self.cliente(actual={"id": 1, "isDeletable": False})
        self.assertTrue(companion.importar_runas("Yone", self.PAG, leer, escribir)[0])
        self.assertEqual([m for m, _, _ in ll], ["POST"])
        leer, escribir, ll = self.cliente(fase="InProgress")
        self.assertFalse(companion.importar_runas("Yone", self.PAG, leer, escribir)[0]); self.assertEqual(ll, [])
        leer, escribir, ll = self.cliente()
        self.assertFalse(companion.importar_runas("Yone", {"selectedPerkIds": [1, 2]}, leer, escribir)[0]); self.assertEqual(ll, [])
        self.assertFalse(companion.importar_runas("Yone", None, leer, escribir)[0])




class HistorialAvisos(unittest.TestCase):  # F8: todos los consejos de la partida; se vacía al entrar a la siguiente selección
    def setUp(self): self.viejo = dict(w.ESTADO); w.ESTADO.update(avisos=[])
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def test_acumula_y_se_vacia(self):
        w.evento(("aviso", {"texto": "A", "tipo": "consejo", "minuto": 6}))
        w.evento(("aviso", {"texto": "error de red", "tipo": "error", "minuto": None}))  # los errores no van al historial
        w.evento(("aviso", {"texto": "B", "tipo": "consejo", "minuto": 16}))
        self.assertEqual([a["texto"] for a in w.ESTADO["avisos"]], ["A", "B"])
        self.assertEqual(w.ESTADO["aviso"]["texto"], "B")
        w.evento(("fase", "ChampSelect")); self.assertEqual(w.ESTADO["avisos"], [])




class AvisoEnFranja(unittest.TestCase):  # F1: el corto sale en la franja 12 s; ≥ 90 s entre avisos y ≤ 6 por partida
    def setUp(self): self.viejo = dict(w.ESTADO); w.ESTADO.update(avisos=[], aviso=None)
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def test_limites_y_pieza(self):
        import overlay
        av = lambda t: w.evento(("aviso", {"texto": "largo " + t, "corto": t, "tipo": "consejo", "minuto": 10}))
        with mock.patch.object(w.time, "time", lambda: 1000.0): av("A")
        self.assertEqual(w.ESTADO["aviso"]["franja"], 1000.0)
        self.assertEqual(overlay.pieza_aviso(w.ESTADO["aviso"], 1011.0), ("A", overlay.AMBAR))
        self.assertIsNone(overlay.pieza_aviso(w.ESTADO["aviso"], 1012.0))  # a los 12 s se va
        with mock.patch.object(w.time, "time", lambda: 1050.0): av("B")  # 50 s después: queda en el historial, no en la franja
        self.assertNotIn("franja", w.ESTADO["aviso"]); self.assertEqual(len(w.ESTADO["avisos"]), 2)
        for i in range(8):
            with mock.patch.object(w.time, "time", lambda: 1200.0 + 100 * i): av(f"C{i}")
        self.assertEqual(sum(1 for a in w.ESTADO["avisos"] if a.get("franja")), 6)  # tope por partida
        self.assertIsNone(overlay.pieza_aviso({"texto": "x", "tipo": "consejo"}, 0))  # sin corto: nada

    def test_avisos_reales_traen_corto(self):
        import companion_gui as g, companion
        e = g.aviso(companion.Texto("largo", "corto"), "consejo", 5)[1]
        self.assertEqual((e["texto"], e["corto"]), ("largo", "corto"))
        self.assertIsNone(g.aviso("error de red")[1]["corto"])




class ReglaHoy(unittest.TestCase):  # F3: en la franja va TU regla que más fallas, no la del autor
    def test_elige_la_medible_que_mas_fallas(self):
        try: import vistas
        except Exception as e: self.skipTest(f"vistas necesita datos: {e}")
        rs = [dict(metrica="kp", texto="KP", numero="x", ok=1, n=20), dict(metrica="nivel", texto="Nv", numero="y", ok=5, n=20, minuto="6"),
              dict(metrica="muertes", texto="M", numero="z", ok=15, n=20)]  # ya ordenadas de la que más cuesta a la que menos
        self.assertEqual(vistas.regla_hoy(rs), dict(metrica="nivel", texto="Nv", numero="y", ok=5, n=20))  # kp no se cuenta en vivo
        self.assertIsNone(vistas.regla_hoy([dict(metrica="nivel", texto="Nv", numero="y", ok=None, n=0)]))
        self.assertIsNone(vistas.regla_hoy(None))

    def test_franja_con_regla_de_nivel(self):
        import overlay
        meta = {"nivel": 5, "nivel_rival": 6, "rival": "Zed", "cs": 40, "rival_cs": 44, "minuto": 4, "muertes14": None, "objetivos": {}}
        t = [x for x, _ in overlay.partes(meta, 0, None, {"metrica": "nivel"})]
        self.assertEqual(t[0], "▼ Regla Nv 6: 5 vs 6 Zed")
        self.assertFalse(any(x.startswith(("Nv", "▼ Nv")) for x in t))  # no se repite como pieza de línea
        t = [x for x, _ in overlay.partes({**meta, "minuto": 18, "muertes14": 1}, 0, None, {"metrica": "nivel"})]
        self.assertFalse(any("Muertes" in x for x in t))  # tu regla es la del nivel: el contador de muertes no ocupa lugar
        t = [x for x, _ in overlay.partes({**meta, "minuto": 18, "muertes14": 1}, 0, None, None)]
        self.assertIn("Muertes 14–25: 1/2", t)  # sin datos tuyos: la de muertes como consejo




class MomentoMuerto(unittest.TestCase):  # F4: muerto, la franja deja tu regla y el próximo objetivo
    def test_muerto(self):
        import overlay, companion
        meta = {"nivel": 11, "nivel_rival": 12, "rival": "Zed", "cs": 140, "rival_cs": 150, "minuto": 18, "muertes14": 2,
                "objetivos": {"dragon": 200, "baron": 40}, "recibido": 0, "muerto": True, "revive": 25}
        self.assertEqual([x for x, _ in overlay.partes(meta, 0)], ["Muertes 14–25: 2/2", "! Barón 0:40"])
        vivo = [x for x, _ in overlay.partes({**meta, "muerto": False}, 0)]
        self.assertGreater(len(vivo), 2)
        temprano = [x for x, _ in overlay.partes({**meta, "minuto": 8, "muertes14": None, "objetivos": {"dragon": 200, "baron": 720}}, 0)]
        self.assertEqual(temprano, ["Dragón 3:20"])  # antes del 14 no hay contador: solo el objetivo
        d = {"activePlayer": {"riotId": "yo#1"}, "gameData": {"gameTime": 900, "gameMode": "CLASSIC", "mapNumber": 11},
             "allPlayers": [{"riotId": "yo#1", "position": "MIDDLE", "team": "ORDER", "isDead": True, "respawnTimer": 24.6, "scores": {}},
                            {"riotId": "el#2", "position": "MIDDLE", "team": "CHAOS", "isDead": True, "respawnTimer": 30, "scores": {}}]}
        m = companion.meta_fase(d, {})
        self.assertEqual((m["muerto"], m["revive"]), (True, 25))
        self.assertNotIn("rival_muerto", m)  # nunca el estado de muerte del rival




class CuentaPorRiotId(unittest.TestCase):  # sin el cliente abierto: tu Riot ID guardado (el login oficial de Riot llega con la production key)
    def setUp(self):
        self.viejo = dict(w.ESTADO); self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        p = mock.patch.object(w.gui, "CUENTA_F", pathlib.Path(self.d.name) / "cuenta.json"); p.start(); self.addCleanup(p.stop)
        p = mock.patch.object(w, "descargar_todo", lambda *a, **k: None); p.start(); self.addCleanup(p.stop)
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def test_valida_y_guarda(self):
        g = w.gui
        for malo in [("sin-tag", "la1"), ("ab#1", "la1"), ("Nombre#TAG", "marte"), ("", "")]:
            with self.assertRaises(ValueError): g.guardar_cuenta(*malo)
        self.assertEqual(g.guardar_cuenta(" cozi#1134 ", "LA1"), {"riot_id": "cozi#1134", "region": "la1"})
        self.assertEqual(g.cuenta_guardada()["region"], "la1")

    def test_buscar(self):
        llamadas = []
        def falso(m, ruta, c=None, base=None): llamadas.append(ruta); return {"gameName": "cozi", "tagLine": "1134"}
        with mock.patch.object(w.companion, "backend", falso):
            ok, msg = w.buscar_cuenta("cozi#1134", "la1")
        self.assertTrue(ok); self.assertIn("Encontrada: cozi#1134", msg)
        self.assertEqual(llamadas, ["/v1/riot/americas/riot/account/v1/accounts/by-riot-id/cozi/1134"])
        def no_existe(*a, **k): raise urllib.error.HTTPError("u", 404, "no", {}, None)
        with mock.patch.object(w.companion, "backend", no_existe):
            ok, msg = w.buscar_cuenta("nadie#000", "euw1")
        self.assertFalse(ok); self.assertIn("No existe", msg)
        self.assertEqual(w.gui.cuenta_guardada()["riot_id"], "cozi#1134")  # revisión de DeepSeek: un TAG mal escrito no borra la cuenta buena
        def caido(*a, **k): raise urllib.error.URLError("sin red")
        with mock.patch.object(w.companion, "backend", caido):
            ok, msg = w.buscar_cuenta("cozi#1134", "kr")
        self.assertTrue(ok); self.assertIn("Guardada", msg)  # sin servidor se guarda igual y se verifica al descargar
        self.assertFalse(w.buscar_cuenta("mal", "la1")[0])




class RangoPorApi(unittest.TestCase):  # al buscar tu nick, el rango llega de la Riot API (league-v4) sin esperar la descarga
    def test_convierte_league_v4(self):
        es = [{"queueType": "RANKED_FLEX_SR", "tier": "GOLD", "rank": "I", "leaguePoints": 3, "wins": 1, "losses": 1},
              {"queueType": "RANKED_SOLO_5x5", "tier": "MASTER", "rank": "I", "leaguePoints": 15, "wins": 186, "losses": 157}]
        rutas = []
        def falso(m, ruta, c=None, base=None): rutas.append(ruta); return es
        with mock.patch.object(w.companion, "backend", falso):
            r = w.rango_api("a" * 78, "la1")
        self.assertEqual((r["tier"], r["division"], r["lp"], r["n"], r["wr"]), ("MASTER", None, 15, 343, 54))
        self.assertEqual(rutas, ["/v1/riot/la1/lol/league/v4/entries/by-puuid/" + "a" * 78])
        with mock.patch.object(w.companion, "backend", lambda *a, **k: []):
            self.assertIsNone(w.rango_api("a" * 78, "la1"))  # sin ranked: nada
        self.assertIsNone(w.rango_api("../../x", "la1"))  # un puuid raro no arma rutas
        self.assertIsNone(w.rango_api(None, "la1"))




class Sirvio(unittest.TestCase):  # v0.13: «¿te sirvieron los avisos?», una respuesta por partida, como contador en el ping
    def setUp(self):
        self.viejo = dict(w.ESTADO); self.sv = dict(w.SIRVIO); w.SIRVIO.update(si=0, no=0, no_vi=0); w.PING[0] = None
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo); w.SIRVIO.update(self.sv); w.PING[0] = None

    def test_contesta_una_vez_y_viaja_en_el_ping(self):
        import http.client, threading
        srv = w.http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        def post(cuerpo):
            c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
            c.request("POST", "/api/sirvio", body=cuerpo, headers={"X-HTC": "1", "Content-Type": "application/json", "Content-Length": str(len(cuerpo))})
            return c.getresponse().status
        try:
            w.ESTADO.update(fin={"texto": "fin"})
            self.assertEqual(post(b'{"valor": "talvez"}'), 400)
            self.assertEqual(post(b'{"valor": "si"}'), 200)
            self.assertEqual(post(b'{"valor": "no"}'), 409)  # una sola por partida
            self.assertEqual((w.SIRVIO["si"], w.ESTADO["fin"]["sirvio"]), (1, "si"))
        finally: srv.shutdown()
        enviado = {}
        with mock.patch.object(w.companion, "backend", lambda m, r, c=None, base=None: enviado.update(c) or {"ok": True}), \
                mock.patch.object(w.gui, "ajustes", lambda: {"metricas": True}):
            w.ping()
        self.assertEqual((enviado["sirvio_si"], enviado["sirvio_no"]), (1, 0))
        self.assertEqual(w.SIRVIO["si"], 0)  # ya enviado: no se cuenta dos veces




class Coach(unittest.TestCase):  # F12 (prototipo): la regla del coach manda en la franja y se arma el informe
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        p = mock.patch.object(w.gui, "COACH_F", pathlib.Path(self.d.name) / "coach.json"); p.start(); self.addCleanup(p.stop)

    def test_codigo_ida_y_vuelta_y_manipulado(self):
        import base64, json
        g = w.gui
        c = g.codigo_coach("  juega   por objetivo ", 1)
        self.assertEqual(g.leer_codigo_coach(c), {"texto": "juega por objetivo", "metrica": "muertes", "tope": 1})
        for malo in ("", "RACHA1.no-es-base64!!", "OTRO." + c[7:], c[:-4],
                     "RACHA1." + base64.urlsafe_b64encode(json.dumps({"t": "x" * 200, "m": "muertes", "tope": 1}).encode()).decode(),
                     "RACHA1." + base64.urlsafe_b64encode(json.dumps({"t": "hola", "m": "muertes", "tope": 9}).encode()).decode()):
            with self.assertRaises(ValueError): g.leer_codigo_coach(malo)
        with self.assertRaises(ValueError): g.codigo_coach("ab", 1)
        self.assertIsNone(g.coach()); g.guardar_coach(c); self.assertEqual(g.coach()["tope"], 1)

    def test_informe_y_regla_de_hoy(self):
        r = {"vistas": {"regla_hoy": {"metrica": "nivel"}}, "resumen": {"partidas": [
            {"fecha": "11-10", "campeon": "Yone", "rival": "Zed", "win": True, "muertes14_25": 1},
            {"fecha": "11-09", "campeon": "Ekko", "rival": None, "win": False, "muertes14_25": 3},
            {"fecha": "11-08", "campeon": "Sylas", "win": True, "muertes14_25": None}]}}
        w.aplicar_coach(r, {"texto": "por objetivo", "metrica": "muertes", "tope": 1})
        rh = r["vistas"]["regla_hoy"]
        self.assertEqual((rh["metrica"], rh["tope"], rh["ok"], rh["n"], rh["coach"]), ("muertes", 1, 1, 2, True))
        inf = r["vistas"]["informe_coach"]
        self.assertIn("Cumplida en 1 de 2 partidas", inf); self.assertIn("Yone vs Zed · victoria · muertes 14–25: 1 cumplida", inf)
        self.assertIn("Ekko vs ? · derrota · muertes 14–25: 3 fallada", inf)
        self.assertIs(w.aplicar_coach(None, {"texto": "x", "tope": 1}), None)  # sin datos no revienta
        sin = {"vistas": {"regla_hoy": None}, "resumen": {"partidas": []}}
        with mock.patch.object(w.gui, "coach", lambda: None): self.assertIsNone(w.aplicar_coach(sin)["vistas"]["regla_hoy"])

    def test_franja_con_tope_del_coach(self):
        import overlay
        meta = {"minuto": 18, "muertes14": 1, "objetivos": {}}
        t = [x for x, _ in overlay.partes(meta, 0, None, {"metrica": "muertes", "tope": 1})]
        self.assertIn("Muertes 14–25: 1/1", t)
        self.assertIn("▼ Muertes 14–25: 2/1", [x for x, _ in overlay.partes({**meta, "muertes14": 2}, 0, None, {"metrica": "muertes", "tope": 1})])



if __name__ == "__main__": unittest.main()
