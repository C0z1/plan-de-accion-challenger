import os
from PIL import Image, ImageDraw
os.chdir(os.path.dirname(os.path.abspath(__file__)))
B = [(34, 150, 56, "#A33A63"), (80, 114, 92, "#F28DB0"), (126, 78, 128, "#F8C3D6"), (172, 42, 164, "#A8D8C0")]
S = (16, 24, 32, 48, 64, 128, 256)


def draw(n, k=8):
    s = n * k / 256
    im = Image.new("RGBA", (n * k, n * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8 * s, 8 * s, 248 * s - 1, 248 * s - 1], 56 * s, fill="#24111A")
    for x, y, h, c in B:
        d.rounded_rectangle([x * s, y * s, (x + 38) * s - 1, (y + h) * s - 1], 9 * s, fill=c)
    return im.resize((n, n), Image.LANCZOS)


for n in S:
    draw(n).save(f"racha-{n}.png")
draw(256).save("racha.ico", sizes=[(n, n) for n in S])
