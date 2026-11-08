"""Pruebas de DeepSeek para builds.py y draft.py (turno 5, iteración 7). Sin red ni key.

Cubre los bordes que pidió Opus: informe con los mejores sin ningún legendario (core vacío → sin `primer`),
guardado_dict con builds.json vacío (0 bytes) o con BOM (→ None, no truena) y datos_draft sin builds.json
(→ build_dict None y build [])."""
import json, os, pathlib, sys, tempfile, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HAY_DATOS = (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists()
if not HAY_DATOS:
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixture mínima para que draft.py importe
import builds  # noqa: E402
import draft   # noqa: E402

ITEMS = {"1055": dict(name="Espada de Doran", gold=dict(total=450), tags=[]),
         "3153": dict(name="Espada del Rey Arruinado", gold=dict(total=3200), tags=[])}


def build_sin_legendarios(win=True):
    # dict mínimo que `resumir`/`lineas` aceptan, con core vacío (partida corta, sin legendario)
    return dict(champ="Yone", pos="MIDDLE", win=win, core=[], botas=None,
                runas=(8000, 8008, (8008, 9111, 9104, 8299, 8400, 8444, 8453)), skills="Q>E>W")


def g(champ, win, opp="Zed", pos="MIDDLE"):
    return dict(win=win, champ=champ, pos=pos, opp=opp, enemies={opp}, gd14=0, t=0)


class Primer(unittest.TestCase):
    def test_informe_sin_legendarios_no_pone_primer(self):
        champs = {"yone": ("Yone", 777)}
        with mock.patch.object(builds, "ddragon", lambda: (ITEMS, {}, champs)), \
                mock.patch.object(builds, "mejores",
                                  lambda cid, nombre, pos=None: [(None, None, "top1", "Uno#KR1 (kr, 1000 LP)")]), \
                mock.patch.object(builds, "tuyas", lambda nombre, pos=None: [(None, None, "yo"), (None, None, "yo")]), \
                mock.patch.object(builds, "build_de", lambda m, t, u, items: build_sin_legendarios()):
            texto, rt, tu = builds.informe("Yone", "MIDDLE")
        self.assertNotIn("primer", rt)          # sin core en los mejores no hay primer ítem que comparar
        self.assertNotIn("Tu WR con", texto)    # y no sale la 4.ª línea

    def test_guardado_dict_vacio_o_con_bom_no_truena(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(builds, "META", pathlib.Path(tmp)):
            f = builds.META / "builds.json"
            f.write_text("", encoding="utf-8")                                   # 0 bytes
            self.assertIsNone(builds.guardado_dict("Yone", "MIDDLE"))
            f.write_text(chr(0xfeff) + '{"Yone|MIDDLE": {"n": 1}}', encoding="utf-8")  # BOM: json.loads lo rechaza
            self.assertIsNone(builds.guardado_dict("Yone", "MIDDLE"))            # sin build, pero no truena

    def test_datos_draft_sin_builds_json(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(builds, "META", pathlib.Path(tmp)), \
                mock.patch.object(draft, "games", [g("Ekko", True) for _ in range(5)]), \
                mock.patch.object(draft, "base", .5):
            d = draft.datos_draft("Zed", "MIDDLE")
        self.assertIsNone(d["build_dict"])
        self.assertEqual(d["build"], [])


if __name__ == "__main__":
    unittest.main()
