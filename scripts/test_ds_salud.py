"""D-a del PLAN-ENVIVO: pruebas de borde de salud.evaluar (pura). Sin red ni Win32.
Los falsos positivos y negativos hallados (S2, S3, S6) ya estan arreglados y sus pruebas pasan."""
import unittest

import salud

AHORA = 1000.0
JUEGO = (0, 0, 1920, 1080)


def estado(**s):
    base = {"fase": "InProgress", "meta": {"recibido": AHORA - 5}, "ajustes": {}, "v": 1}
    base.update(s); return {"codigo": 200, "json": base, "bytes": 5000, "ms": 20}


def franja(rect=(422, 6, 1100, 40), **kw):
    f = dict(rect=rect, visible=True, topmost=True, transparente=True, noactivate=True, colgada=False, sobre_juego=True, monitor=1)
    f.update(kw); return f


def sano(**kw):
    d = {"estado": estado(), "fase_lcu": "InProgress", "vivo": [100, 102], "juego": JUEGO, "monitor_juego": 1, "franja": franja(), "franja_debe": True}
    d.update(kw); return d


def por_id(res, i): return [x for x in res if x["id"] == i]


def nivel(d, i):
    xs = por_id(salud.evaluar(d, AHORA), i)
    return xs[0]["nivel"] if xs else None


class Sano(unittest.TestCase):
    def test_pasada_sana_no_tiene_falla_ni_aviso(self):
        self.assertEqual(salud.resumen(salud.evaluar(sano(), AHORA)), "OK")


class S1(unittest.TestCase):
    def test_200_kb_justos_pasan_y_uno_mas_falla(self):  # 200_000 bytes es el umbral (no 200 KiB)
        e = estado(); e["bytes"] = 200_000
        self.assertEqual(nivel(sano(estado=e), "S1"), "OK")
        e["bytes"] = 200_001
        self.assertEqual(nivel(sano(estado=e), "S1"), "FALLA")

    def test_1000_ms_justos_pasan(self):
        e = estado(); e["ms"] = 1000
        self.assertEqual(nivel(sano(estado=e), "S1"), "OK")

    def test_falta_una_clave_o_json_invalido(self):
        e = estado(); del e["json"]["ajustes"]
        self.assertEqual(nivel(sano(estado=e), "S1"), "FALLA")
        self.assertEqual(salud.evaluar({"estado": {"codigo": 200, "json": "no es dict"}}, AHORA)[0]["nivel"], "FALLA")
        self.assertEqual(salud.evaluar({}, AHORA)[0]["nivel"], "FALLA")  # servidor muerto: solo S1, sin excepcion


class S3S4(unittest.TestCase):
    def test_gametime_que_no_avanza_falla_y_en_cero_no(self):
        self.assertEqual(nivel(sano(vivo=[500, 500]), "S3"), "FALLA")
        self.assertEqual(nivel(sano(vivo=[0, 0]), "S3"), "OK")  # cargando la partida: el reloj aun no corre
        self.assertEqual(nivel(sano(vivo=[500, None]), "S3"), "OK")

    def test_sin_respuesta_es_aviso_si_carga_y_falla_si_no(self):
        self.assertEqual(nivel(sano(vivo=[None, None], cargando=True), "S3"), "AVISO")
        self.assertEqual(nivel(sano(vivo=[None, None], cargando=False), "S3"), "FALLA")

    def test_fase_game_start_no_cuenta_como_partida(self):
        d = sano(estado=estado(fase="GameStart"), fase_lcu="GameStart", franja=None, franja_debe=False)
        r = salud.evaluar(d, AHORA)
        self.assertEqual([x["id"] for x in r if x["id"] in ("S3", "S4", "S5", "S9")], [])  # sin chequeos de partida
        self.assertEqual(nivel(d, "S6"), "OK")

    def test_meta_none_o_recibido_none_con_el_juego_vivo_falla_s4(self):
        self.assertEqual(nivel(sano(estado=estado(meta=None)), "S4"), "FALLA")
        self.assertEqual(nivel(sano(estado=estado(meta={"recibido": None})), "S4"), "FALLA")

    def test_s4_25_s_justos_ok_y_26_falla_y_solo_con_juego_pasado_el_30(self):
        self.assertEqual(nivel(sano(estado=estado(meta={"recibido": AHORA - 25})), "S4"), "OK")
        self.assertEqual(nivel(sano(estado=estado(meta={"recibido": AHORA - 26})), "S4"), "FALLA")
        self.assertIsNone(nivel(sano(vivo=[30, 32], estado=estado(meta=None)), "S4"))

    def test_falso_positivo_fase_none_en_racha_y_cliente_cerrado_no_es_partida(self):
        # salud.py:34 y :203: lcu None (cliente cerrado) y fase None de Racha cuentan como «jugando»; sin partida
        # real, S3 pasa a FALLA a los 120 s. Debe ser: sin Live API ni meta fresca, no jugando.
        d = {"estado": estado(fase=None, meta=None), "fase_lcu": None, "vivo": [None, None], "cargando": False}
        self.assertNotEqual(nivel(d, "S3"), "FALLA")


