import os
import tempfile
import unittest

import numpy as np
import pandas as pd

from metodo.comparar_ops import cargar_mt5, comparar
from metodo.hooks.compilar_mq5 import leer_log, resumir


def _py(n=200, semilla=0):
    rng = np.random.default_rng(semilla)
    horas = pd.bdate_range("2024-01-01", periods=n) + pd.Timedelta(hours=16, minutes=40)
    return pd.DataFrame({"hora": horas, "lado": rng.choice([1, -1], n),
                         "r": np.where(rng.random(n) < 0.4, 2.0, -1.0)})


class TestComparar(unittest.TestCase):
    def test_iguales_coinciden(self):
        py = _py()
        mt = py.copy()
        mt["hora"] += pd.Timedelta(minutes=1)
        mt["r"] += 0.02
        c = comparar(py, mt)
        self.assertTrue(c.pasa, str(c))
        self.assertEqual(len(c.pares), 200)

    def test_lado_en_texto_en_mt5(self):
        # un DataFrame de MT5 con "LONG"/"SHORT" (sin pasar por cargar_mt5) debe emparejar igual
        py = _py()
        mt = py.copy()
        mt["lado"] = np.where(mt.lado > 0, "LONG", "SHORT")
        c = comparar(py, mt)
        self.assertTrue(c.pasa, str(c))
        self.assertEqual(len(c.pares), 200)

    def test_desfase_horario_no_empareja(self):
        py = _py()
        mt = py.copy()
        mt["hora"] += pd.Timedelta(hours=7)          # Python en hora NY, MT5 en hora servidor
        self.assertFalse(comparar(py, mt).pasa)
        self.assertTrue(comparar(py, mt, desfase="7h").pasa)

    def test_errores_compensados_se_detectan(self):
        # misma media y mismas ops, pero un 30 % de R cambiadas entre sí: la media engaña
        py = _py()
        mt = py.copy()
        idx = mt.sample(frac=0.3, random_state=1).index
        mt.loc[idx, "r"] = mt.loc[idx, "r"].sample(frac=1, random_state=2).to_numpy()
        c = comparar(py, mt)
        self.assertFalse(c.pasa, str(c))

    def test_carga_csv_orb(self):
        txt = ("Fecha;Hora;Simbolo;Lado;Lotes;PrecioEntrada;PrecioSalida;Salida;StopPts;RiesgoPct;"
               "RiesgoDinero;PnL_bruto;Comision;Swap;PnL_neto;R;SlipEntradaPts;SlipSalidaPts;SlipPctStop;PF_movil;Balance\n"
               "2026.11.10;17:05;US100.cash;LONG;0.5;21000.0;21050.0;TP;2000;1.00;100;50;-1;0;49;0.500;1;0;0.1;1.2;10049\n")
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write(txt)
        try:
            d = cargar_mt5(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(d.lado.iloc[0], 1)
        self.assertAlmostEqual(d.r.iloc[0], 0.5)
        self.assertEqual(d.hora.iloc[0], pd.Timestamp("2026-11-10 17:05"))

    def test_carga_csv_plantilla(self):
        txt = ("cierre;posicion;tipo;volumen;precio;beneficio;comision;swap;apertura;precio_entrada;sl_inicial;r_bruto\n"
               "2026.11.10 18:00:00;7;cierra_corto;0.1;99.0;10;0;0;2026.11.10 17:00:00;100.0;101.0;1.000\n")
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write(txt)
        try:
            d = cargar_mt5(f.name)
        finally:
            os.unlink(f.name)
        self.assertEqual(d.lado.iloc[0], -1)
        self.assertEqual(d.hora.iloc[0], pd.Timestamp("2026-11-10 17:00"))


class TestLogMetaEditor(unittest.TestCase):
    def test_log_utf16(self):
        log = ("C:\\MT5_Lab\\MQL5\\Experts\\x.mq5(12,5) : error 256: undeclared identifier 'foo'\r\n"
               "C:\\MT5_Lab\\MQL5\\Experts\\x.mq5(20,1) : warning 43: possible loss of data\r\n"
               "Result: 1 errors, 1 warnings, 234 msec elapsed\r\n")
        with tempfile.NamedTemporaryFile("wb", suffix=".log", delete=False) as f:
            f.write(b"\xff\xfe" + log.encode("utf-16-le"))
        try:
            err, warn, lineas = resumir(leer_log(f.name))
        finally:
            os.unlink(f.name)
        self.assertEqual((err, warn, len(lineas)), (1, 1, 2))

    def test_log_limpio_en_espanol(self):
        self.assertEqual(resumir("Resultado: 0 errores, 0 advertencias, 100 msec")[:2], (0, 0))


if __name__ == "__main__":
    unittest.main()
