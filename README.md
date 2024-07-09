# WHOTS Metadata Scrapper

- This is a Scrapy Framework project for scraping some information from
  the [Upper Ocean Processes Group / Project WHOTS - WHOI Hawaii Ocean Time-series Station](https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html)
  website.

- The data is automatically saved `at 00:00 on day-of-month 1`.
  [GitHub actions](https://github.com/hot-dogs/whots-metadata/blob/main/.github/workflows/whots-scrapy.yml)
  and saved
  at [results/items.json](https://github.com/hot-dogs/whots-metadata/blob/main/results/items.json)


# Prerequisites:

```yaml
name: whots-metadata
channels:
  - conda-forge
  - defaults
dependencies:
  - scrapy=2.11.0
  - python=3.12
```

# Installing: 

```bash
conda create --prefix ./.env python scrapy -c conda-forge  
```

# Usage:

- To run whots_metadata crawler: 

```bash
conda activate ./.env      
cd src/whots_metadata
scrapy crawl whotsmetadata -O ../../results/items.json                    
```
