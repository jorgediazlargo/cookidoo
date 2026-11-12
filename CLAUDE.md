# cookidoo

Recetas Thermomix propias: se crean en «Mis recetas creadas» de Cookidoo
(cuenta de Jorge, cookidoo.es) y además se publican en GitHub Pages para verlas.

**El importador por URL de Cookidoo NO sirve**: solo admite webs de Cookidoo o
de la comunidad Vorwerk («Por el momento no es posible importar desde este
sitio web»). Las recetas se suben con la API interna de recetas creadas.

## Subir una receta a Cookidoo

API no oficial (sacada de la web de Cookidoo, miaucl/cookidoo-api y
danielkliem/mcp-cookidoo); puede cambiar sin aviso.

1. `python3 cookidoo_payload.py recetas/<slug>.toml` → cuerpo JSON del PATCH.
2. Navegador integrado en `https://cookidoo.es/created-recipes/es-ES` con la
   sesión de Jorge (si sale el login de eu.login.vorwerk.com, que entre él; no
   usar su contraseña). Desde la página, con `fetch` (cookies de sesión):
   - Nueva: `POST /created-recipes/es-ES` con `{"recipeName": nombre}` →
     `recipeId`; esperar ~5 s; `PATCH /created-recipes/es-ES/{recipeId}` con el
     JSON. Headers `Accept`/`Content-Type: application/json`.
   - Ya subida (`cookidoo_id` en el TOML): solo el PATCH a ese id.
3. Guardar `cookidoo_id = "<recipeId>"` en el TOML y comprobar con
   `GET` (Accept `application/vnd.vorwerk.customer-recipe.full+json`) que los
   pasos llevan sus anotaciones `TTS`.
4. Enlace para Jorge: `https://cookidoo.es/created-recipes/es-ES/<recipeId>`.

Ajustes TM con botón de cocinado guiado: `N seg|min[/T°C|/Varoma][/giro inverso]/vel X|cuchara`.
`cookidoo_payload.py` convierte «giro inverso» y «vel cuchara» a los iconos de
Cookidoo (U+E003, U+E002). Rangos (`vel 5-10`), Turbo y Amasar quedan como texto.

- Web (solo para ver): https://jorgediazlargo.github.io/cookidoo/
- Repo **público** (`jorgediazlargo/cookidoo`): nada personal en las recetas.

## Cómo funciona

`recetas/*.toml` → `build.py` → `_site/` (una página por receta con
`<script type="application/ld+json">` schema.org/Recipe).
Cada push a `main` publica con
`.github/workflows/pages.yml`. Solo stdlib, Python 3.11+.

Probar en local: `python3 build.py --base-url http://localhost:8000 && python3 -m http.server -d _site`

## Añadir una receta

Copia `recetas/hummus.toml` como plantilla. Campos:

- Obligatorios: `nombre`, `raciones`, `tiempo_total` (min), `ingredientes`, `pasos`.
- Opcionales: `descripcion`, `tiempo_preparacion`, `tiempo_coccion`,
  `dificultad`, `categoria`, `cocina`, `etiquetas`, `fecha`, `cookidoo_id`, `imagen`
  (`img/x.jpg` dentro de `recetas/img/`, o URL absoluta), `notas`, `slug`.
- `imagen`: **siempre cuadrada 1:1** (p. ej. 1024×1024 o 1080×1080). Jorge las
  genera con ChatGPT: al darle el prompt, pide explícitamente formato cuadrado 1:1.
- `ingredientes` admite secciones: `{ titulo = "Para la masa", items = [...] }`
  (en el JSON-LD se aplanan: Cookidoo no lee secciones).

Estilo Cookidoo (para que se lea igual que las oficiales):

- Cantidades en gramos siempre que se pueda, también líquidos (`40 g de agua`).
- Un ingrediente por línea, cantidad primero: `400 g de garbanzos cocidos, escurridos`.
- Pasos en usted e imperativo, con los ajustes TM en notación Cookidoo:
  `5 min/100°C/vel 1`, `3 seg/vel 7`, `giro inverso` (`10 min/100°C/giro inverso/vel cuchara`),
  `Varoma`, `Amasar 2 min`, `Turbo 1 seg`. Mariposa: «Coloque la mariposa».
- Un paso por cada programación del vaso; «baje los restos con la espátula» cuando toque.
