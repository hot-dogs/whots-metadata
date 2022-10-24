import scrapy
from ..items import WhotsMetadataItem

URL = "https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html"

BUOY_CSS = {
    "CURRENT": {
        "WHOTS_NUMBER": {"tr_nth-child": 2},
        "WHOTS_SYS1": {"a_nth-child": 9},
        "WHOTS_SYS2": {"a_nth-child": 10},
    },

    "PREVIOUS": {
        "WHOTS_NUMBER": {"tr_nth-child": 3},
        "WHOTS_SYS1": {"a_nth-child": 10},
        "WHOTS_SYS2": {"a_nth-child": 11},
    }
}

SELECTOR = 'div#content3 > div > div:nth-child(4) > table:nth-child(1)'
TR_SELECTOR = " tr:nth-child("


class WhotsScrapy(scrapy.Spider):
    name = 'whotsmetadata'
    start_urls = [
        URL
    ]

    def parse(self, response):
        items = WhotsMetadataItem()
        main_selector = response.css(SELECTOR)
        for keys, values in BUOY_CSS.items():
            number = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > strong:nth-child(1)::text").extract_first()[-2:]

            sys1 = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS1"]["a_nth-child"]) +
                ")::text").extract_first()

            sys2 = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS2"]["a_nth-child"]) +
                ")::text").extract_first()

            link1 = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS1"]["a_nth-child"]) +
                ")::attr(href)").extract_first()[:-6] + '.txt'

            link2 = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS2"]["a_nth-child"]) +
                ")::attr(href)").extract_first()[:-6] + '.txt'

            items["number"] = number
            items["sys1"] = sys1
            items["sys2"] = sys2
            items["link1"] = (URL[:-14] + link1)
            items["link2"] = (URL[:-14] + link2)

            yield {keys: items}

