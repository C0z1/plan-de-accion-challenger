"""Overlay en partida: los estados de la pastilla, su dibujo, cuándo se ve, dónde va y que la ventana abre y cierra."""
import unittest

import overlay

META = {"nivel": 11, "nivel_rival": 12, "rival": "Ahri", "campeon": "Ekko", "cs": 71, "rival_cs": 140, "recibido": 1000.0, "t": 300, "kda": "1/0/2"}


class TestEstado(unittest.TestCase):  # la pastilla 380×72 (plan del overlay de Fable con la revisión de DeepSeek)
    def e(self, **kw): return overlay.estado({**META, **kw}, 1000.0)

    def test_linea_bordes(self):
        self.assertEqual(self.e(t=839)["tipo"], "linea"); self.assertEqual(self.e(t=840, muertes14=0)["tipo"], "peleas")
        self.assertEqual(self.e(t=1499, muertes14=0)["tipo"], "peleas"); self.assertEqual(self.e(t=1500, muertes14=0)["tipo"], "tarde")

    def test_nivel_contra_rival(self):
        e = self.e(t=400)
        self.assertEqual((e["flecha"]["txt"], e["flecha"]["color"], e["chip"]), ("-1", "rojo", ("Nivel -1", "rojo")))
        self.assertEqual(self.e(t=400, nivel=12)["flecha"]["txt"], "=")
        self.assertEqual(self.e(t=400, nivel=13)["flecha"]["color"], "salvia")
        self.assertIsNone(self.e(t=400, rival=None)["rival"])  # práctica: solo tu medallón

    def test_ritmo_de_cs(self):  # umbral sobre el flotante: cs_meta 70 al 10 -> a los 5:00 se esperan 30
        b = lambda cs: self.e(t=300, nivel=12, cs=cs, cs_meta=70)["b"]
        self.assertEqual((b(30)["color"], b(26)["color"], b(25)["color"]), ("salvia", "oro", "rojo"))
        self.assertEqual(b(30)["etq"], "ritmo 30")
        self.assertEqual(self.e(t=700, nivel=12)["b"]["num"], "-69")  # pasado el 10: CS contra tu rival

    def test_peleas_y_tope(self):
        chip = lambda m, tope=2: overlay.estado({**META, "t": 1000, "muertes14": m}, 0, regla={"tope": tope})["chip"]
        self.assertEqual([chip(0), chip(2), chip(3), chip(2, tope=3)],
                         [("Vas bien", "salvia"), ("En tu tope", "oro"), ("Sobre tope", "rojo"), ("Vas bien", "salvia")])
        self.assertEqual(self.e(t=1000, muertes14=1, participacion=.58)["b"]["num"], "58%")

    def test_ajustes_apagan(self):
        self.assertEqual(overlay.estado({**META, "t": 300}, 0, {"franja_linea": False})["tipo"], "tarde")
        self.assertEqual(overlay.estado({**META, "t": 1000, "muertes14": 0}, 0, {"franja_regla": False})["tipo"], "tarde")

    def test_aviso_8_s(self):
        av = {"franja": 100.0, "corto": "Min 17: 2 muertes desde el 14"}
        self.assertEqual(overlay.estado(META, 107.9, aviso=av)["tipo"], "aviso")
        self.assertNotEqual(overlay.estado(META, 108.1, aviso=av)["tipo"], "aviso")

    def test_aram_y_sin_datos(self):
        self.assertEqual(overlay.textos(overlay.estado({"modo": "ARAM", "kills": [9, 32], "kda": "6/8/10", "campeon": "Lux"}, 0)), ["9 – 32", "kills", "6/8/10", "KDA"])
        self.assertIsNone(overlay.estado(None, 0)); self.assertEqual(overlay.textos(None), [])

    def test_sin_ordenes(self):  # Riot: dato y tu regla, nunca órdenes (los textos del lienzo se cambiaron)
        for kw in ({"t": 300}, {"t": 700, "nivel": 12}, {"t": 1000, "muertes14": 3}, {"t": 1600, "oro": {"equipo": 9000, "equipo_rival": 9800}}):
            for txt in overlay.textos(self.e(**kw)):
                self.assertNotRegex(txt, r"(?i)pelees|juega|farmea|puedes|cuidado|debes|ve a")
                self.assertLessEqual(len(txt), 12)


