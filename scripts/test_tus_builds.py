"""«Tu build» sin key: companion_web.tus_builds regenera builds.json solo si hay partidas más nuevas, y nunca truena."""
import os, pathlib, tempfile, time, unittest
from unittest import mock

import builds
import companion_web as w


class TestTusBuilds(unittest.TestCase):
    def correr(self, partida_nueva, con_json):
        with tempfile.TemporaryDirectory() as d:
            raw, meta = pathlib.Path(d) / "raw", pathlib.Path(d) / "meta"; raw.mkdir(); meta.mkdir()
            if con_json: (meta / "builds.json").write_text("{}"); time.sleep(0.05)
            if partida_nueva: (raw / "LA1_1.json").write_text("{}")
            if con_json and not partida_nueva: os.utime(meta / "builds.json")
            with mock.patch.dict(os.environ, {"DATOS_DIR": str(raw)}), mock.patch.object(builds, "META", meta), \
                    mock.patch.object(builds, "guardar_tuyas") as g:
                w.tus_builds(); return g.called

    def test_regenera_si_hay_partidas_nuevas(self):
        self.assertTrue(self.correr(partida_nueva=True, con_json=False))
        self.assertTrue(self.correr(partida_nueva=True, con_json=True))

    def test_no_regenera_sin_partidas(self):
        self.assertFalse(self.correr(partida_nueva=False, con_json=True))

    def test_un_fallo_no_truena(self):
        with mock.patch.object(builds, "guardar_tuyas", side_effect=ValueError("roto")), \
                mock.patch.dict(os.environ, {"DATOS_DIR": tempfile.gettempdir()}):
            w.tus_builds()


if __name__ == "__main__":
    unittest.main()
