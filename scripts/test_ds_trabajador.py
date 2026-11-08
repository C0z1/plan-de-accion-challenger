"""Pruebas de DeepSeek para companion_gui.trabajador (turno 5, iteración 10). Sin red ni ventana.

Cubre lo que pidió Opus: (1) el error cambia de texto entre vueltas → salen los dos; (2) error, vuelta sin error,
el mismo error → sale 2 veces; (3) `lcu` que lanza siempre → las esperas crecen 6, 12, 24 (espera(1..3); la de 3 s
es con fallos=0, o sea una vuelta con el cliente arriba, que aquí nunca ocurre)."""
import queue, sys, unittest

AQUI = __import__("pathlib").Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import companion_gui as g  # noqa: E402


def dormidor(vueltas, guarda=None):
    """time.sleep falso: guarda el argumento y corta el bucle con KeyboardInterrupt al acabarse vueltas."""
    def dormir(s):
        if next(vueltas, None) is None: raise KeyboardInterrupt
        if guarda is not None: guarda.append(s)
    return dormir


class Trabajador(unittest.TestCase):
    def test_error_distinto_entre_vueltas_sale_dos_veces(self):
        c, q = g.companion, queue.Queue()
        orig = c.lcu, c.vivo, g.time.time, g.time.sleep
        vueltas = iter(range(3))  # 3 vueltas completas y corta en la 4.ª
        errores = iter([ValueError("uno"), ValueError("dos"), ValueError("dos")])  # la 3.ª repite: no suma aviso
        def vivo_roto():
            raise next(errores)
        reloj = iter(range(0, 10_000, 100))
        c.lcu, c.vivo = (lambda path: "InProgress"), vivo_roto
        g.time.time, g.time.sleep = (lambda: next(reloj)), dormidor(vueltas)
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, c.vivo, g.time.time, g.time.sleep = orig
        avisos = [e[1]["texto"] for e in list(q.queue) if e[0] == "aviso"]
        self.assertEqual(len(avisos), 2); self.assertIn("uno", avisos[0]); self.assertIn("dos", avisos[1])

    def test_error_limpio_mismo_error_sale_dos_veces(self):
        c, q = g.companion, queue.Queue()
        orig = c.lcu, c.vivo, g.time.time, g.time.sleep
        vueltas = iter(range(4))  # 4 vueltas: error, limpia, mismo error, y una más que ya no suma
        secuencia = iter([("err", "uno"), ("ok", None), ("err", "uno"), ("err", "uno")])
        def vivo_raro():
            tipo, val = next(secuencia)
            if tipo == "err": raise ValueError(val)
            return val
        reloj = iter(range(0, 10_000, 100))
        c.lcu, c.vivo = (lambda path: "InProgress"), vivo_raro
        g.time.time, g.time.sleep = (lambda: next(reloj)), dormidor(vueltas)
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, c.vivo, g.time.time, g.time.sleep = orig
        avisos = [e[1]["texto"] for e in list(q.queue) if e[0] == "aviso"]
        self.assertEqual(avisos, [e for e in avisos if "uno" in e]); self.assertEqual(len(avisos), 2)

    def test_lcu_que_lanza_siempre_crece_la_espera(self):
        c, q = g.companion, queue.Queue()
        orig = c.lcu, g.time.sleep
        segundos = []
        c.lcu, g.time.sleep = (lambda path: 1 / 0), dormidor(iter(range(3)), segundos)
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, g.time.sleep = orig
        self.assertEqual(segundos, [6, 12, 24])  # fallos 1, 2, 3: espera(1)=6, (2)=12, (3)=24


if __name__ == "__main__":
    unittest.main()
