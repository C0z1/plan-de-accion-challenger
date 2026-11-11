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
        self.assertEqual(set(c), {"version", "region", "overlay", "champ_select", "revision"})  # nada que identifique

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
        self.assertEqual(c, "pico:1:Item6692"); self.assertIn("Zed terminó Item6692", txt); self.assertIn("Min 12", txt)
        self.assertIsNone(companion.aviso_pico(self.foto([3142], [6692]), leg))  # parejos en ítems: sin aviso
        self.assertEqual(companion.aviso_pico(self.foto([3142], [6692, 3142]), leg)[0], "pico:2:Item3142")
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
        leer, escribir, ll = self.cliente(actual={"id": 77, "isDeletable": True})
        ok, msg = companion.importar_runas("Yone", self.PAG, leer, escribir)
        self.assertTrue(ok); self.assertIn("Listo", msg)
        self.assertEqual([(m, p) for m, p, _ in ll], [("DELETE", "/lol-perks/v1/pages/77"), ("POST", "/lol-perks/v1/pages")])
        self.assertEqual(ll[1][2]["selectedPerkIds"], self.PAG["selectedPerkIds"]); self.assertTrue(ll[1][2]["current"])
        self.assertTrue(all(p.startswith("/lol-perks/") for _, p, _ in ll))  # nada fuera de las runas

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



if __name__ == "__main__": unittest.main()
