"""Pruebas sintéticas de metodo/robustez.py: sin edge no debe aprobar, con edge sí."""
import numpy as np
import pandas as pd
import unittest

from metodo.robustez import dsr, min_trl, pbo, psr, spa, sr_esperado_maximo, matriz_diaria

DIAS = pd.bdate_range("2018-01-01", periods=1500)


def _matriz(n_var=30, edge=0.0, rho=0.6, semilla=0):
    """Variantes correladas (como parámetros vecinos), R diario ~ N(0,1); la variante 0 lleva edge."""
    rng = np.random.default_rng(semilla)
    comun = rng.standard_normal((len(DIAS), 1))
    m = np.sqrt(rho) * comun + np.sqrt(1 - rho) * rng.standard_normal((len(DIAS), n_var))
    m[:, 0] += edge
    return pd.DataFrame(m, index=DIAS, columns=[f"v{i}" for i in range(n_var)])


class TestRobustez(unittest.TestCase):
    def test_spa_sin_edge_no_aprueba(self):
        ps = [spa(_matriz(semilla=s), reps=500)["p_spa"] for s in range(6)]
        assert sum(p <= 0.05 for p in ps) <= 1

    def test_spa_con_edge_aprueba_y_stepm_la_encuentra(self):
        r = spa(_matriz(edge=0.12), reps=1000)
        assert r["p_spa"] <= 0.05
        assert "v0" in r["superiores"]

    def test_pbo_sin_edge_cerca_de_la_mitad(self):
        assert 0.25 <= pbo(_matriz(), s=10)["pbo"] <= 0.75

    def test_pbo_con_edge_bajo(self):
        assert pbo(_matriz(edge=0.15), s=10)["pbo"] <= 0.1

    def test_psr_y_min_trl(self):
        rng = np.random.default_rng(1)
        r = rng.standard_normal(5000) * 1.0 + 0.05  # Sharpe 0,05 por operación
        assert psr(r) > 0.95
        n = min_trl(r)
        sr = r.mean() / r.std(ddof=1)  # con datos normales MinTRL ≈ 1 + (1 + SR²/2)·(1,645/SR)²
        self.assertAlmostEqual(n / (1 + (1 + sr ** 2 / 2) * (1.6449 / sr) ** 2), 1.0, delta=0.05)
        assert min_trl(-r) == float("inf")

    def test_dsr_castiga_buscar_mucho(self):
        rng = np.random.default_rng(2)
        r = rng.standard_normal(1000) + 0.08
        assert dsr(r, 1) > dsr(r, 1000)
        assert sr_esperado_maximo(1, 0.01) == 0.0

    def test_matriz_diaria_rellena_ceros(self):
        a = pd.DataFrame({"fecha": ["2020-01-01", "2020-01-01", "2020-01-03"], "r": [1.0, -0.5, 2.0]})
        b = pd.DataFrame({"fecha": ["2020-01-02"], "r": [1.0]})
        m = matriz_diaria({"a": a, "b": b})
        assert m.loc["2020-01-01", "a"] == 0.5 and m.loc["2020-01-01", "b"] == 0.0
        assert m.shape == (3, 2)

    def test_embudo_con_variantes(self):
        from metodo.embudo import embudo
        m = _matriz(edge=0.12)
        ops = pd.DataFrame({"fecha": m.index, "r_bruto": m.v0 + 0.02, "coste_r": 0.02})
        res = embudo(ops, n_pruebas=30, corte_oos="2022-01-01", variantes=m)
        nombres = [p[0] for p in res.puertas]
        assert "SPA mejor de N" in nombres and "PBO (CSCV)" in nombres


if __name__ == "__main__":
    unittest.main()
