"""D-b del PLAN-ENVIVO: pruebas de D1, D2, D3 y D10 (nacieron como expectedFailure; Opus aplico T6, T7 y T9). Sin red ni Win32.
Hoy fallan por la razon escrita en el diagnostico; cuando Opus aplique T6, T7 y T9 se les quita el decorador.
overlay.visible(s, ahora) aun no existe: se importa con getattr (la prueba falla con un mensaje claro)."""
import itertools, json, pathlib, unittest
from unittest import mock

import companion, companion_gui, overlay

BASE = pathlib.Path(__file__).resolve().parent.parent
PRACTICA = BASE / "datos" / "vivo" / "20261109-173828.jsonl"


def foto_practice():
    if PRACTICA.exists():
        d = json.loads(PRACTICA.read_text(encoding="utf-8").splitlines()[0]); return d.get("foto", d)
    return {"gameData": {"gameMode": "PRACTICETOOL", "mapNumber": 11, "gameTime": 60}, "allPlayers": [], "events": {"Events": []}}


def visible():
    f = getattr(overlay, "visible", None)
    if f is None: raise AssertionError("overlay.visible(s, ahora) no existe todavia (T7)")
    return f


def estado(fase, recibido, ahora):
    return {"fase": fase, "ajustes": {}, "meta": {"minuto": 8, "objetivos": {"dragon": ahora + 300}, "recibido": recibido}}


class Franja(unittest.TestCase):
    def test_d1_grieta_acepta_practicetool(self):  # D1 / T6: hoy grieta() solo acepta CLASSIC
        self.assertTrue(companion.grieta(foto_practice()))

    def test_d2_visible_con_fase_none_y_meta_fresca(self):  # D2 / T7: hoy overlay.py exige fase == InProgress
        self.assertTrue(visible()(estado(None, 1000, 1005), 1005))

    def test_d3_oculta_con_meta_de_31_segundos(self):  # D3 / T7: hoy partes() no limita la edad de la meta
        self.assertFalse(visible()(estado("InProgress", 1000, 1031), 1031))


class _Fin(BaseException): pass


class Reconnect(unittest.TestCase):
    def test_d10_reconnect_no_reinicia_avisado_ni_archivo(self):  # D10 / T9: hoy `elif not jugando` los reinicia
        fases = iter(["InProgress", "Reconnect", "InProgress"]); archivos, estados, cuenta = [], [], itertools.count()
        def lcu(ruta):
            try: return next(fases)
            except StopIteration: raise _Fin
        def capturar(a, d):
            a = a or f"f{next(cuenta)}"; archivos.append(a); return a
        def paso(d, estado, aj): estado["avisado"].add(len(estados)); estados.append(set(estado["avisado"])); return None, []
        with mock.patch.object(companion, "lcu", lcu), mock.patch.object(companion, "vivo", lambda: foto_practice()), \
             mock.patch.object(companion, "capturar", capturar), mock.patch.object(companion, "paso_vivo", paso), \
             mock.patch.object(companion_gui, "ajustes", lambda: {}), mock.patch.object(companion_gui, "SONDEO_VIVO", 0), \
             mock.patch.object(companion_gui.time, "sleep", lambda s: None):
            with self.assertRaises(_Fin): companion_gui.trabajador(mock.Mock())
        self.assertEqual(len(set(archivos)), 1, f"se abrieron {len(set(archivos))} archivos")
        self.assertEqual(len(estados), 2); self.assertTrue(estados[0] <= estados[1], "el segundo InProgress perdio los avisos ya dados")


def c_objetivo(dragon=None, baron=None, nivel=None, cs=None):
    """c como lo arma overlay.partes: clave -> (texto, color), más las de ayuda *_falta y abajo_nv."""
    c = {}
    if dragon is not None: c["dragon"], c["dragon_falta"] = (f"Dragón {overlay.reloj(dragon)}", overlay.TXT), dragon
    if baron is not None: c["baron"], c["baron_falta"] = (f"Barón {overlay.reloj(baron)}", overlay.TXT), baron
    if nivel is not None: c["nivel"], c["abajo_nv"] = (f"Nv {nivel} vs 13", overlay.TXT), False
    if cs is not None: c["cs"] = (f"CS {cs} vs 90", overlay.TXT)
    return c


class Elegir(unittest.TestCase):
    def test_minuto_1_sin_rival_muestra_el_dragon_proximo(self):
        """Falla hoy: sin piezas de linea ni regla, elegir devuelve [] y no el proximo objetivo."""
        self.assertEqual(overlay.elegir(c_objetivo(dragon=240), 1), [("Dragón 4:00", overlay.TXT)])


    def test_minuto_1_con_rival_no_agrega_el_dragon(self):
        """Con nivel y CS, el dragón a 240 s no está pronto y no se fuerza."""
        res = overlay.elegir(c_objetivo(nivel=14, cs=100, dragon=240), 1)
        self.assertEqual(len(res), 2)
        self.assertFalse(any(t.startswith(("Dragón", "! Dragón")) for t, _ in res))


    def test_sin_rival_y_objetivos_apagados_da_vacio(self):
        """Objetivos apagados: sin dragon/baron en c, el fallback no tiene qué mostrar."""
        self.assertEqual(overlay.elegir({}, 1), [])


    def test_aram_y_muerto_sin_cambio(self):
        """ARAM vuelve antes de elegir: el fallback no mete dragón/barón en ARAM ni con el jugador muerto."""
        meta = {"modo": "ARAM", "kills": [2, 3], "amenazas": [{"campeon": "Zed", "kda": "5/2/3"}], "kda": "1/2/3",
                "muerto": True, "objetivos": {"dragon": 240, "baron": None}}
        ps = overlay.partes(meta, 1000.0, {})
        self.assertFalse(any(t.startswith(("Dragón", "Barón", "! Dragón", "! Barón")) for t, _ in ps))
        self.assertEqual(ps[0][0], "▼ Kills 2 vs 3")
        self.assertTrue(any(t == "Tu KDA 1/2/3" for t, _ in ps))


if __name__ == "__main__": unittest.main()
