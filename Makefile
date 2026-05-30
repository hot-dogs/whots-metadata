.PHONY: env test crawl clean-bytecode

PYTHON ?= python
ENV_PREFIX ?= ./.env
PYTHONPATH := src/whots_metadata

# Create or update the local conda environment used by this project.
env:
	conda env update --prefix $(ENV_PREFIX) --file environment.yml --prune

# Run parser/unit tests without writing __pycache__ files into the source tree.
test:
	PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests

# Run the Scrapy crawler and refresh results/items.json plus results/whots_metadata.json.
crawl:
	cd src/whots_metadata && scrapy crawl whotsmetadata -O ../../results/items.json

clean-bytecode:
	find src tests -name __pycache__ -type d -prune -exec rm -rf {} +
