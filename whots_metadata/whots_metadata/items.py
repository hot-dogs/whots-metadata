# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WhotsMetadataItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    number = scrapy.Field()
    sys1 = scrapy.Field()
    sys2 = scrapy.Field()
    link1 = scrapy.Field()
    link2 = scrapy.Field()
