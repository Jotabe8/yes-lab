"""Hook de Claude Code: compila cada .mq5 tras editarlo y devuelve los errores a Claude.

Se engancha como PostToolUse (Edit/Write/MultiEdit) en .claude/settings.json. Solo actúa en
Windows y si existe el MetaEditor del laboratorio (C:\\MT5_Lab\\MetaEditor64.exe, o la ruta de la
variable MT5_LAB_METAEDITOR). En la nube (Linux) o con otro archivo sale sin hacer nada.

Nunca usa el terminal de la cuenta real: compila con el MetaEditor portable del laboratorio, y
no compila archivos dentro de AppData\\...\\MetaQuotes\\Terminal (reescribir el .ex5 ahí reinicia el
EA en los gráficos de la cuenta real).

Salida 2 con errores o warnings (Claude los lee y corrige); salida 0 si compila limpio.

También sirve a mano:
    python metodo/hooks/compilar_mq5.py ruta/EA.mq5      compila y resume el log
    python metodo/hooks/compilar_mq5.py --log ruta.log   resume un log de MT5 (UTF-16LE)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

METAEDITOR = os.environ.get("MT5_LAB_METAEDITOR", r"C:\MT5_Lab\MetaEditor64.exe")
RESULTADO = re.compile(r"(\d+)\s*(?:errors?|errores),\s*(\d+)\s*(?:warnings?|advertencias?)", re.I)
LINEA = re.compile(r"\b(error|errores|warning|advertencia)\b", re.I)


def leer_log(ruta: str | Path) -> str:
    """Lee un log de MetaEditor/MT5. Suelen ir en UTF-16LE con BOM; si no, UTF-8 o ANSI."""
    datos = Path(ruta).read_bytes()
    if datos[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return datos.decode("utf-16")
    if len(datos) > 1 and datos[1:2] == b"\x00":            # UTF-16LE sin BOM
        return datos.decode("utf-16-le", errors="replace")
    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return datos.decode("cp1252", errors="replace")


def resumir(texto: str) -> tuple[int, int, list[str]]:
    """Devuelve (errores, warnings, líneas con error/warning) de un log de compilación."""
    lineas = [l.strip() for l in texto.splitlines() if LINEA.search(l) and not RESULTADO.search(l)]
    m = RESULTADO.search(texto)
    if m:
        return int(m.group(1)), int(m.group(2)), lineas
    err = sum(1 for l in lineas if re.search(r"\berror(es)?\b", l, re.I))
    return err, len(lineas) - err, lineas


def compilar(archivo: Path) -> tuple[int, int, list[str]]:
    log = archivo.with_suffix(".log")
    log.unlink(missing_ok=True)                    # que no se lea el resultado de otra compilación
    subprocess.run([METAEDITOR, "/portable", f"/compile:{archivo}", f"/log:{log}"],
                   capture_output=True, timeout=120)
    if not log.exists():
        return 1, 0, [f"MetaEditor no escribió el log {log}"]
    return resumir(leer_log(log))


def _informe(archivo: Path, err: int, warn: int, lineas: list[str]) -> str:
    cab = f"{archivo.name}: {err} errores, {warn} warnings (MetaEditor del laboratorio)"
    return "\n".join([cab] + lineas[:40])


def hook() -> int:
    try:
        datos = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    ruta = (datos.get("tool_input") or {}).get("file_path") or ""
    if not ruta.lower().endswith(".mq5") or os.name != "nt" or not Path(METAEDITOR).exists():
        return 0                                   # .mqh, nube o PC sin laboratorio: nada
    archivo = Path(ruta)
    if "metaquotes\\terminal" in str(archivo).lower():
        # Carpeta de datos de un terminal instalado (la cuenta real): compilar ahí reescribe el .ex5
        # y MT5 reinicia el EA en los gráficos abiertos. Nunca desde el hook.
        print(f"{archivo.name}: no compilo en la carpeta de un terminal real; copia el .mq5 al "
              "laboratorio o al repo", file=sys.stderr)
        return 0
    err, warn, lineas = compilar(archivo)
    if err or warn:
        print(_informe(archivo, err, warn, lineas) + "\nCorrige hasta 0 errores y 0 warnings "
              "(checklist de mql5-pro).", file=sys.stderr)
        return 2
    print(f"{archivo.name}: compila sin errores ni warnings")
    return 0


def main(args: list[str]) -> int:
    if not args:
        return hook()
    if args[0] == "--log" and len(args) > 1:
        err, warn, lineas = resumir(leer_log(args[1]))
        print(_informe(Path(args[1]), err, warn, lineas))
        return 1 if err else 0
    archivo = Path(args[0]).resolve()
    if not Path(METAEDITOR).exists():
        print(f"No encuentro MetaEditor en {METAEDITOR} (variable MT5_LAB_METAEDITOR)", file=sys.stderr)
        return 1
    err, warn, lineas = compilar(archivo)
    print(_informe(archivo, err, warn, lineas))
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