class TestFase2(unittest.TestCase):  # «Igualaste» y la moneda del 14 (PLAN-OVERLAY.md, fase 2)
    def test_igualaste_3_s(self):
        m = {}
        overlay.marcar(m, {**META, "t": 400, "nivel": 5, "nivel_rival": 6}, 100.0)
        overlay.marcar(m, {**META, "t": 410, "nivel": 6, "nivel_rival": 6}, 110.0)
        e = lambda ahora: overlay.estado({**META, "t": 410, "nivel": 6, "nivel_rival": 6}, ahora, marcas=m)["tipo"]
        self.assertEqual((e(112.9), e(113.1)), ("igualaste", "linea"))
        m2 = {}; overlay.marcar(m2, {**META, "t": 400, "nivel": 6, "nivel_rival": 6}, 100.0)  # ya iba igual: no es igualar
        m3 = {}; overlay.marcar(m3, {**META, "t": 400, "nivel": 5, "nivel_rival": 6}, 100.0)
        overlay.marcar(m3, {**META, "t": 410, "rival": "Zed", "nivel": 6, "nivel_rival": 6}, 110.0)  # cambió el rival: no cuenta
        self.assertNotIn("igualo", m3)
        self.assertNotIn("igualo", m2)

    def test_oro14_5_s_y_racha(self):
        m = {}; oro = {"tu": 5400, "rival": 5060}
        overlay.marcar(m, {**META, "t": 835, "oro": oro}, 100.0); self.assertNotIn("oro14", m)
        overlay.marcar(m, {**META, "t": 845, "oro": oro}, 110.0)
        e = overlay.estado({**META, "t": 845, "muertes14": 0}, 114.9, marcas=m, racha_oro={"ok": 4, "n": 5})
        self.assertEqual((e["tipo"], e["num"], e["b"]["num"], e["chip"]), ("oro14", "+350", "4 / 5", ("Arriba", "salvia")))
        self.assertEqual(overlay.estado({**META, "t": 845, "muertes14": 0}, 115.1, marcas=m)["tipo"], "peleas")
        overlay.marcar(m, {**META, "t": 900, "oro": {"tu": 0, "rival": 9000}}, 200.0); self.assertEqual(m["oro14"][1], 340)  # una sola vez

    def test_otra_partida_vacia_marcas(self):
        m = {}; overlay.marcar(m, {**META, "t": 900, "oro": {"tu": 1, "rival": 0}}, 0.0)
        overlay.marcar(m, {**META, "t": 10}, 1.0); self.assertNotIn("oro14", m)

    def test_sin_ordenes(self):
        m = {"igualo": 0.0, "oro14": (0.0, -200)}
        for e in (overlay.estado({**META, "t": 845, "nivel": 6, "nivel_rival": 6}, 1.0, marcas=m, racha_oro={"ok": 1, "n": 5}),
                  overlay.estado({**META, "t": 400, "nivel": 6, "nivel_rival": 6}, 1.0, marcas={"igualo": 0.0})):
            for txt in overlay.textos(e): self.assertNotRegex(txt, r"(?i)pelea|juega|farmea|puedes|debes")


