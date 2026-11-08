"""Pruebas de DeepSeek para builds.por_primer() (turno 5, iteración 11). Sin red ni key.

Cubre los bordes que pidió Opus: empate en n entre dos ítems (orden estable y ambos salen), un id
que no está en `items` (sale el id como nombre) e `informe` con 4 partidas tuyas (no sale la línea
«por primer ítem» porque el mínimo es 5)."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HAY_DATOS = (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists()
if not HAY_DATOS:
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixture mínima
import builds  # noqa: E402

ITEMS = {"3153": dict(name="Rey Arruinado", gold=dict(total=3200), tags=[])}
PERKS = (8000, 8008, (8008, 9111, 9104, 8299, 8400, 8444, 8453))


def b(core, win=True):
    """dict mínimo de build que `resumir`/`lineas`/`por_primer` aceptan."""
    return dict(champ="Yone", pos="MIDDLE", win=win, core=core, botas=None, runas=PERKS, skills="Q>E>W")


class PorPrimer(unittest.TestCase):
    def test_empate_en_n_orden_estable_y_ambos_salen(self):
        bs = [b(["1"])] * 5 + [b(["2"])] * 5
        pp = builds.por_primer(bs, {"1": {"name": "Uno"}, "2": {"name": "Dos"}})
        self.assertEqual([(nm, len(v)) for nm, v in pp], [("Uno", 5), ("Dos", 5)])  # estable: el orden de 1.ª aparición

    def test_id_desconocido_sale_el_id(self):
        pp = builds.por_primer([b(["xyz"])] * 5, ITEMS)  # "xyz" no está en items
        self.assertEqual([(nm, len(v)) for nm, v in pp], [("xyz", 5)])

    def test_informe_con_4_partidas_no_saca_por_primer(self):
        champs = {"yone": ("Yone", 777)}
        with mock.patch.object(builds, "ddragon", lambda: (ITEMS, {}, champs)), \
                mock.patch.object(builds, "mejores", lambda cid, nombre, pos=None: []), \
                mock.patch.object(builds, "tuyas", lambda nombre, pos=None: [(None, None, "yo")] * 4), \
                mock.patch.object(builds, "build_de", lambda m, t, u, items: b(["3153"])):
            texto, rt, tu = builds.informe("Yone", "MIDDLE")
        self.assertNotIn("por primer ítem", texto)  # 4 < 5: la línea no sale
        self.assertIsNotNone(tu)                    # pero tu build sí


if __name__ == "__main__":
    unittest.main()
