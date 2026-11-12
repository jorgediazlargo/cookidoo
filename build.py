#!/usr/bin/env python3
"""Genera el sitio estático de recetas (una página por receta con JSON-LD
schema.org/Recipe) para importarlas en Cookidoo pegando su URL.

Uso:  python3 build.py [--base-url https://jorgediazlargo.github.io/cookidoo]
Salida: _site/
Solo stdlib (tomllib, Python 3.11+).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import tomllib
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
RECETAS = ROOT / "recetas"
OUT = ROOT / "_site"
DEFAULT_BASE = "https://jorgediazlargo.github.io/cookidoo"
AUTOR = "Jorge Díaz Largo"

OBLIGATORIOS = ("nombre", "raciones", "tiempo_total", "ingredientes", "pasos")


def slugify(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def iso_min(minutos: int | None) -> str | None:
    if not minutos:
        return None
    h, m = divmod(int(minutos), 60)
    return "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "")


def fmt_min(minutos: int | None) -> str:
    if not minutos:
        return ""
    h, m = divmod(int(minutos), 60)
    return " ".join(p for p in (f"{h} h" if h else "", f"{m} min" if m else "") if p)


def cargar(path: Path) -> dict:
    with path.open("rb") as f:
        r = tomllib.load(f)
    faltan = [k for k in OBLIGATORIOS if not r.get(k)]
    if faltan:
        sys.exit(f"{path.name}: faltan campos obligatorios: {', '.join(faltan)}")
    r["slug"] = r.get("slug") or path.stem
    return r


def ingredientes_planos(r: dict) -> list[str]:
    """`ingredientes` puede ser una lista de strings o de secciones
    {titulo, items}. Para el JSON-LD se aplana (Cookidoo no lee secciones)."""
    out = []
    for i in r["ingredientes"]:
        out.extend(i["items"] if isinstance(i, dict) else [i])
    return out


def jsonld(r: dict, base: str) -> dict:
    url = f"{base}/{r['slug']}/"
    d = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["nombre"],
        "description": r.get("descripcion", ""),
        "author": {"@type": "Person", "name": AUTOR},
        "datePublished": str(r.get("fecha", date.today())),
        "url": url,
        "inLanguage": "es-ES",
        "recipeYield": f"{r['raciones']} raciones",
        "prepTime": iso_min(r.get("tiempo_preparacion")),
        "cookTime": iso_min(r.get("tiempo_coccion")),
        "totalTime": iso_min(r["tiempo_total"]),
        "recipeCategory": r.get("categoria"),
        "recipeCuisine": r.get("cocina"),
        "keywords": ", ".join(r.get("etiquetas", [])) or None,
        "tool": ["Thermomix"],
        "recipeIngredient": ingredientes_planos(r),
        "recipeInstructions": [
            {"@type": "HowToStep", "position": n, "text": p, "url": f"{url}#paso-{n}"}
            for n, p in enumerate(r["pasos"], 1)
        ],
    }
    if r.get("imagen"):
        img = r["imagen"]
        d["image"] = [img if img.startswith("http") else f"{base}/{img.lstrip('/')}"]
    if r.get("notas"):
        d["comment"] = {"@type": "Comment", "text": r["notas"]}
    return {k: v for k, v in d.items() if v not in (None, "", [])}


CSS = """
:root{--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--acc:#00a35c;--line:#e5e5ea}
@media (prefers-color-scheme:dark){:root{--bg:#111;--fg:#f2f2f7;--mut:#a1a1a6;--line:#2c2c2e}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:17px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:720px;margin:0 auto;padding:24px 16px 64px}
a{color:var(--acc)}h1{line-height:1.2;margin:.2em 0}.mut{color:var(--mut)}
.meta{display:flex;flex-wrap:wrap;gap:8px 20px;margin:12px 0 20px;color:var(--mut);font-size:15px}
img.hero{width:100%;border-radius:12px;margin:8px 0}
h2{margin-top:32px;border-bottom:1px solid var(--line);padding-bottom:4px}
ol li{margin:8px 0}ul.lista{list-style:none;padding:0}ul.lista li{padding:10px 0;border-bottom:1px solid var(--line)}
.url{font-family:ui-monospace,monospace;font-size:14px;word-break:break-all}
"""


def pagina(titulo: str, cuerpo: str, head_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title>{head_extra}
<style>{CSS}</style></head>
<body><main>{cuerpo}</main></body></html>
"""


def render_receta(r: dict, base: str) -> str:
    e = html.escape
    ld = json.dumps(jsonld(r, base), ensure_ascii=False, indent=2).replace("</", "<\\/")
    head = (
        f'\n<meta name="description" content="{e(r.get("descripcion", ""))}">'
        f'\n<link rel="canonical" href="{base}/{r["slug"]}/">'
        f'\n<script type="application/ld+json">\n{ld}\n</script>'
    )
    meta = [f"🍽 {r['raciones']} raciones"]
    if r.get("tiempo_preparacion"):
        meta.append(f"🔪 Preparación {fmt_min(r['tiempo_preparacion'])}")
    meta.append(f"⏱ Total {fmt_min(r['tiempo_total'])}")
    if r.get("dificultad"):
        meta.append(f"📶 {e(r['dificultad'])}")

    def ul(items: list[str]) -> str:
        return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"

    ingr_html, sueltos = "", []
    for i in r["ingredientes"]:
        if isinstance(i, dict):
            if sueltos:
                ingr_html, sueltos = ingr_html + ul(sueltos), []
            ingr_html += f"<h3>{e(i['titulo'])}</h3>" + ul(i["items"])
        else:
            sueltos.append(i)
    if sueltos:
        ingr_html += ul(sueltos)

    pasos = "".join(f'<li id="paso-{n}">{e(p)}</li>' for n, p in enumerate(r["pasos"], 1))
    img = ""
    if r.get("imagen"):
        src = jsonld(r, base)["image"][0]
        img = f'<img class="hero" src="{e(src)}" alt="{e(r["nombre"])}">'
    notas = f"<h2>Notas</h2><p>{e(r['notas'])}</p>" if r.get("notas") else ""
    cuerpo = f"""<p><a href="{base}/">← Recetas</a></p>
<h1>{e(r['nombre'])}</h1>
<p class="mut">{e(r.get('descripcion', ''))}</p>
<div class="meta">{''.join(f'<span>{m}</span>' for m in meta)}</div>
{img}
<h2>Ingredientes</h2>{ingr_html}
<h2>Preparación</h2><ol>{pasos}</ol>
{notas}
<h2>Importar en Cookidoo</h2>
<p class="url">{base}/{r['slug']}/</p>"""
    return pagina(r["nombre"], cuerpo, head)


def render_indice(recetas: list[dict], base: str) -> str:
    e = html.escape
    items = "".join(
        f'<li><a href="{base}/{r["slug"]}/">{e(r["nombre"])}</a>'
        f'<div class="mut">{e(r.get("categoria", ""))} · {fmt_min(r["tiempo_total"])} · {r["raciones"]} raciones</div></li>'
        for r in sorted(recetas, key=lambda r: r["nombre"].lower())
    )
    cuerpo = f"""<h1>Recetas Thermomix</h1>
<p class="mut">Abre una receta y pega su URL en Cookidoo para importarla.</p>
<ul class="lista">{items}</ul>"""
    return pagina("Recetas Thermomix", cuerpo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    base = ap.parse_args().base_url.rstrip("/")

    recetas = [cargar(p) for p in sorted(RECETAS.glob("*.toml"))]
    slugs = [r["slug"] for r in recetas]
    if len(slugs) != len(set(slugs)):
        sys.exit("Slugs duplicados")

    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    (OUT / ".nojekyll").touch()
    if (RECETAS / "img").exists():
        shutil.copytree(RECETAS / "img", OUT / "img")
    for r in recetas:
        d = OUT / r["slug"]
        d.mkdir()
        (d / "index.html").write_text(render_receta(r, base), encoding="utf-8")
    (OUT / "index.html").write_text(render_indice(recetas, base), encoding="utf-8")
    print(f"{len(recetas)} recetas → {OUT}")


if __name__ == "__main__":
    main()
