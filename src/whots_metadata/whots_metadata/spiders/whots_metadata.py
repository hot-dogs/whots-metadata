import json
from pathlib import Path

import scrapy

from ..items import WhotsMetadataItem
from ..parser import (
    DATA_URL,
    SOURCE_URL,
    attach_position_sources,
    legacy_items_from_metadata,
    parse_whots_metadata,
    refresh_warnings,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
RICH_OUTPUT_PATH = PROJECT_ROOT / "results" / "whots_metadata.json"


class WhotsMetadataSpider(scrapy.Spider):
    name = "whotsmetadata"
    start_urls = [SOURCE_URL]

    def parse(self, response):
        metadata = parse_whots_metadata(response.text, source_url=response.url)
        yield scrapy.Request(
            DATA_URL,
            callback=self.parse_data_index,
            errback=self.data_index_failed,
            cb_kwargs={"metadata": metadata},
        )

    def parse_data_index(self, response, metadata):
        attach_position_sources(metadata, response.text, data_url=response.url)
        yield from self.emit_outputs(metadata)

    def data_index_failed(self, failure):
        metadata = failure.request.cb_kwargs["metadata"]
        metadata.setdefault("source_health", {})["data_directory"] = {
            "status": "MISSING",
            "url": DATA_URL,
            "error": failure.getErrorMessage(),
        }
        refresh_warnings(metadata)
        self.log(metadata["warnings"][-1], level=scrapy.log.WARNING)
        yield from self.emit_outputs(metadata)

    def emit_outputs(self, metadata):
        self._write_rich_metadata(metadata)

        for warning in metadata["warnings"]:
            self.log(warning, level=scrapy.log.WARNING)

        for legacy_item in legacy_items_from_metadata(metadata):
            role, payload = next(iter(legacy_item.items()))
            self.log(
                f"{role}: WHOTS-{payload.get('number')} "
                f"{payload.get('sys1')} / {payload.get('sys2')}"
            )
            yield {role: WhotsMetadataItem(payload)}

    def _write_rich_metadata(self, metadata):
        RICH_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RICH_OUTPUT_PATH.write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
