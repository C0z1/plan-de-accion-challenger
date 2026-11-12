"""dev_practica: nunca escribe al cliente fuera de None/Lobby, y --seco no escribe nada."""
import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import dev_practica as d


class Candado(unittest.TestCase):
    def test_se_niega_en_cola_o_partida(self):
        for fase in ("Matchmaking", "ReadyCheck", "ChampSelect", "InProgress", None):
            escrito = []
            self.assertFalse(d.main([], lcu=lambda p, f=fase: f, escribir=lambda *a: escrito.append(a) or True), fase)
            self.assertEqual(escrito, [], fase)

    def test_salir_solo_de_la_practica(self):  # en una partida real, early-exit sería abandonar (revisión del asistente)
        for (modo, sale), orden in ((x, o) for x in (("CLASSIC", False), ("ARAM", False), (None, False), ("PRACTICETOOL", True)) for o in ("salir", "reconectar")):
            escrito = []
            r = d.main([orden], lcu=lambda p, m=modo: {"phase": "InProgress", "gameData": {"queue": {"gameMode": m}}}, escribir=lambda *a: escrito.append(a) or True)
            self.assertEqual((r, bool(escrito)), (sale, sale), modo)

    def test_salir_solo_en_partida(self):  # hallazgo 18: modo de práctica en la sesión pero fuera de partida, no escribe
        for fase, sale in (("None", False), ("Lobby", False), ("InProgress", True), ("Reconnect", True)):
            escrito = []
            r = d.main(["reconectar"], lcu=lambda p, f=fase: {"phase": f, "gameData": {"queue": {"gameMode": "PRACTICETOOL"}}},
                       escribir=lambda *a: escrito.append(a) or True)
            self.assertEqual((r, bool(escrito)), (sale, sale), fase)

    def test_seco_no_escribe(self):
        escrito = []
        self.assertTrue(d.main(["--seco"], lcu=lambda p: "None" if p.endswith("phase") else None,
                               escribir=lambda *a: escrito.append(a) or True))
        self.assertEqual(escrito, [])


if __name__ == "__main__": unittest.main()
