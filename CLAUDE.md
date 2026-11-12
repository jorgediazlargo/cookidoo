# cookidoo

Recetas Thermomix propias publicadas en GitHub Pages para importarlas en
Cookidoo pegando la URL de cada receta.

- Web: https://jorgediazlargo.github.io/cookidoo/
- URL de una receta: `https://jorgediazlargo.github.io/cookidoo/<slug>/`
  (`<slug>` = nombre del fichero `.toml` sin extensión).
- Repo **público** (`jorgediazlargo/cookidoo`): nada personal en las recetas.

## Cómo funciona

`recetas/*.toml` → `build.py` → `_site/` (una página por receta con
`<script type="application/ld+json">` schema.org/Recipe, que es lo que lee el
importador de Cookidoo). Cada push a `main` publica con
`.github/workflows/pages.yml`. Solo stdlib, Python 3.11+.

Probar en local: `python3 build.py --base-url http://localhost:8000 && python3 -m http.server -d _site`

## Añadir una receta

Copia `recetas/hummus.toml` como plantilla. Campos:

- Obligatorios: `nombre`, `raciones`, `tiempo_total` (min), `ingredientes`, `pasos`.
- Opcionales: `descripcion`, `tiempo_preparacion`, `tiempo_coccion`,
  `dificultad`, `categoria`, `cocina`, `etiquetas`, `fecha`, `imagen`
  (`img/x.jpg` dentro de `recetas/img/`, o URL absoluta), `notas`, `slug`.
- `ingredientes` admite secciones: `{ titulo = "Para la masa", items = [...] }`
  (en el JSON-LD se aplanan: Cookidoo no lee secciones).

Estilo Cookidoo (para que se lea igual que las oficiales):

- Cantidades en gramos siempre que se pueda, también líquidos (`40 g de agua`).
- Un ingrediente por línea, cantidad primero: `400 g de garbanzos cocidos, escurridos`.
- Pasos en usted e imperativo, con los ajustes TM en notación Cookidoo:
  `5 min/100°C/vel 1`, `3 seg/vel 7`, `giro inverso` (`10 min/100°C/giro inverso/vel cuchara`),
  `Varoma`, `Amasar 2 min`, `Turbo 1 seg`. Mariposa: «Coloque la mariposa».
- Un paso por cada programación del vaso; «baje los restos con la espátula» cuando toque.

El importador de Cookidoo crea la receta como texto: los ajustes TM aparecen
escritos en el paso, pero hay que revisarla en Cookidoo tras importar.