class TestExpandida(unittest.TestCase):  # fase 3: al morir, marcador de objetivos (sin timers) y tu regla
    O = {"tuyos": {"dragones": 2, "torres": 4, "larvas": 3, "baron": 0}, "rival": {"dragones": 1, "torres": 2, "larvas": 3, "baron": 1},
         "dragon": 120, "baron": 300}

    def test_solo_muerto(self):
        R = {"texto": "≤ 2 muertes del 14 al 25; antes de un dragón, heraldo o barón, no pelear si no hace falta."}
        e = overlay.estado({**META, "t": 1000, "muertes14": 1, "muerto": True, "objetivos": self.O}, 0, regla=R)
        self.assertEqual(e["extra"]["marcador"], "Dragones 2–1 · Torres 4–2 · Larvas 3–3 · Barón 0–1")
        self.assertTrue(e["extra"]["regla"].endswith("…") and len(e["extra"]["regla"]) <= 62)
        self.assertNotIn("extra", overlay.estado({**META, "t": 1000, "muertes14": 1, "objetivos": self.O}, 0))  # vivo
        self.assertNotIn("extra", overlay.estado({**META, "t": 1000, "muertes14": 1, "muerto": True, "objetivos": self.O}, 0, {"franja_muerto": False}))
        self.assertNotIn("extra", overlay.estado({**META, "muerto": True}, 0))  # sin objetivos

    def test_sin_timers_y_alto(self):
        e = overlay.estado({**META, "t": 1000, "muertes14": 1, "muerto": True, "objetivos": self.O}, 0)
        for t in overlay.textos(e): self.assertNotRegex(t, r"\d:\d\d")  # ningún reloj: solo conteos
        try: import PIL  # noqa: F401
        except ImportError: return
        self.assertEqual(overlay.pintar(e, 1.5).size, (570, 165))

    def test_corta(self):
        self.assertEqual(overlay.corta("Reloj de Arena de Zhonya", 17), "Reloj de Arena…")
        self.assertEqual(overlay.corta("Agrietador", 17), "Agrietador")


