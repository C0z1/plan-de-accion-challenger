"""Pruebas de vistas.errores: sin_pelea solo si tu equipo pierde la pelea, y un frame sin tu id no truena."""
import json, os, pathlib, sys, tempfile, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")

import vistas  # noqa: E402

# yo = 1 (equipo 100, con 3 y 4); rival 2 (equipo 200, con 5 y 6)
PARTS = [dict(participantId=i, teamId=t, teamPosition="MIDDLE" if i in (1, 2) else "TOP", championName=f"C{i}")
         for i, t in ((1, 100), (3, 100), (4, 100), (2, 200), (5, 200), (6, 200))]


def correr(frames):
    with tempfile.TemporaryDirectory() as d:
        raw = pathlib.Path(d); (raw / "timeline").mkdir()
        m = raw / "XX_1.json"
        m.write_text(json.dumps({"info": {"participants": PARTS}}), encoding="utf-8")
        (raw / "timeline" / m.name).write_text(json.dumps({"info": {"frames": frames}}), encoding="utf-8")
        return vistas.errores([dict(f=m, pid=1, champ="C1")], 20)


def pelea(victimas):
    return [{"events": [{"type": "CHAMPION_KILL", "timestamp": 900000 + k * 5000, "victimId": v, "killerId": 5 if v in (3, 4) else 3}
                        for k, v in enumerate(victimas)]}]


class SinPelea(unittest.TestCase):
    def test_solo_cuenta_si_tu_equipo_pierde(self):
        self.assertEqual(correr(pelea([3, 4, 5]))["partidas"]["sin_pelea"], 1)  # caen 2 tuyos y 1 rival: perdida
        self.assertEqual(correr(pelea([5, 6, 3]))["partidas"]["sin_pelea"], 0)  # la gana tu equipo sin ti: no es error

    def test_frame_sin_tu_id_no_truena(self):
        frames = [{"events": []} for _ in range(6)] + [{"events": [], "participantFrames": {"2": {"level": 6}}}]
        self.assertEqual(correr(frames)["partidas"]["abajo_6"], 0)


if __name__ == "__main__":
    unittest.main()
