"""Pruebas de DeepSeek para la caché de rendimiento, las rutas del .exe congelado y la
primera vez instalado (turno 8). Sin red ni ventanas; solo librería estándar."""
import importlib, json, os, pathlib, sys, tempfile, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import companion_gui as gui  # noqa: E402
import companion_web as web  # noqa: E402


def _raw(d, n):
    raw = pathlib.Path(d, "raw"); raw.mkdir()
    for i in range(n):
        (raw / f"LA1_{i}.json").write_text("{}")
    return raw


class Cache(unittest.TestCase):
    def test_borrar_partida_invalida(self):
        # turno 8 (a): borrar una partida cambia la firma (n) y recalcula, no sirve la caché vieja
        with tempfile.TemporaryDirectory() as d:
            raw, cache = _raw(d, 2), pathlib.Path(d, "c.json")
            with mock.patch.object(web, "rendimiento", return_value={"x": 1}) as r:
                web.rendimiento_rapido(raw, cache)
                (raw / "LA1_1.json").unlink()
                web.rendimiento_rapido(raw, cache)
            self.assertEqual(r.call_count, 2)

    def test_cache_json_corrupto_recalcula(self):
        # turno 8 (a): un JSON corrupto en la caché no truena: se ignora, recalcula y se reescribe
        with tempfile.TemporaryDirectory() as d:
            raw, cache = _raw(d, 1), pathlib.Path(d, "c.json")
            cache.write_text("{no es json", encoding="utf-8")
            with mock.patch.object(web, "rendimiento", return_value={"x": 1}) as r:
                self.assertEqual(web.rendimiento_rapido(raw, cache), {"x": 1})
            self.assertEqual(r.call_count, 1)
            self.assertEqual(json.loads(cache.read_text(encoding="utf-8"))["datos"], {"x": 1})

    def test_cambiar_score_py_invalida_la_cache(self):
        # turno 8 (a): un arreglo de score.py sin subir VERSION debe invalidar la caché (el mtime de score.py va en la firma)
        import score as score_mod
        with tempfile.TemporaryDirectory() as d:
            raw, cache = _raw(d, 1), pathlib.Path(d, "c.json")
            with mock.patch.object(web, "rendimiento", return_value={"media": 1}):
                web.rendimiento_rapido(raw, cache)
            f = pathlib.Path(score_mod.__file__); st = f.stat()
            try:
                os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))  # score.py "editado"
                with mock.patch.object(web, "rendimiento", return_value={"media": 2}):
                    self.assertEqual(web.rendimiento_rapido(raw, cache), {"media": 2})
            finally:
                os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns))  # dejar el mtime como estaba


class RepoCongelado(unittest.TestCase):
    """turno 8 (b): companion_gui.REPO cuando el .exe está congelado (sys.frozen)."""

    def tearDown(self):
        importlib.reload(gui)  # devolver REPO/RAW reales para no contaminar el resto de la suite

    def _repo(self, exe):
        with mock.patch.object(sys, "frozen", True, create=True), \
             mock.patch.object(sys, "executable", str(exe)):
            importlib.reload(gui)
            return gui.REPO

    def test_instalado_scripts_junto_al_exe(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d); (base / "scripts").mkdir()
            self.assertEqual(self._repo(base / "HTC.exe"), base)

    def test_dist_htc_repo_dos_arriba(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d); (base / "scripts").mkdir(); (base / "dist" / "HTC").mkdir(parents=True)
            self.assertEqual(self._repo(base / "dist" / "HTC" / "HTC.exe"), base)

    def test_sin_scripts_cae_a_la_carpeta_del_exe(self):
        with tempfile.TemporaryDirectory() as d:
            base = pathlib.Path(d); (base / "HTC").mkdir()
            self.assertEqual(self._repo(base / "HTC" / "HTC.exe"), base / "HTC")


class PrimeraVez(unittest.TestCase):
    def test_datos_dir_vacio_no_tumba(self):
        # turno 8 (e): instalación nueva (DATOS_DIR vacío): perfil, rendimiento_rapido y /api/estado no truenan
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(gui, "RAW", pathlib.Path(d)):  # perfil() lee RAW/perfil.json
                self.assertEqual(gui.perfil(), "sin historial todavía")
            with mock.patch.dict(os.environ, {"DATOS_DIR": d}), \
                 mock.patch.object(web, "CACHE", pathlib.Path(d, "cache.json")):
                self.assertIsNone(web.rendimiento_rapido())  # sin partidas: None, sin tronar
                web.refrescar()  # lo que corre el hilo al arrancar
                e = json.loads(web.estado())  # lo que sirve /api/estado
            self.assertIn("fase", e)
            self.assertIsNone(e["rendimiento"])


if __name__ == "__main__":
    unittest.main()
