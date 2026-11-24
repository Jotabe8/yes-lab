"""Uso por línea de comandos.

    python -m arbitraje_segunda_mano.app.evaluar "PS5 slim con lector y 2 mandos" 330
    python -m arbitraje_segunda_mano.app.evaluar "Sony A7 III 20k disparos" 650 --envio 5
    python -m arbitraje_segunda_mano.app.evaluar --precios-maximos
"""
import argparse

from . import catalogo
from .puntuacion import CANALES, evaluar, precio_maximo


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evalúa un anuncio de segunda mano")
    ap.add_argument("texto", nargs="?", help="título y descripción del anuncio")
    ap.add_argument("precio", nargs="?", type=float, help="precio del anuncio en €")
    ap.add_argument("--envio", type=float, default=0.0, help="envío que pagas al comprar")
    ap.add_argument("--canal", default="wallapop", choices=sorted(CANALES))
    ap.add_argument("--precios-maximos", action="store_true",
                    help="precio máximo de compra por modelo (para las búsquedas guardadas)")
    a = ap.parse_args(argv)
    modelos = catalogo.cargar()
    canal = CANALES[a.canal]

    if a.precios_maximos:
        for m in modelos:
            pm = precio_maximo(m, canal, a.envio)
            txt = f"{pm:8.0f} €" if pm is not None else "   (sin precios)"
            print(f"{m.categoria:9} {m.nombre:38} {txt}")
        return 0

    if a.texto is None or a.precio is None:
        ap.error("indica texto y precio, o --precios-maximos")
    modelo = catalogo.identificar(a.texto, modelos)
    if modelo is None:
        print("No encaja en ningún modelo del catálogo: descartado.")
        return 1
    r = evaluar(a.precio, modelo, canal, a.envio, catalogo.alarmas(a.texto))
    print(f"Modelo: {modelo.nombre}")
    print(f"Coste de compra: {r.coste_compra:.2f} €  ·  venta esperada: {r.venta_esperada} €")
    if r.descuento_vs_nuevo is not None:
        print(f"Descuento frente a nuevo: {r.descuento_vs_nuevo:.0%}")
    if r.margen_neto is not None:
        print(f"Margen neto: {r.margen_neto:.2f} € ({r.margen_pct:.0%})")
    print("Decisión:", "COMPRAR" if r.comprar else "no comprar")
    for mot in r.motivos:
        print(" -", mot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
