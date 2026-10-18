# Marketplace Scraper — Django starter

A working, single-source scraper for https://books.toscrape.com/, a storefront explicitly provided for scraping practice. Its prices and ratings are demonstration data, not real market data.

## Quick start

Requires Python 3.10 or later. Extract this project and open a terminal in its folder.

```bash
python -m venv .venv
```

Activate the environment:
- macOS/Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py scrape --pages 1
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to search saved products and download CSV or JSON. Scraping runs in the terminal, not through a web button. The included SQLite database already contains 20 products from a live verification run. You can start fresh by deleting `db.sqlite3` and running `migrate` again.

Collect more pages:

```bash
python manage.py scrape --pages 3 --delay 1
```

Each page contains up to 20 listings; every product detail page is fetched for full descriptions. Defaults: one page, a one-second minimum interval between request starts, three attempts for transient failures, and connection/read timeouts. HTTP 403/429 stops the run so the source can be reviewed or retried later. Previously saved products remain intact. Repeating a run updates products by source and UPC instead of inserting duplicates. Restarting revisits pages; persisted crawl checkpoints are not implemented.

## Data and exports

Fields: source, source_id (UPC), title, decimal price, currency, description, image_url, listing_url, availability, scraped_at (UTC).

- `/export/json/`: JSON, with prices represented as decimal strings.
- `/export/csv/`: UTF-8 CSV; leading formula characters in text are neutralized for spreadsheet safety.
- Add `?q=keyword` to either export to filter titles.
- `samples/products.json` and `samples/products.csv` contain the 20 live records collected during verification.

Images are stored as absolute URLs, not downloaded. Optional missing descriptions are empty strings. Missing required fields cause a visible error rather than silently producing incomplete data. HTML layout changes may require selector updates.

## Tests

```bash
python manage.py test catalog
```

Seven tests cover extraction, layout-change failures, pagination, host restrictions, HTTP throttling, repeated-run deduplication, exports, search filtering, and spreadsheet formula neutralization. A live one-page run also collected 20 records successfully.

## Project map

- `catalog/scraper.py`: fetching, rate limits, retries, and source-specific parsing.
- `catalog/models.py`: database schema and unique product identity.
- `catalog/management/commands/scrape.py`: CLI collection command.
- `catalog/views.py`: catalog and export endpoints.
- `catalog/templates/catalog/index.html`: responsive catalog interface.

## Scope and next steps

This is a local, single-worker starter, not a production multi-platform service. This source uses server-rendered HTML, so browser automation, login, and anti-bot bypass are unnecessary. No social-media connectors are included. The source adapter is separated so more sources can be added later; each requires its own extraction and access checks.

For larger deployments, add a worker queue and scheduler, PostgreSQL, run history/checkpoints, structured monitoring, authenticated UI access, and source-specific concurrency limits. Browser rendering can be introduced for sources requiring JavaScript. The included Django development server and development secret are for local use only; configure production hosting, a private secret, allowed hosts, and DEBUG=False before deployment. Avoid overlapping scrape jobs with SQLite.

Dependency ranges are in requirements.txt. Exact versions used during verification are in requirements-tested.txt.