class TestPintar(unittest.TestCase):
    def test_tamano_esquinas_y_peor_caso(self):
        try: import PIL  # noqa: F401
        except ImportError: self.skipTest("sin Pillow")
        casos = [overlay.estado({**META, "t": 300, "nivel": 18, "nivel_rival": 18, "cs": 399, "cs_meta": 90}, 0),
                 overlay.estado({**META, "t": 1000, "muertes14": 4}, 0, regla={"tope": 6}),
                 overlay.estado({**META, "campeon": None}, 0, aviso={"franja": 0, "corto": "Min 12: Ahri ya tiene 2 ítems completos contra 1"})]
        for esc in (0.75, 1, 1.5, 2):
            for e in casos:
                im = overlay.pintar(e, esc)
                self.assertEqual(im.size, (round(380 * esc), round(72 * esc)))
                self.assertEqual(im.getpixel((0, 0))[3], 0)  # esquina redonda: transparente
                self.assertGreater(im.getpixel((im.width // 2, 2))[3], 150)  # fondo translúcido

    def test_pulso_engorda_el_borde(self):  # fase B: dos pulsos al entrar un aviso o un momento
        try: import PIL  # noqa: F401
        except ImportError: self.skipTest("sin Pillow")
        e = overlay.estado(META, 0, aviso={"franja": 0, "corto": "Min 12: 2 muertes"})
        a, b = overlay.pintar(e), overlay.pintar({**e, "pulso": True})
        self.assertGreater(b.getpixel((190, 3))[3], a.getpixel((190, 3))[3] - 1)
        self.assertNotEqual(list(a.getdata()), list(b.getdata()))
        self.assertEqual(sum(overlay.SACUDIDA), -1 + 0)  # termina en 0 y casi simétrica: la ventana vuelve a su lugar
        self.assertEqual(overlay.SACUDIDA[-1], 0)

    def test_premultiplicado_sin_halos(self):  # rojo al 50 %: B=0 G=0 R=128 A=128; transparente: todo 0 (si no, halo)
        try: from PIL import Image
        except ImportError: self.skipTest("sin Pillow")
        im = Image.new("RGBA", (2, 1)); im.putpixel((0, 0), (255, 0, 0, 128)); im.putpixel((1, 0), (255, 255, 255, 0))
        self.assertEqual(overlay.bgra_premultiplicado(im), bytes([0, 0, 128, 128, 0, 0, 0, 0]))

    def test_escala(self):
        self.assertEqual([overlay.escala(None), overlay.escala((0, 0, 1280, 720)), overlay.escala((0, 0, 3840, 2160)), overlay.escala((0, 0, 9, 4000))], [1.0, 0.75, 2.0, 2.0])


class TestVisible(unittest.TestCase):  # D2 + D3 del plan En vivo
    def s(self, fase="InProgress", edad=5, overlay=True):
        return {"fase": fase, "meta": {"recibido": 1000 - edad}, "ajustes": {"overlay": overlay}}

    def test_en_partida_con_foto_fresca(self): self.assertTrue(overlay.visible(self.s(), 1000))

    def test_cliente_cerrado_sigue_si_la_foto_llega(self):
        self.assertTrue(overlay.visible(self.s(fase=None), 1000)); self.assertTrue(overlay.visible(self.s(fase="Reconnect"), 1000))

    def test_foto_vieja_oculta(self): self.assertFalse(overlay.visible(self.s(edad=31), 1000))

    def test_fuera_de_partida_o_apagada_oculta(self):
        for s in (self.s(fase="EndOfGame"), self.s(fase="None"), self.s(fase="ChampSelect"), self.s(overlay=False), {"fase": "InProgress", "meta": {"recibido": None}}, {}):
            self.assertFalse(overlay.visible(s, 1000), s)


class TestColocar(unittest.TestCase):  # D4: la franja sigue a la ventana del juego
    def test_juego_en_el_segundo_monitor(self):
        self.assertEqual(overlay.colocar((1920, 0, 4480, 1440), (1920, 1080), 30), (1920 + int(2560 * 0.22), 6))
        self.assertEqual(overlay.colocar((1920, 0, 4480, 1440), (1920, 1080), 30, pos="abajo"), (1920 + int(2560 * 0.30), int(1440 * 0.85) - 30 - 6))  # encima del HUD

    def test_no_pisa_el_marcador(self):  # D9: 719 px (peor caso medido a 1920) en un juego de 1366 se corre a la izquierda
        x, _ = overlay.colocar((0, 0, 1366, 768), (1366, 768), 34, ancho_franja=719)
        self.assertLessEqual(x + 719, int(1366 * overlay.TOPE_DERECHO)); self.assertGreaterEqual(x, 6)
        self.assertEqual(overlay.colocar((0, 0, 1920, 1080), (1920, 1080), 34, ancho_franja=719)[0], int(1920 * 0.22))  # a 1920 cabe: no se mueve

    def test_sin_juego_usa_la_pantalla_principal(self):
        self.assertEqual(overlay.colocar(None, (1920, 1080), 30, pos="abajo", util=0.95), (int(1920 * 0.30), int(1080 * 0.85) - 36))  # encima del HUD, a la derecha del chat


class TestZonas(unittest.TestCase):  # fase C: ni arriba ni abajo pisan minimapa, marcador, HUD ni chat (zonas de salud.py)
    def test_no_pisa_en_ninguna_resolucion(self):
        import salud
        for W, H in ((1920, 1080), (2560, 1440), (1366, 768), (3840, 2160), (1280, 720)):
            juego = (0, 0, W, H); e = overlay.escala(juego); aw = round(380 * e)
            for pos, ah in (("arriba", round(72 * e)), ("abajo", round(72 * e)), ("arriba", round(110 * e)), ("abajo", round(110 * e))):  # también la expandida
                x, y = overlay.colocar(juego, (W, H), ah, 0.22, pos, 6, 1.0, aw)
                f = (x / W, y / H, (x + aw) / W, (y + ah) / H)
                pisa = [z for z, (a, b, c, d) in salud.ZONAS.items() if f[0] < c and f[2] > a and f[1] < d and f[3] > b]
                self.assertEqual(pisa, [], f"{W}x{H} {pos}")


class TestVentana(unittest.TestCase):
    def test_error_de_dibujo_se_registra_una_vez(self):  # D7
        try: import tkinter; tkinter.Tk().destroy()
        except Exception: self.skipTest("sin pantalla")
        vueltas, log = iter(range(3)), []
        overlay.correr(lambda: 1 / 0, lambda: next(vueltas, None) is not None, x=5, registrar=log.append)
        self.assertEqual(len(log), 1); self.assertIn("ZeroDivisionError", log[0])

    def test_abre_y_cierra_fuera_de_pantalla(self):
        try: import tkinter; tkinter.Tk().destroy()
        except Exception: self.skipTest("sin pantalla")  # CI Ubuntu sin display
        vueltas = iter(range(3))
        overlay.correr(lambda: {"fase": "InProgress", "meta": META}, lambda: next(vueltas, None) is not None, x=5)


if __name__ == "__main__":
    unittest.main()
