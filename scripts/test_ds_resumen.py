"""Pruebas de DeepSeek para score.resumen() (turno 5, iteración 13, afinada en la noche).

Cubre los bordes que pidió Opus: 0 partidas (tendencia [] y por_campeon {}), exactamente 20 partidas
(tendencia de un solo bloque) y `clave` en victorias/derrotas (con positivo/negativo claro, y con todos
los componentes del signo equivocado: ahí debe ser None). Los dos últimos quedan FALLANDO a propósito
hasta que Opus aplique `clave = None` cuando el extremo no tiene el signo del resultado."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HAY_DATOS = (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists()
if not HAY_DATOS:
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixture mínima
import score  # noqa: E402  (su _prueba() corre al importar, sin red ni archivos)


def g(win=True, comp=None, score_=50.0, champ="Yone", t=0):
    """Partida mínima con lo que `resumen` lee (comp en el orden de score.COMP)."""
    return dict(t=t, champ=champ, win=win, kda="1/2/3", score=score_, puesto=3, puesto_eq=2, linea=1,
                comp=comp if comp is not None else {c: 0.0 for c in score.COMP})


class Resumen(unittest.TestCase):
    def _resumen(self, gs):
        with mock.patch.object(score, "partidas", lambda raw=None: (gs, None, "yo")):
            return score.resumen()

    def test_sin_partidas(self):
        r = self._resumen([])
        self.assertEqual(r["tendencia"], [])
        self.assertEqual(r["por_campeon"], {})

    def test_20_partidas_tendencia_un_solo_valor(self):
        r = self._resumen([g(score_=55.0, t=i * 1000) for i in range(20)])
        self.assertEqual(len(r["tendencia"]), 1)     # un solo bloque de 20
        self.assertEqual(r["tendencia"][0], 55.0)

    def test_clave_victoria_con_positivo_da_el_mayor(self):
        comp = dict(daño=-0.5, oro=0.8, kp=0.3, muertes=-1.2, visión=0.4, cs=-0.9, objetivos=0.6, línea=-0.7)
        r = self._resumen([g(win=True, comp=comp, t=1)])
        self.assertEqual(r["partidas"][0]["clave"], ("oro", 0.8))

    def test_clave_derrota_con_negativo_da_el_menor(self):
        comp = dict(daño=-0.5, oro=0.8, kp=0.3, muertes=-1.2, visión=0.4, cs=-0.9, objetivos=0.6, línea=-0.7)
        r = self._resumen([g(win=False, comp=comp, t=1)])
        self.assertEqual(r["partidas"][0]["clave"], ("muertes", -1.2))

    def test_clave_victoria_todos_negativos_da_none(self):
        # nada te subió sobre tu rol: un «lo que más te subió» con z<0 engaña (propuesta: None).
        comp = dict(daño=-0.5, oro=-0.8, kp=-0.3, muertes=-1.0, visión=-0.4, cs=-0.9, objetivos=-0.6, línea=-0.7)
        r = self._resumen([g(win=True, comp=comp, t=1)])
        self.assertIsNone(r["partidas"][0]["clave"])

    def test_clave_derrota_todos_positivos_da_none(self):
        # nada te bajó sobre tu rol: un «lo que más te bajó» con z>0 engaña (propuesta: None).
        comp = dict(daño=0.5, oro=0.8, kp=0.3, muertes=1.0, visión=0.4, cs=0.9, objetivos=0.6, línea=0.7)
        r = self._resumen([g(win=False, comp=comp, t=1)])
        self.assertIsNone(r["partidas"][0]["clave"])


if __name__ == "__main__":
    unittest.main()
