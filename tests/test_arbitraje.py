import unittest

from arbitraje_segunda_mano.app import catalogo
from arbitraje_segunda_mano.app.catalogo import Modelo, alarmas, identificar, normalizar
from arbitraje_segunda_mano.app.puntuacion import (CANALES, Canal, Parametros, evaluar,
                                                   precio_maximo)


def modelo(**kw):
    base = dict(id="x", categoria="c", nombre="X", palabras_clave=["x"], mediana_usado=500.0)
    base.update(kw)
    return Modelo(**base)


class NormalizarTests(unittest.TestCase):
    def test_variantes_de_ps5(self):
        for t in ("PS 5", "ps5", "Ps-5", "PS5!"):
            self.assertEqual(normalizar(t), "ps5")

    def test_acentos_y_objetivos(self):
        self.assertEqual(normalizar("Cámara Sony 85mm f/1.8"), "camara sony85 1 8")


class CatalogoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modelos = catalogo.cargar()

    def test_catalogo_carga_y_ids_unicos(self):
        ids = [m.id for m in self.modelos]
        self.assertGreaterEqual(len(ids), 10)
        self.assertEqual(len(ids), len(set(ids)))

    def test_ps5_digital_frente_a_lector(self):
        self.assertEqual(identificar("PS 5 slim digital 1TB", self.modelos).id, "ps5-slim-digital")
        self.assertEqual(identificar("PS5 Slim con lector + 2 mandos", self.modelos).id,
                         "ps5-slim-disco")
        self.assertEqual(identificar("PS5 Pro como nueva", self.modelos).id, "ps5-pro")

    def test_camaras(self):
        self.assertEqual(identificar("Sony Alpha A7 III cuerpo", self.modelos).id, "sony-a7-iii")
        self.assertEqual(identificar("Sony A7 IV body", self.modelos).id, "sony-a7-iv")
        self.assertEqual(identificar("Sony FE 85mm f/1.8", self.modelos).id, "sony-85-18")
        self.assertIsNone(identificar("Sony FE 85mm f/1.4 GM", self.modelos))

    def test_fuera_de_catalogo(self):
        self.assertIsNone(identificar("Bicicleta de montaña", self.modelos))


class AlarmasTests(unittest.TestCase):
    def test_graves_y_leves(self):
        a = alarmas("PS5 para piezas, sin factura")
        self.assertIn("para piezas", a["graves"])
        self.assertIn("sin factura", a["leves"])

    def test_no_confunde_palabras_parecidas(self):
        self.assertEqual(alarmas("Funcionamiento comprobado, perfecta")["graves"], [])

    def test_accesorio(self):
        self.assertTrue(alarmas("Mando PS5 DualSense")["graves"])


class PuntuacionTests(unittest.TestCase):
    def test_margen_a_mano(self):
        p = Parametros(embalaje=3, reacondicionado=5, p_problema=0.0)
        r = evaluar(300, modelo(), CANALES["wallapop"], envio_compra=5, p=p)
        # 500 − 3 − 5 − 305 = 187
        self.assertAlmostEqual(r.margen_neto, 187.0)
        self.assertTrue(r.comprar)

    def test_comision_y_riesgo(self):
        canal = Canal("t", comision_pct=0.10, comision_fija=1.0, envio_vendedor=4.0)
        p = Parametros(embalaje=0, reacondicionado=0, p_problema=0.1)
        r = evaluar(300, modelo(precio_suelo=250.0), canal, p=p)
        # 500·0.9 − 1 − 4 − 0.1·(300−250) − 300 = 140
        self.assertAlmostEqual(r.margen_neto, 140.0)

    def test_alarma_grave_bloquea(self):
        r = evaluar(100, modelo(), CANALES["wallapop"], alarmas={"graves": ["icloud"], "leves": []})
        self.assertFalse(r.comprar)

    def test_rotacion_lenta_bloquea(self):
        r = evaluar(100, modelo(dias_venta=60.0), CANALES["wallapop"])
        self.assertFalse(r.comprar)

    def test_sin_mediana_no_decide(self):
        r = evaluar(100, modelo(mediana_usado=None), CANALES["wallapop"])
        self.assertFalse(r.comprar)
        self.assertIsNone(r.margen_neto)

    def test_canal_sin_comision_falla(self):
        with self.assertRaises(ValueError):
            evaluar(100, modelo(), CANALES["ebay"])

    def test_descuento_vs_nuevo(self):
        r = evaluar(300, modelo(precio_nuevo=600.0), CANALES["wallapop"])
        self.assertAlmostEqual(r.descuento_vs_nuevo, 0.5)

    def test_precio_maximo_es_la_frontera(self):
        m, c, p = modelo(), CANALES["wallapop"], Parametros()
        pm = precio_maximo(m, c, envio_compra=5, p=p)
        self.assertTrue(evaluar(pm, m, c, 5, p=p).comprar)
        self.assertFalse(evaluar(pm + 1, m, c, 5, p=p).comprar)


if __name__ == "__main__":
    unittest.main()
