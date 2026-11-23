import unittest

import pandas as pd

from metodo.exportar_mt5 import operaciones

T0 = int(pd.Timestamp("2026-11-06 14:30").timestamp())


def _deals():
    # depósito, y la operación real del 6-11 (largo US100.cash, 0,87 lotes, stop 114,38 puntos de precio)
    return pd.DataFrame([
        dict(ticket=1, order=0, time=T0 - 86400 * 30, type=2, entry=0, position_id=0, magic=0, symbol="",
             volume=0, price=0, profit=10000.0, commission=0, swap=0, fee=0),
        dict(ticket=2, order=10, time=T0, type=0, entry=0, position_id=500, magic=7, symbol="US100.cash",
             volume=0.87, price=27126.78, profit=0, commission=0, swap=0, fee=0),
        dict(ticket=3, order=11, time=T0 + 3600, type=1, entry=1, position_id=500, magic=7, symbol="US100.cash",
             volume=0.87, price=27019.93, profit=-92.96, commission=0, swap=0, fee=0),
        # otra posición, corta, cerrada en ganancia con comisión
        dict(ticket=4, order=12, time=T0 + 86400, type=1, entry=0, position_id=501, magic=7, symbol="US100.cash",
             volume=1.0, price=27000.0, profit=0, commission=-1.0, swap=0, fee=0),
        dict(ticket=5, order=13, time=T0 + 86400 + 600, type=0, entry=1, position_id=501, magic=7, symbol="US100.cash",
             volume=1.0, price=26800.0, profit=200.0, commission=-1.0, swap=0, fee=0),
    ])


def _ordenes():
    return pd.DataFrame([
        dict(ticket=10, time_setup=T0, position_id=500, sl=27126.78 - 114.38),
        dict(ticket=11, time_setup=T0 + 3600, position_id=500, sl=0.0),
        dict(ticket=12, time_setup=T0 + 86400, position_id=501, sl=27100.0),
        dict(ticket=13, time_setup=T0 + 86400 + 600, position_id=501, sl=0.0),
    ])


class TestExportarMT5(unittest.TestCase):
    def test_r_como_el_informe_del_ea(self):
        ops = operaciones(_deals(), _ordenes(), simbolo="US100.cash")
        self.assertEqual(len(ops), 2)
        a = ops.iloc[0]
        self.assertEqual(a.lado, "largo")
        self.assertAlmostEqual(a.r_bruta, -0.934, places=3)  # el informe diario del 6-11 dice −0,934
        self.assertAlmostEqual(a.R, -0.934, places=3)        # sin costes
        b = ops.iloc[1]
        self.assertEqual(b.lado, "corto")
        self.assertAlmostEqual(b.r_bruta, 2.0)               # 200 puntos a favor / stop de 100
        self.assertAlmostEqual(b.R, 2.0 - 2.0 / 100)         # 2 $ de comisión con 1 $/punto → 0,02 R

    def test_respaldo_por_riesgo_pct(self):
        ops = operaciones(_deals(), pd.DataFrame(), simbolo="US100.cash", riesgo_pct=1.0)
        self.assertAlmostEqual(ops.iloc[0].R, -92.96 / 100.0, places=4)  # 1 % de 10.000
        self.assertEqual(operaciones(_deals(), pd.DataFrame()).shape[0], 0)  # sin stop ni respaldo: no inventa R

    def test_filtros_y_posicion_abierta(self):
        d = _deals()
        d = d[d.ticket != 5]  # la segunda posición sigue abierta
        self.assertEqual(len(operaciones(d, _ordenes(), simbolo="US100.cash")), 1)
        self.assertEqual(len(operaciones(_deals(), _ordenes(), magic=99)), 0)


if __name__ == "__main__":
    unittest.main()
