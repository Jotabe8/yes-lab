"""Catálogo cerrado de modelos vigilados y reconocimiento del modelo a partir del texto de un anuncio.

Solo se valoran anuncios que encajan en un modelo del catálogo: mejor pocos modelos bien
conocidos que muchos mal valorados.
"""
import csv
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

RUTA_CATALOGO = Path(__file__).with_name("catalogo.csv")

# Señales de alarma. Se buscan como palabras o frases completas en el texto normalizado.
ALARMAS_GRAVES = (
    "para piezas", "no funciona", "no enciende", "averiado", "averiada", "bloqueado",
    "bloqueada", "icloud",
    "replica", "imitacion", "falsa", "falso", "caja vacia", "solo caja", "solo la caja",
    "busco", "compro", "cambio por", "cambio x", "baneada", "baneado", "roto", "rota",
)
ALARMAS_LEVES = (
    "sin factura", "sin caja", "sin cargador", "golpe", "aranazo", "aranazos", "rayada",
    "rayado", "detalle", "drift", "hongos", "negociable",
)
# Si el anuncio empieza por una de estas palabras, probablemente vende un accesorio.
ACCESORIOS = ("mando", "mandos", "juego", "juegos", "funda", "cargador", "soporte", "caja",
              "correa", "bateria", "parasol", "tapa", "dock", "base", "skin", "pegatina")


def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos ni signos, y une letras con el número que las sigue.

    Así "PS 5", "ps5" y "PlayStation-5" acaban igual; "85mm f/1.8" queda "85 1 8".
    """
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"(\d)\s*mm\b", r"\1", t)          # 85mm -> 85
    t = re.sub(r"\bf\s*(\d)", r"\1", t)           # f 1 8 / f1 8 -> 1 8
    t = re.sub(r"\b([a-z]+) (\d+)\b", r"\1\2", t)  # ps 5 -> ps5 (no "digital 1tb")
    return " ".join(t.split())


def _contiene(texto_norm: str, frase_norm: str) -> bool:
    return f" {frase_norm} " in f" {texto_norm} "


def _num(valor: str) -> Optional[float]:
    valor = (valor or "").strip()
    return float(valor) if valor else None


@dataclass
class Modelo:
    id: str
    categoria: str
    nombre: str
    palabras_clave: List[str]
    excluir: List[str] = field(default_factory=list)
    precio_nuevo: Optional[float] = None
    mediana_usado: Optional[float] = None
    precio_suelo: Optional[float] = None
    dias_venta: Optional[float] = None
    fuente_precios: str = ""
    fecha_precios: str = ""

    def coincidencia(self, texto_norm: str) -> int:
        """Longitud de la palabra clave más larga que aparece (0 si no encaja o hay exclusión)."""
        if any(_contiene(texto_norm, e) for e in self.excluir):
            return 0
        return max((len(k) for k in self.palabras_clave if _contiene(texto_norm, k)), default=0)


def cargar(ruta: Path = RUTA_CATALOGO) -> List[Modelo]:
    modelos = []
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            modelos.append(Modelo(
                id=fila["id"],
                categoria=fila["categoria"],
                nombre=fila["modelo"],
                palabras_clave=[normalizar(k) for k in fila["palabras_clave"].split("|") if k.strip()],
                excluir=[normalizar(k) for k in fila["excluir"].split("|") if k.strip()],
                precio_nuevo=_num(fila["precio_nuevo"]),
                mediana_usado=_num(fila["mediana_usado"]),
                precio_suelo=_num(fila["precio_suelo"]),
                dias_venta=_num(fila["dias_venta"]),
                fuente_precios=fila.get("fuente_precios", ""),
                fecha_precios=fila.get("fecha_precios", ""),
            ))
    return modelos


def identificar(texto: str, modelos: List[Modelo]) -> Optional[Modelo]:
    """Devuelve el modelo cuya palabra clave más específica aparece en el texto, o None."""
    t = normalizar(texto)
    mejor, puntos = None, 0
    for m in modelos:
        p = m.coincidencia(t)
        if p > puntos:
            mejor, puntos = m, p
    return mejor


def alarmas(texto: str) -> dict:
    """Señales de alarma del anuncio: {'graves': [...], 'leves': [...]}."""
    t = normalizar(texto)
    graves = [a for a in ALARMAS_GRAVES if _contiene(t, a)]
    leves = [a for a in ALARMAS_LEVES if _contiene(t, a)]
    primera = t.split(" ", 1)[0] if t else ""
    if primera in ACCESORIOS:
        graves.append(f"posible accesorio ('{primera}')")
    return {"graves": graves, "leves": leves}