class S2(unittest.TestCase):
    def test_fases_distintas_fallan_e_iguales_pasan(self):
        d = sano(estado=estado(fase="Lobby"), fase_lcu="InProgress", franja=None, franja_debe=False)
        self.assertEqual(nivel(d, "S2"), "FALLA")
        d["fase_lcu"] = "Lobby"  # iguales: OK
        self.assertEqual(nivel(d, "S2"), "OK")


class S5S6(unittest.TestCase):
    def test_franja_ausente_u_oculta_falla_si_debe_verse(self):
        self.assertEqual(nivel(sano(franja=None), "S5"), "FALLA")
        self.assertEqual(nivel(sano(franja=franja(visible=False)), "S5"), "FALLA")

    def test_banderas_de_ventana(self):
        for k in ("topmost", "transparente", "noactivate"):
            self.assertEqual(nivel(sano(franja=franja(**{k: False})), "S5"), "FALLA", k)
        self.assertEqual(nivel(sano(franja=franja(colgada=True)), "S5"), "FALLA")
        self.assertEqual(nivel(sano(franja=franja(sobre_juego=False)), "S5"), "FALLA")

    def test_otro_monitor_y_fuera_del_juego(self):
        self.assertEqual(nivel(sano(franja=franja(monitor=2)), "S5"), "FALLA")
        self.assertEqual(nivel(sano(franja=franja(rect=(-1920 + 10, 6, -1920 + 700, 40), monitor=2)), "S5"), "FALLA")
        self.assertEqual(nivel(sano(franja=franja(rect=(1900, 6, 2000, 40))), "S5"), "FALLA")  # se sale por la derecha

    def test_ancho_60_justo_pasa_y_61_falla(self):
        w = int(1920 * 0.60)  # 1152 px
        # a x=300..1452 (0.756 del ancho) no pisa el marcador: con el ancho justo S5 queda OK
        self.assertEqual(nivel(sano(franja=franja(rect=(300, 6, 300 + w, 40))), "S5"), "OK")
        r = por_id(salud.evaluar(sano(franja=franja(rect=(300, 6, 300 + w, 40))), AHORA), "S5")[0]
        self.assertNotIn("ancho", r["detalle"])
        r = por_id(salud.evaluar(sano(franja=franja(rect=(300, 6, 300 + w + 20, 40))), AHORA), "S5")[0]
        self.assertIn("ancho", r["detalle"])

    def test_alto_8_por_ciento(self):  # la pastilla mide 72 px a 1080 (6,7 %); el tope pasó de 5 a 8 % (plan del overlay)
        r = por_id(salud.evaluar(sano(franja=franja(rect=(422, 6, 802, 6 + 72))), AHORA), "S5")[0]
        self.assertNotIn("alto", r["detalle"])
        r = por_id(salud.evaluar(sano(franja=franja(rect=(422, 6, 802, 6 + 100))), AHORA), "S5")[0]
        self.assertIn("alto", r["detalle"])

    def test_pisa_cada_zona_prohibida(self):
        for z, (a, b, c, e) in salud.ZONAS.items():
            x, y = int(JUEGO[2] * (a + c) / 2), int(JUEGO[3] * (b + e) / 2)  # el centro de la zona
            f = franja(rect=(x - 20, y - 10, x + 20, y + 10))
            r = por_id(salud.evaluar(sano(franja=f), AHORA), "S5")[0]
            self.assertEqual(r["nivel"], "FALLA", z); self.assertIn(f"pisa {z}", r["detalle"], z)

    def test_tocar_el_borde_de_una_zona_no_la_pisa(self):
        a = int(1920 * 0.78)  # borde izquierdo del marcador, y justo debajo de su borde inferior
        f = franja(rect=(a - 100, 6, a, 40))
        self.assertNotIn("pisa marcador", por_id(salud.evaluar(sano(franja=f), AHORA), "S5")[0]["detalle"])

    def test_s6_visible_fuera_de_partida_falla(self):
        d = {"estado": estado(fase="Lobby"), "fase_lcu": "Lobby", "franja": franja()}
        self.assertEqual(nivel(d, "S6"), "FALLA")
        d["franja"] = None
        self.assertEqual(nivel(d, "S6"), "OK")

    def test_falso_negativo_franja_visible_con_meta_de_mas_de_30_s_en_partida(self):
        # salud.py:46 y :60: en partida con franja_debe False (meta vieja) no se mira nada, y el plan pide S6 FALLA ahi.
        d = sano(estado=estado(meta={"recibido": AHORA - 45}), franja_debe=False)
        self.assertEqual(nivel(d, "S6"), "FALLA")


