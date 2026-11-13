"""Estela (0.18, PLAN-REINVENCION.md): reglas del CSS de la página leídas como texto. Solo se anima transform, opacity y
stroke-dashoffset; nada de backdrop-filter ni mix-blend-mode; reducir movimiento cubre ::after; sin URLs externas;
contraste AA de los colores de texto contra el peor fondo de tarjeta."""
import pathlib, re, unittest

HTML = (pathlib.Path(__file__).parent / "web" / "index.html").read_text(encoding="utf-8")
CSS = "\n".join(re.findall(r"<style>(.*?)</style>", HTML, re.S))


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


def mezcla(fondo, color, alfa):
    f, c = [int(fondo[i:i + 2], 16) for i in (1, 3, 5)], [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - alfa) + y * alfa):02x}" for x, y in zip(f, c))


class Estela(unittest.TestCase):
    def test_keyframes_solo_transform_opacity_dash(self):
        for nombre, cuerpo in re.findall(r"@keyframes\s+([\w-]+)\s*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", CSS):
            props = set(re.findall(r"([\w-]+)\s*:", re.sub(r"\d+%|from|to", "", cuerpo)))
            self.assertLessEqual(props, {"transform", "opacity", "stroke-dashoffset"}, f"@keyframes {nombre}: {props}")

    def test_sin_efectos_caros(self):
        self.assertNotIn("backdrop-filter", CSS); self.assertNotIn("mix-blend-mode", CSS)

    def test_transiciones_baratas(self):
        for t in re.findall(r"transition:([^;}]+)", CSS):
            if t.strip().startswith("none"): continue
            for parte in t.split(","):
                self.assertRegex(parte.strip(), r"^(transform|opacity|color|border-color|background-color)\b", t)

    def test_reducir_movimiento_cubre_after(self):
        self.assertIn(".quieto *::after", CSS)
        self.assertRegex(CSS, r"prefers-reduced-motion:reduce\)\{\*,\*::before,\*::after")
        self.assertIn(".enjuego *::after", CSS); self.assertIn(".oculta *::after", CSS)  # quieta en partida y oculta

    def test_tokens_y_presupuesto(self):
        for t in ("--e1:", "--e2:", "--e3:", "--e4:", "--estela:", "--vidrio:", "--sal:", "--pasa:"): self.assertIn(t, CSS)
        self.assertLessEqual(CSS.count("infinite"), 1)  # solo el cometa de carga: un bucle visible redibuja toda la ventana (15–20 % de CPU medido)

    def test_sin_urls_externas(self):
        self.assertEqual(re.findall(r"url\((?!['\"]?(data:|/|#|%23))[^)]*\)", CSS), [])
        self.assertNotRegex(HTML, r"(src|href)=\"https?://(?!127\.0\.0\.1)(?!github\.com/C0z1)")

    def test_contraste_aa(self):
        peor = mezcla("#44203A", "#F28DB0", .22)  # tope de tarjeta con la aurora rosa encima
        for var in ("--txt", "--muted", "--soft", "--e3", "--tealfg", "--redfg"):
            c = re.search(rf"{var}:(#[0-9A-Fa-f]{{6}})", CSS)[1]
            self.assertGreaterEqual(contraste(c, peor), 4.5, f"{var} {c} sobre {peor}")


if __name__ == "__main__":
    unittest.main()
