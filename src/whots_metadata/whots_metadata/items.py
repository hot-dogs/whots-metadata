# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WhotsMetadataItem(scrapy.Item):
    # Legacy fields preserved for existing results/items.json consumers.
    number = scrapy.Field()
    sys1 = scrapy.Field()
    sys2 = scrapy.Field()
    link1 = scrapy.Field()
    link2 = scrapy.Field()

    # Rich metadata fields for downstream tools such as hot-forecast.
    deployment_label = scrapy.Field()
    deployment_location_text = scrapy.Field()
    deployed_utc = scrapy.Field()
    ndbc_station_id = scrapy.Field()
    page_last_updated = scrapy.Field()
    plot_urls = scrapy.Field()
    position_sources = scrapy.Field()
    roman = scrapy.Field()
    sys1_complete_url = scrapy.Field()
    sys1_daily_url = scrapy.Field()
    sys2_complete_url = scrapy.Field()
    sys2_daily_url = scrapy.Field()
