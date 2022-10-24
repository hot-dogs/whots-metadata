# WHOTS Scrapy Metadata

- This scrapy project is used for extracting metadata information from
  the [Upper Ocean Processes Group / Project WHOTS - WHOI Hawaii Ocean Time-series Station](https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html)
  website.

- The data is automatically scraped at `00:00 on day-of-month 1` by
  [GitHub actions](https://github.com/hot-dogs/whots-metadata/blob/main/.github/workflows/whots-scrapy.yml)
  and saved
  at [results/items.json](https://github.com/hot-dogs/whots-metadata/blob/main/results/items.json)


# Prerequisites

```yaml
name: whots-metadata
channels:
  - conda-forge
  - defaults
dependencies:
  - scrapy=2.7.0
  - python=3.10
```

# Installing 

```bash
conda create --prefix ./.env python=3.10 scrapy=2.7.0 -c conda-forge  
```

# Running the spider

- To run whots_metadata crawler: 

```bash
conda activate ./.env      
cd whots_metadata
scrapy crawl whotsmetadata -O ../results/items.json                    
```

- The results will be stored under `/results`, on `.json` file.
