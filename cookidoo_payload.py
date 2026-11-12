#!/usr/bin/env python3
"""Convierte una receta TOML en el cuerpo del PATCH de Cookidoo
(`/created-recipes/es-ES/{id}`), con anotaciones de ajustes TM para que los
pasos tengan botón de cocinado guiado.

Uso:  python3 cookidoo_payload.py recetas/x.toml   → JSON por stdout

La API de recetas creadas de Cookidoo no es pública: formato sacado de
github.com/danielkliem/mcp-cookidoo y miaucl/cookidoo-api. Puede cambiar.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build import cargar, ingredientes_planos  # noqa: E402

# Cookidoo pinta el giro inverso y la vel cuchara con iconos de uso privado
# (visto en recetas creadas desde su editor web).
GIRO_INVERSO = ""
CUCHARA = ""

# «5 seg/vel 5», «22 min/100°C/vel 1», «10 min/100°C/giro inverso/vel cuchara»,
# «20 min/Varoma/vel 2». No se anotan rangos («vel 5-10») ni Turbo/Amasar:
# quedan como texto y se programan a mano.
_ACCION = re.compile(
    r"(?P<n>\d+)\s*(?P<u>seg|min)"
    r"(?:\s*/\s*(?:(?P<t>\d+)\s*°\s*C|(?P<varoma>Varoma)))?"
    rf"(?:\s*/\s*(?P<ccw>{GIRO_INVERSO}))?"
    rf"\s*/\s*vel\s*(?P<v>{CUCHARA}|\d+(?:[.,]\d+)?)(?![\d,.]*\s*-)",
    re.IGNORECASE,
)


def texto_cookidoo(texto: str) -> str:
    texto = re.sub(r"vel\s+cuchara", f"vel {CUCHARA}", texto, flags=re.IGNORECASE)
    return re.sub(r"giro\s+inverso", GIRO_INVERSO, texto, flags=re.IGNORECASE)


def anotaciones(texto: str) -> list[dict]:
    out = []
    for m in _ACCION.finditer(texto):
        seg = int(m["n"]) * (60 if m["u"].lower() == "min" else 1)
        vel = "soft" if m["v"] == CUCHARA else m["v"].replace(",", ".")
        pos = {"offset": m.start(), "length": m.end() - m.start()}
        if m["varoma"]:
            out.append({
                "type": "MODE", "name": "STEAMING", "position": pos,
                "data": {"time": seg, "speed": vel, "direction": "CW", "accessory": "Varoma"},
            })
        else:
            data: dict = {"speed": vel, "time": seg}
            if m["ccw"]:
                data["direction"] = "CCW"
            if m["t"]:
                data["temperature"] = {"value": m["t"], "unit": "C"}
            out.append({"type": "TTS", "position": pos, "data": data})
    return out


def payload(r: dict) -> dict:
    return {
        "name": r["nombre"],
        "image": None,
        "isImageOwnedByUser": False,
        "tools": ["TM7", "TM6", "TM5"],
        "yield": {"value": int(r["raciones"]), "unitText": "portion"},
        "prepTime": int(r.get("tiempo_preparacion") or 0) * 60,
        "cookTime": int(r.get("tiempo_coccion") or 0) * 60,
        "totalTime": int(r["tiempo_total"]) * 60,
        "ingredients": [{"type": "INGREDIENT", "text": i} for i in ingredientes_planos(r)],
        "instructions": [
            {"type": "STEP", "text": t, "annotations": anotaciones(t)}
            for t in map(texto_cookidoo, r["pasos"])
        ],
        "hints": r.get("notas", ""),
        "workStatus": "PRIVATE",
        "recipeMetadata": {"requiresAnnotationsCheck": False},
    }


if __name__ == "__main__":
    print(json.dumps(payload(cargar(Path(sys.argv[1]))), ensure_ascii=False))
