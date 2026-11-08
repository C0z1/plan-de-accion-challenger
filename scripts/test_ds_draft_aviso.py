"""Pruebas de DeepSeek para draft.datos_draft / draft.avisos (turno 4, iteración 4). Sin red ni datos reales."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo, como test_draft
import draft


def g(champ, win, opp="Zed", pos="MIDDLE"):
    return dict(win=win, champ=champ, pos=pos, opp=opp, enemies={opp}, gd14=0, t=0)


class AvisoDraft(unittest.TestCase):
    def datos(self, juegos, rival, pos="MIDDLE"):
        with mock.patch.object(draft, "games", juegos), mock.patch.object(draft, "base", .5):
            return draft.datos_draft(rival, pos)

    def test_todos_counter_duro_sin_alternativa(self):
        # Ekko (0-4 vs Viktor) y Yone (0-4 vs Viktor): techo Wilson 49% < base 50% en ambos.
        js = [g("Ekko", True) for _ in range(30)] + [g("Ekko", False, "Viktor") for _ in range(4)]
        js += [g("Yone", True) for _ in range(10)] + [g("Yone", False, "Viktor") for _ in range(4)]
        d = self.datos(js, "Viktor")
        self.assertTrue(d["filas"][0]["counter"])
        self.assertTrue(all(f["counter"] for f in d["filas"]))
        self.assertTrue(any("Ningún otro de tu pool lo evita" in a for a in d["avisos"]))

    def test_un_solo_campeon_con_2_partidas_sin_alternativa(self):
        js = [g("Yone", True, pos="TOP") for _ in range(2)]
        d = self.datos(js, "Zed", "TOP")
        self.assertTrue(any("No tienes otro con más partidas" in a for a in d["avisos"]))

    def test_rival_desconocido_no_marca_counter_ni_truena(self):
        js = [g("Ekko", True) for _ in range(6)]
        d = self.datos(js, "Nadie")
        self.assertFalse(d["conocido"])
        self.assertEqual(d["avisos"], [])


if __name__ == "__main__":
    unittest.main()
