"""Calculadora de margen neto y decisión de compra.

    ingreso     = mediana_usado × (1 − comisión_canal) − comisión_fija − envío_vendedor
    costes      = embalaje + reacondicionado + mediana_usado × provisión_garantía
                  + p_problema × pérdida_si_sale_mal
    margen_neto = ingreso − costes − (precio + envío_compra)

El descuento frente a nuevo solo sirve para detectar; el margen sale del precio de usado.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .catalogo import Modelo


@dataclass
class Canal:
    """Dónde se revende. Comisiones como fracción (0.10 = 10 %)."""
    nombre: str
    comision_pct: Optional[float]
    comision_fija: float = 0.0
    envio_vendedor: float = 0.0


# VERIFICAR las comisiones antes de operar: cambian y dependen de si eres particular o profesional.
CANALES: Dict[str, Canal] = {
    # En Wallapop Envíos el envío y la protección los paga el comprador (web oficial, nov-2026).
    "wallapop": Canal("wallapop", comision_pct=0.0),
    "en_mano": Canal("en_mano", comision_pct=0.0),
    # Sin configurar a propósito: rellenar con la tabla vigente de eBay.es.
    "ebay": Canal("ebay", comision_pct=None),
}


@dataclass
class Parametros:
    embalaje: float = 3.0
    reacondicionado: float = 5.0          # limpieza, pequeñas piezas
    provision_garantia_pct: float = 0.0   # 0 como particular; 0.03-0.05 como profesional
    p_problema: float = 0.05              # probabilidad de que la compra salga mal
    perdida_sin_suelo_pct: float = 0.5    # pérdida si sale mal y no hay precio suelo conocido
    umbral_eur: float = 30.0
    umbral_pct: float = 0.25
    max_dias_venta: float = 30.0
    colchon_suelo: float = 0.0            # cuánto por encima del suelo se acepta pagar


@dataclass
class Resultado:
    modelo: str
    precio: float
    coste_compra: float
    venta_esperada: Optional[float]
    margen_neto: Optional[float]
    margen_pct: Optional[float]
    descuento_vs_nuevo: Optional[float]
    comprar: bool
    motivos: List[str] = field(default_factory=list)


def _margen(coste_compra: float, modelo: Modelo, canal: Canal, p: Parametros) -> float:
    venta = modelo.mediana_usado
    ingreso = venta * (1 - canal.comision_pct) - canal.comision_fija - canal.envio_vendedor
    if modelo.precio_suelo is not None:
        perdida = max(coste_compra - modelo.precio_suelo, 0.0)
    else:
        perdida = coste_compra * p.perdida_sin_suelo_pct
    costes = (p.embalaje + p.reacondicionado + venta * p.provision_garantia_pct
              + p.p_problema * perdida)
    return ingreso - costes - coste_compra


def _cumple_margen(margen: float, coste: float, p: Parametros) -> bool:
    return margen >= p.umbral_eur and coste > 0 and margen / coste >= p.umbral_pct


def evaluar(precio: float, modelo: Modelo, canal: Canal, envio_compra: float = 0.0,
            alarmas: Optional[dict] = None, p: Optional[Parametros] = None) -> Resultado:
    p = p or Parametros()
    if canal.comision_pct is None:
        raise ValueError(f"El canal '{canal.nombre}' no tiene comisión configurada")
    coste = precio + envio_compra
    descuento = (1 - precio / modelo.precio_nuevo) if modelo.precio_nuevo else None
    motivos: List[str] = []

    if modelo.mediana_usado is None:
        return Resultado(modelo.id, precio, coste, None, None, None, descuento, False,
                         ["falta la mediana de usado de este modelo en el catálogo"])

    margen = _margen(coste, modelo, canal, p)
    pct = margen / coste if coste else None
    comprar = _cumple_margen(margen, coste, p)
    if not comprar:
        motivos.append(f"margen insuficiente (mínimo {p.umbral_eur:.0f} € y {p.umbral_pct:.0%})")

    if alarmas and alarmas.get("graves"):
        comprar = False
        motivos.append("alarmas graves: " + ", ".join(alarmas["graves"]))
    if alarmas and alarmas.get("leves"):
        motivos.append("revisar: " + ", ".join(alarmas["leves"]))
    if modelo.dias_venta is not None and modelo.dias_venta > p.max_dias_venta:
        comprar = False
        motivos.append(f"rotación lenta ({modelo.dias_venta:.0f} días)")
    if modelo.dias_venta is None:
        motivos.append("rotación desconocida")
    if modelo.precio_suelo is not None and coste > modelo.precio_suelo + p.colchon_suelo:
        motivos.append(f"riesgo por encima del suelo: {coste - modelo.precio_suelo:.0f} €")
    if modelo.precio_suelo is None:
        motivos.append("precio suelo desconocido")

    return Resultado(modelo.id, precio, coste, modelo.mediana_usado, round(margen, 2),
                     round(pct, 4) if pct is not None else None,
                     round(descuento, 4) if descuento is not None else None, comprar, motivos)


def precio_maximo(modelo: Modelo, canal: Canal, envio_compra: float = 0.0,
                  p: Optional[Parametros] = None) -> Optional[float]:
    """Precio de anuncio más alto que todavía cumple los umbrales de margen.

    Es el precio máximo a poner en la búsqueda guardada de Wallapop.
    """
    p = p or Parametros()
    if modelo.mediana_usado is None or canal.comision_pct is None:
        return None
    bajo, alto = 0.0, modelo.mediana_usado
    if not _cumple_margen(_margen(bajo + envio_compra + 1e-9, modelo, canal, p),
                          bajo + envio_compra + 1e-9, p):
        return None
    for _ in range(60):  # bisección: el margen baja al subir el precio
        medio = (bajo + alto) / 2
        coste = medio + envio_compra
        if _cumple_margen(_margen(coste, modelo, canal, p), coste, p):
            bajo = medio
        else:
            alto = medio
    return round(bajo, 2)
