# WHOTS Metadata Scraper

- This is a Scrapy Framework project for scraping some information from
  the [Upper Ocean Processes Group / Project WHOTS - WHOI Hawaii Ocean Time-series Station](https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html)
  website.

- The data is automatically saved `at 00:00 on day-of-month 1`.
  [GitHub actions](https://github.com/hot-dogs/whots-metadata/blob/main/.github/workflows/whots-scrapy.yml)
  and saved
  at [results/items.json](https://github.com/hot-dogs/whots-metadata/blob/main/results/items.json).

- The crawler also writes a richer machine-readable sidecar at
  `results/whots_metadata.json`. That file is intended for downstream tools
  such as `hot-forecast`, while `results/items.json` keeps the original compact
  output shape for existing users.

## Output contract

- `results/items.json`: legacy compact output with `CURRENT` and `PREVIOUS`
  objects. The original `number`, `sys1`, `sys2`, `link1`, and `link2` keys are
  preserved.
- `results/whots_metadata.json`: structured metadata with source URL, scrape
  time, page update time, NDBC station, current/previous deployment records,
  daily/complete logger URLs, plot URLs, WHOTS position source URLs, source
  health, and parser warnings.

# Prerequisites:

```yaml
name: whots-metadata
channels:
  - conda-forge
  - defaults
dependencies:
  - scrapy
  - python
```

# Installing:

```bash
conda env update --prefix ./.env --file environment.yml --prune
conda activate ./.env
python -m pip install --no-deps -e .
```

The conda environment supplies runtime dependencies. The editable install only
registers the local `whots_metadata` package for import by tools such as
`hot-forecast`. The project uses only `conda-forge` to avoid Anaconda
commercial-channel warnings in CI.

`environment.yml` pins Twisted with Scrapy because newer Twisted releases can
break older Scrapy downloader imports in CI.

# Usage:

- To run whots_metadata crawler:

```bash
conda activate ./.env
make crawl
```

# Testing

```bash
conda activate ./.env
make test
```

# Position files

The rich metadata discovers current and previous WHOTS position-source files from
the WHOI data-directory index. For the current WHOTS deployment this can include
`Melo`, `Rover`, and `beacon` files, plus `_end.txt` files when WHOI provides
them. The `_end.txt` files contain the short recent position records that
`hot-forecast` can fetch at run time for WHOTS watch-circle plots.

# Source health

`results/whots_metadata.json` includes `source_health` so downstream tools can
see whether the WHOTS page and data-directory index were available during the
metadata run. If the data-directory request fails, the crawler still writes the
main WHOTS deployment metadata and emits a warning that `position_sources` may be
empty.
