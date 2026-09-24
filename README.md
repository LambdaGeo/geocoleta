# fielddash

Schema-driven dashboards for **field data collection** (Epicollect5), built directly from the **form schema**. Every question is identified by Epicollect's stable `ref`, and its input type (`radio`, `checkbox`, `integer`, `location`, ...) automatically dictates the filter, chart, and map representation. Modifying, adding, or reordering questions in the form does not break the dashboard, and setting up a new fieldwork survey requires only a YAML configuration file.

Ready-to-use pages:
- **Overview**: summary indicators, map, submissions over time, collectors.
- **Highlights**: curated charts configured in your YAML.
- **Questions**: all questions grouped by section, with search, text-field toggle, and dynamic cross-tabulation.
- **Data**: searchable table with CSV and Excel export.

## Installation

```bash
pip install git+https://github.com/LambdaGeo/fielddash
# or for development:
git clone https://github.com/LambdaGeo/fielddash && cd fielddash
pip install -e ".[dev]"
```

## Quickstart

```bash
fielddash run exemplos/residuos/projeto.yaml
```

The example uses anonymized household survey data on solid waste management (Itaqui-Bacanga, São Luís – MA) and showcases a custom project page (`Reciclagem`).

## Setting Up a New Field Project

1. Create a project folder with a `.env` file containing your Epicollect app credentials (generated under *Apps* in your project's administration area):
   ```bash
   MYPROJ_CLIENT_ID=...
   MYPROJ_CLIENT_SECRET=...
   ```
   *Public projects do not require credentials: simply omit `credentials` in the config.*

2. Create `myproject.yaml`:
   ```yaml
   title: "My Field Survey"
   source:
     type: epicollect
     project: project-slug      # or ${VARIABLE} from .env
     credentials: MYPROJ
   ```

3. Inspect the form fields to select aliases, filters, and highlights:
   ```bash
   fielddash fields myproject.yaml
   ```

4. Complete the configuration (all keys below are optional) and run `fielddash run myproject.yaml`:
   ```yaml
   subtitle: "Research team, institution..."
   fields:            # alias -> ref suffix, column, or question label
     neighborhood: "5401ce"
     waste_dest: "48c35e"
   types:             # force type (e.g. treat free text as category)
     neighborhood: category
   ignore: [created_by, "3401cb"]   # hide fields (e.g. collector email)
   filters: [created_at, neighborhood]
   highlights:
     - {field: waste_dest, by: neighborhood, title: "Waste destination by neighborhood"}
   sections:          # tabs on the Questions page (default: form groups)
     - {title: "Profile", fields: [age, gender]}
   map: {field: location, popup: [neighborhood]}
   extensions: [pages]              # .py files or directories with custom pages
   timezone: America/Fortaleza
   cache_minutes: 5
   ```
   *(Note: Portuguese configuration keys such as `titulo`, `fonte`, `campos`, `ignorar`, etc., are also supported for backwards compatibility).*

Running `fielddash run folder/` will scan all `.yaml` files in the directory and present a project selector in the sidebar.
To work offline or test without internet access, use `source: {type: json, data: ..., schema: ...}` (as shown in `exemplos/residuos/projeto.yaml`).

## Using in a Custom Streamlit Script / Deployment

The dashboard can also be invoked as a Python function inside your own Streamlit app:

```python
# streamlit_app.py
import fielddash

fielddash.dashboard("projects/")          # or "projects/waste.yaml"
```

Relative paths are resolved relative to the current directory or the script folder.
Run with:
```bash
streamlit run streamlit_app.py
```

### Streamlit Community Cloud
Deploy your repository (containing `streamlit_app.py`, your `.yaml` configs, and a `requirements.txt` with `fielddash @ git+https://github.com/LambdaGeo/fielddash`), then add credentials in *Settings → Secrets* in TOML format:

```toml
MYPROJ_CLIENT_ID = "..."
MYPROJ_CLIENT_SECRET = "..."
```

`fielddash` checks environment variables and `.env` first, then falls back to `st.secrets` (also resolving `${VAR}` references in YAML). The data cache is shared among server sessions, so Epicollect receives at most one request per project every `cache_minutes`.

### Self-Hosted Server
```bash
fielddash run projects/ --server.port 8501 --server.headless true
```
(e.g., as a systemd service behind an Nginx reverse proxy with HTTPS).

## Custom Pages

A project-specific page is a standard `.py` file listed in `extensions`:

```python
from fielddash.core.registry import page
from fielddash.ui.charts import render_field


@page("Recycling", order=40)
def render(ctx):
    ds = ctx.dataset
    render_field(ds, ctx.df, ds.field("recycle_habit"), by=ds.field("neighborhood"))
```

- `ctx.df` provides the data with all active sidebar filters applied.
- `ds.field("alias")` resolves the field (column, type, options) dynamically by its stable schema ref.
- Additional data sources (e.g. KoboToolbox, CSV) can be registered with `@source("type")`.

## Project Structure

```
fielddash/
  cli.py            CLI commands `fielddash run` and `fielddash fields`
  web.py            `fielddash.dashboard()`: config, cache, filters, navigation
  app.py            Streamlit entry point used by `fielddash run`
  core/schema.py    Epicollect schema parser -> list[Field], column naming, reconciliation
  core/normalize.py raw entries -> typed series (ordered categories, lists, coords, datetimes)
  core/config.py    YAML config parser (+ ${VAR} resolution from .env and secrets)
  sources/          data source plugins (@source): epicollect (API, pagination), json
  ui/               dynamic filters, charts, and maps based on field types
  views/            default pages (@page): Overview, Highlights, Questions, Data
exemplos/           example projects with anonymized datasets
tests/              pytest test suite (schema, index shifting, AppTest integration)
docs/PLANO.md       historical development plan
```

## Running Tests

```bash
pytest
```

## Authors

- **Sergio Costa** ([@LambdaGeo](https://github.com/LambdaGeo))
- **André Moura** ([@AndreMouraL](https://github.com/AndreMouraL))

## License

MIT — see [LICENSE](LICENSE).
