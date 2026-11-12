"""Ventana nueva (Edge --app con perfil propio, sin tocar el marco) y búsqueda del cliente de LoL fuera de C:\\Riot Games."""
import os, pathlib, tempfile, threading, unittest
from unittest import mock

import companion
import ventana


class Proc:
    def __init__(self, vivo=True): self.pid, self.vivo, self.terminado = 1234, vivo, False
    def poll(self): return None if self.vivo else 0
    def terminate(self): self.terminado = True


class TestVentana(unittest.TestCase):
    def setUp(self): self.orig = ventana.PROC[0]
    def tearDown(self): ventana.PROC[0] = self.orig

    def test_con_ventana_viva_no_abre_otra(self):
        ventana.PROC[0] = Proc()
        with mock.patch.object(ventana, "ventanas", return_value=[99]), mock.patch.object(ventana, "_win", return_value=(None, None, mock.Mock(), None)), \
                mock.patch("subprocess.Popen") as p:
            self.assertTrue(ventana.abrir("http://127.0.0.1:1/", "perfil")); p.assert_not_called()

    def test_abre_con_perfil_propio_y_barra_oscura(self):
        ventana.PROC[0] = None
        with mock.patch.object(ventana, "edge", return_value="msedge"), mock.patch.object(ventana, "_al_job"), \
                mock.patch("subprocess.Popen", return_value=Proc()) as p:
            self.assertTrue(ventana.abrir("http://127.0.0.1:1/", "C:/x/datos/edge"))
        args = p.call_args[0][0]
        for a in ("--app=http://127.0.0.1:1/", "--user-data-dir=C:/x/datos/edge", "--force-dark-mode"): self.assertIn(a, args)

    def test_dos_a_la_vez_una_sola(self):  # abrir a mano y champ select al mismo tiempo
        ventana.PROC[0] = None
        def popen(*a, **k): ventana.PROC[0] = Proc(); return ventana.PROC[0]
        with mock.patch.object(ventana, "edge", return_value="msedge"), mock.patch.object(ventana, "_al_job"), \
                mock.patch.object(ventana, "ventanas", return_value=[99]), mock.patch.object(ventana, "_win", return_value=(None, None, mock.Mock(), None)), \
                mock.patch("subprocess.Popen", side_effect=popen) as p:
            hs = [threading.Thread(target=ventana.abrir, args=("u", "p")) for _ in range(5)]
            for h in hs: h.start()
            for h in hs: h.join()
        self.assertEqual(p.call_count, 1)

    def test_sin_edge(self):
        ventana.PROC[0] = None
        with mock.patch.object(ventana, "edge", return_value=None): self.assertFalse(ventana.abrir("u", "p"))

    def test_cerrar(self):
        ventana.PROC[0] = None; ventana.cerrar()  # sin ventana no truena
        ventana.PROC[0] = pr = Proc(); ventana.cerrar(); self.assertTrue(pr.terminado)

    def test_limpiar_viejas_no_truena(self):
        self.assertGreaterEqual(ventana.limpiar_viejas(), 0)

    def test_pagina_sin_barra_propia(self):
        html = (pathlib.Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")
        for x in ("barra-v", "sin_marco", "recortar", "/api/ventana"): self.assertNotIn(x, html)


class TestLockfile(unittest.TestCase):
    def setUp(self): self.orig = companion.LOCK, companion.AUTO[0], companion._BUSCADO[0]
    def tearDown(self): companion.LOCK, companion.AUTO[0], companion._BUSCADO[0] = self.orig

    def test_lol_en_otro_disco(self):  # 2026-11-12: el amigo con LoL fuera de C:\Riot Games no veía su cliente
        with tempfile.TemporaryDirectory() as t:
            lol = pathlib.Path(t, "Juegos", "LoL"); lol.mkdir(parents=True); (lol / "lockfile").write_text("x:1:2:pw:https")
            meta = pathlib.Path(t, "Riot Games", "Metadata", "league_of_legends.live"); meta.mkdir(parents=True)
            (meta / "league_of_legends.live.product_settings.yaml").write_text(f'product_install_full_path: "{lol.as_posix()}"\n')
            companion.LOCK = companion.AUTO[0] = pathlib.Path(t, "no", "lockfile"); companion._BUSCADO[0] = 0
            env = {k: v for k, v in os.environ.items() if k != "LOL_LOCKFILE"} | {"PROGRAMDATA": t}
            with mock.patch.dict(os.environ, env, clear=True): self.assertEqual(companion._lock(), lol / "lockfile")

    def test_lock_puesto_a_mano_no_se_toca(self):  # las pruebas que apuntan LOCK a un archivo propio
        companion.LOCK = pathlib.Path("no-existe.lockfile"); companion._BUSCADO[0] = 0
        self.assertEqual(companion._lock(), pathlib.Path("no-existe.lockfile"))


if __name__ == "__main__":
    unittest.main()
