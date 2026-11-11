"""Racha: prototipos de sonidos (solo stdlib). Uso: python generar.py -> escribe los .wav junto al script.
44.1 kHz, mono, 16 bit, pico -12 dBFS, ataque/liberacion suaves (sin clics). Ver propuesta.md."""
import math, struct, wave, os

SR, PICO = 44100, 10 ** (-12 / 20)  # -12 dBFS
AQUI = os.path.dirname(os.path.abspath(__file__))


def nota(f, ms, ataque=12, rel=None, tri=0.0, f_fin=None, decae=0.0):
    """Una nota: seno (+ algo de triangulo) con ataque coseno, liberacion coseno y caida exponencial opcional."""
    n = int(SR * ms / 1000); a = int(SR * ataque / 1000); r = int(SR * (rel if rel is not None else ms * 0.6) / 1000)
    out, fase = [], 0.0
    for i in range(n):
        fi = f if f_fin is None else f + (f_fin - f) * i / n
        fase += 2 * math.pi * fi / SR
        s = math.sin(fase)
        if tri: s = (1 - tri) * s + tri * (2 / math.pi) * math.asin(math.sin(fase))
        e = 1.0
        if i < a: e = 0.5 - 0.5 * math.cos(math.pi * i / a)
        if i > n - r: e *= 0.5 + 0.5 * math.cos(math.pi * (i - (n - r)) / r)
        out.append(s * e * math.exp(-decae * i / SR))
    return out


def mezcla(*partes):
    """partes = (inicio_ms, muestras): las suma en una sola pista."""
    n = max(int(SR * ms / 1000) + len(m) for ms, m in partes); out = [0.0] * n
    for ms, m in partes:
        o = int(SR * ms / 1000)
        for i, x in enumerate(m): out[o + i] += x
    return out


def guardar(nombre, muestras):
    pico = max(abs(x) for x in muestras) or 1
    datos = b"".join(struct.pack("<h", int(x / pico * PICO * 32767)) for x in muestras)
    with wave.open(os.path.join(AQUI, nombre), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(datos)


# Notas (Hz)
E5, G5, A5, B5, D6, E6 = 659.26, 783.99, 880.0, 987.77, 1174.66, 1318.51
C5, D5, A4, E4 = 523.25, 587.33, 440.0, 329.63

SONIDOS = {
    # franja en partida: una sola gota grave-media, 150 ms, sin brillo (lo mas discreto de todo)
    "aviso.wav": nota(A4, 150, ataque=15, rel=110, tri=0.0, f_fin=A4 * 0.97),
    # pico del rival: dos notas bajando suave (A4 -> E4), tono de «ojo» sin alarma; opcion, sustituye a aviso
    "pico.wav": mezcla((0, nota(A4, 130, 12, 90)), (130, nota(E4, 190, 12, 150))),
    # champ select listo: dos notas subiendo (E5 -> B5), 340 ms
    "listo.wav": mezcla((0, nota(E5, 150, 14, 100, tri=0.15)), (140, nota(B5, 260, 14, 210, tri=0.15, decae=3))),
    # fin de partida / 3 momentos: arpegio suave E5 G5 B5 con cola, 760 ms
    "fin.wav": mezcla((0, nota(E5, 300, 15, 220, decae=4)), (170, nota(G5, 300, 15, 220, decae=4)), (340, nota(B5, 420, 15, 340, decae=5))),
    # actualizacion instalada: quinta ascendente D5 -> A5, 420 ms
    "actualizado.wav": mezcla((0, nota(D5, 170, 14, 120, tri=0.1)), (150, nota(A5, 270, 14, 220, tri=0.1, decae=3))),
    # reporte enviado: dos toques agudos muy cortos, 230 ms
    "enviado.wav": mezcla((0, nota(B5, 80, 8, 60)), (90, nota(E6, 140, 8, 110, decae=4))),
    # clic de interruptor: toque seco y suave, 45 ms
    "clic.wav": nota(1320, 45, ataque=5, rel=38, tri=0.3, decae=20),
}

if __name__ == "__main__":
    for n, m in SONIDOS.items():
        guardar(n, m)
        with wave.open(os.path.join(AQUI, n)) as w:
            x = struct.unpack(f"<{w.getnframes()}h", w.readframes(w.getnframes()))
            print(f"{n:16s} {1000 * w.getnframes() / w.getframerate():6.0f} ms  pico {20 * math.log10(max(map(abs, x)) / 32767):6.1f} dBFS  "
                  f"extremos {x[0]},{x[-1]}  {w.getframerate()} Hz {w.getnchannels()}ch {8 * w.getsampwidth()}bit")
