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
        "WHOTS_SYS1": {"a_nth-child": 9 },
        "WHOTS_SYS2": {"a_nth-child": 10},
    }
}

SELECTOR = 'div#content3 > div > div:nth-child(4) > table:nth-child(1)'
TR_SELECTOR = " tr:nth-child("

class WhotsMetadataSpider(scrapy.Spider):
    name = 'whotsmetadata'
    start_urls = [
        URL
    ]

    def parse(self, response):
        items = WhotsMetadataItem()
        main_selector = response.css(SELECTOR)
        
        if not main_selector:
            self.log("Main selector is None", level=scrapy.log.ERROR)
            return
        
        for keys, values in BUOY_CSS.items():
            number_selector = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > strong:nth-child(1)::text"
            )
            number = number_selector.extract_first()
            if number:
                number = number[-2:]
            self.log(f"Number for {keys}: {number}")

            sys1_selector = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS1"]["a_nth-child"]) +
                ")::text"
            )
            sys1 = sys1_selector.extract_first()
            self.log(f"Sys1 for {keys}: {sys1}")

            sys2_selector = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS2"]["a_nth-child"]) +
                ")::text"
            )
            sys2 = sys2_selector.extract_first()
            self.log(f"Sys2 for {keys}: {sys2}")

            link1_selector = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS1"]["a_nth-child"]) +
                ")::attr(href)"
            )
            link1 = link1_selector.extract_first()
            if link1:
                link1 = link1[:-6] + '.txt'
            self.log(f"Link1 for {keys}: {link1}")

            link2_selector = main_selector.css(
                TR_SELECTOR +
                str(values["WHOTS_NUMBER"]["tr_nth-child"]) +
                ")" +
                "> td > a:nth-child(" +
                str(values["WHOTS_SYS2"]["a_nth-child"]) +
                ")::attr(href)"
            )
            link2 = link2_selector.extract_first()
            if link2:
                link2 = link2[:-6] + '.txt'
            self.log(f"Link2 for {keys}: {link2}")

            if number and sys1 and sys2 and link1 and link2:
                items["number"] = number
                items["sys1"] = sys1
                items["sys2"] = sys2
                items["link1"] = (URL[:-14] + link1)
                items["link2"] = (URL[:-14] + link2)
                yield {keys: items}
            else:
                self.log(f"Skipping {keys} due to missing data", level=scrapy.log.WARNING)