class S7aS9(unittest.TestCase):
    def test_cpu_1_justo_ok_y_dos_pasadas_arriba_falla(self):
        self.assertEqual(nivel(sano(cpu=1.0, cpu_antes=1.0, rss_mb=100), "S8"), "OK")
        self.assertEqual(nivel(sano(cpu=1.5, cpu_antes=0.2, rss_mb=100), "S8"), "AVISO")
        self.assertEqual(nivel(sano(cpu=1.5, cpu_antes=1.5, rss_mb=100), "S8"), "FALLA")
        self.assertEqual(nivel(sano(cpu=1.5, cpu_antes=None, rss_mb=100), "S8"), "AVISO")  # primera pasada
        self.assertIsNone(nivel(sano(cpu=None), "S8"))

    def test_s8_edad_proceso_cero_cuenta_como_recien_arrancado(self):
        """edad_proceso 0 es recién arrancado: dos pasadas altas es AVISO, no FALLA."""
        self.assertEqual(nivel(sano(cpu=1.5, cpu_antes=1.5, rss_mb=100, edad_proceso=0), "S8"), "AVISO")

    def test_s8_edad_proceso_none_cuenta_como_viejo(self):
        """edad_proceso None (sin medir) cuenta como viejo: dos pasadas altas es FALLA."""
        self.assertEqual(nivel(sano(cpu=1.5, cpu_antes=1.5, rss_mb=100, edad_proceso=None), "S8"), "FALLA")

    def test_s8_edad_proceso_200_cuenta_como_viejo(self):
        """edad_proceso 200 >= ARRANQUE: dos pasadas altas es FALLA."""
        self.assertEqual(nivel(sano(cpu=1.5, cpu_antes=1.5, rss_mb=100, edad_proceso=200), "S8"), "FALLA")

    def test_s8_lectura_anterior_del_arranque_no_cuenta(self):
        """cpu_antes medido a los 28 s de abrir Racha (precalculo) no vale como pasada anterior."""
        self.assertEqual(nivel(sano(cpu=1.41, cpu_antes=2.03, rss_mb=61, edad_proceso=340, edad_antes=28), "S8"), "AVISO")
        self.assertEqual(nivel(sano(cpu=1.41, cpu_antes=2.03, rss_mb=61, edad_proceso=340, edad_antes=200), "S8"), "FALLA")
        self.assertEqual(nivel(sano(cpu=1.41, cpu_antes=2.03, rss_mb=61, edad_proceso=340, edad_antes=None), "S8"), "FALLA")

    def test_rss_200_justo_ok_y_201_falla(self):
        self.assertEqual(nivel(sano(cpu=0.1, rss_mb=200), "S8"), "OK")
        self.assertEqual(nivel(sano(cpu=0.1, rss_mb=201), "S8"), "FALLA")

    def test_grabacion_dos_archivos_atrasada_o_ausente(self):
        self.assertEqual(nivel(sano(vivo=[100, 102], grabacion=[10, 2]), "S9"), "FALLA")
        self.assertEqual(nivel(sano(vivo=[100, 102], grabacion=[46, 1]), "S9"), "FALLA")
        self.assertEqual(nivel(sano(vivo=[100, 102], grabacion=[45, 1]), "S9"), "OK")
        self.assertEqual(nivel(sano(vivo=[100, 102], grabacion=[None, 0]), "S9"), "FALLA")
        self.assertIsNone(nivel(sano(vivo=[50, 52], grabacion=[None, 0]), "S9"))  # partida de menos de 60 s

    def test_pantalla_completa(self):
        self.assertEqual(nivel(sano(pantalla_completa=True), "S7"), "FALLA")  # Racha dice False y el juego True
        d = sano(pantalla_completa=True); d["estado"]["json"]["pantalla_completa"] = True
        self.assertEqual(nivel(d, "S7"), "AVISO")
        self.assertEqual(nivel(sano(pantalla_completa=False), "S7"), "OK")


class S10(unittest.TestCase):
    def test_vista_mala_falla_y_sana_pasa(self):
        r = salud.evaluar(sano(vistas={"perfil": (True, 800, ""), "envivo": (False, 900, "Esta vista falló")}), AHORA)
        self.assertEqual([x["nivel"] for x in por_id(r, "S10")], ["OK", "FALLA"])


if __name__ == "__main__": unittest.main()
