import unittest

from whots_metadata.parser import (
    int_to_roman,
    legacy_items_from_metadata,
    parse_latest_position,
    parse_whots_metadata,
    roman_to_int,
)


HTML = """
<html><body>
<div id="content3">
<table class="notebox">
<tr><td><strong>WHOTS-21</strong><br />
Deployed: September 24, 2025 at 00:53 UTC<br />
<strong>Met data text files:</strong><br />
Daily transmission:
<a href="data/WHOTS-XXI_MET_sys1QC_daily.txt">Logger 5</a>
<a href="data/WHOTS-XXI_MET_sys2QC_daily.txt">Logger 42</a><br />
Complete listing:
<a href="data/WHOTS-XXI_MET_sys1QC.txt">Logger 5</a>
<a href="data/WHOTS-XXI_MET_sys2QC.txt">Logger 42</a><br />
<a href="whotsplot.html?images/WHOTS-XXI_MET_p1QC_all.png">plot-1</a>
</td></tr>
<tr><td><strong>WHOTS-20</strong><br />
Deployed: June 2, 2024 at 03:47 UTC<br />
Daily transmission:
<a href="data/WHOTS-XX_MET_sys1QC_daily.txt">Logger 3</a>
<a href="data/WHOTS-XX_MET_sys2QC_daily.txt">Logger 8</a><br />
Complete listing:
<a href="data/WHOTS-XX_MET_sys1QC.txt">Logger 3</a>
<a href="data/WHOTS-XX_MET_sys2QC.txt">Logger 8</a><br />
</td></tr>
</table>
<p>WHOTS 21 buoy was deployed from the R/V Sette on September 24, 2025 at
00:53 UTC at approximately 22&deg; 46&acute; N 158&deg; W.</p>
<a href="https://www.ndbc.noaa.gov/station_page.php?station=51wh0&unit=M&tz=GMT">NDBC</a>
<span class="caption"><i>Last updated:  2026/05/28</i></span>
</div>
</body></html>
"""


DATA_INDEX_HTML = """
<html><body><table>
<tr><td><a href="WHOTS-XXI_Melo.txt">WHOTS-XXI_Melo.txt</a></td><td align="right">2026-05-29 21:31  </td><td align="right"> 73K</td></tr>
<tr><td><a href="WHOTS-XXI_Melo_end.txt">WHOTS-XXI_Melo_end.txt</a></td><td align="right">2026-05-29 21:31  </td><td align="right">595 </td></tr>
<tr><td><a href="WHOTS-XXI_Rover.txt">WHOTS-XXI_Rover.txt</a></td><td align="right">2026-05-29 12:11  </td><td align="right"> 53K</td></tr>
<tr><td><a href="WHOTS-XXI_Rover_end.txt">WHOTS-XXI_Rover_end.txt</a></td><td align="right">2026-05-29 12:11  </td><td align="right">488 </td></tr>
<tr><td><a href="WHOTS-XXI_beacon.txt">WHOTS-XXI_beacon.txt</a></td><td align="right">2025-12-18 17:44  </td><td align="right">343 </td></tr>
<tr><td><a href="WHOTS-XX_Melo.txt">WHOTS-XX_Melo.txt</a></td><td align="right">2025-12-18 17:44  </td><td align="right">158K</td></tr>
<tr><td><a href="WHOTS-XX_Melo_end.txt">WHOTS-XX_Melo_end.txt</a></td><td align="right">2025-12-18 17:44  </td><td align="right">594 </td></tr>
</table></body></html>
"""


MELO_END = """
% year mon day hr min    Latitude   Longitude    yearday
  2026   5  29 17  30   22.773601 -157.911346 514.729167
  2026   5  29 21  30   22.773208 -157.906738 514.895833
"""


ROVER_END = """
% year mo dy hr mn    latitude   longitude   yday      msg# BatV snrMx    imei
  2026  5 29 12  1   22.772080 -157.912080  514.50069  2728 1581    44 4530420
  2026  5 29 12  1   22.772110 -157.912080  514.50071  2292 1587    42 4530400
"""


class WhotsParserTests(unittest.TestCase):
    def test_parses_current_previous_and_page_metadata(self):
        metadata = parse_whots_metadata(
            HTML,
            source_url="https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html",
            scraped_at_utc="2026-05-29T00:00:00Z",
        )

        self.assertEqual(metadata["schema_version"], "whots-metadata.v1")
        self.assertEqual(metadata["page_last_updated"], "2026/05/28")
        self.assertEqual(metadata["ndbc_station_id"], "51WH0")
        self.assertEqual(
            metadata["warnings"],
            ["WHOTS data directory was not checked; position_sources may be empty."],
        )

        current = metadata["current"]
        self.assertEqual(current["role"], "CURRENT")
        self.assertEqual(current["number"], 21)
        self.assertEqual(current["roman"], "XXI")
        self.assertEqual(current["deployed_utc"], "2025-09-24T00:53:00Z")
        self.assertEqual(current["sys1"], "Logger 5")
        self.assertEqual(current["sys2"], "Logger 42")
        self.assertEqual(
            current["sys1_daily_url"],
            "https://uop.whoi.edu/currentprojects/WHOTS/data/WHOTS-XXI_MET_sys1QC_daily.txt",
        )
        self.assertEqual(
            current["sys1_complete_url"],
            "https://uop.whoi.edu/currentprojects/WHOTS/data/WHOTS-XXI_MET_sys1QC.txt",
        )
        self.assertEqual(
            current["plot_urls"],
            [
                "https://uop.whoi.edu/currentprojects/WHOTS/whotsplot.html?images/WHOTS-XXI_MET_p1QC_all.png"
            ],
        )
        self.assertEqual(current["deployment_location_text"], "22\u00b0 46\u00b4 N 158\u00b0 W")

        previous = metadata["previous"]
        self.assertEqual(previous["role"], "PREVIOUS")
        self.assertEqual(previous["number"], 20)
        self.assertEqual(previous["sys1"], "Logger 3")
        self.assertEqual(previous["sys2"], "Logger 8")

    def test_legacy_items_keep_original_contract(self):
        metadata = parse_whots_metadata(HTML, scraped_at_utc="2026-05-29T00:00:00Z")
        items = legacy_items_from_metadata(metadata)

        self.assertEqual(items[0]["CURRENT"]["number"], "21")
        self.assertEqual(items[0]["CURRENT"]["sys1"], "Logger 5")
        self.assertEqual(
            items[0]["CURRENT"]["link1"],
            "https://uop.whoi.edu/currentprojects/WHOTS/data/WHOTS-XXI_MET_sys1.txt",
        )
        self.assertEqual(items[1]["PREVIOUS"]["number"], "20")
        self.assertIn("sys1_complete_url", items[0]["CURRENT"])

    def test_discovers_position_sources_from_data_index(self):
        metadata = parse_whots_metadata(
            HTML,
            scraped_at_utc="2026-05-29T00:00:00Z",
            data_index_html=DATA_INDEX_HTML,
        )

        self.assertEqual(metadata["source_health"]["data_directory"]["status"], "OK")
        self.assertEqual(metadata["warnings"], [])

        sources = metadata["current"]["position_sources"]
        self.assertEqual(
            sources["melo"]["end_url"],
            "https://uop.whoi.edu/currentprojects/WHOTS/data/WHOTS-XXI_Melo_end.txt",
        )
        self.assertEqual(
            sources["rover"]["url"],
            "https://uop.whoi.edu/currentprojects/WHOTS/data/WHOTS-XXI_Rover.txt",
        )
        self.assertEqual(
            sources["beacon"]["url"],
            "https://uop.whoi.edu/currentprojects/WHOTS/data/WHOTS-XXI_beacon.txt",
        )
        self.assertIn("melo", metadata["previous"]["position_sources"])


    def test_data_directory_warning_when_not_checked(self):
        metadata = parse_whots_metadata(HTML, scraped_at_utc="2026-05-29T00:00:00Z")

        self.assertEqual(metadata["source_health"]["data_directory"]["status"], "NOT_CHECKED")
        self.assertEqual(
            metadata["warnings"],
            ["WHOTS data directory was not checked; position_sources may be empty."],
        )

    def test_parses_latest_position_rows(self):
        melo = parse_latest_position(MELO_END)
        self.assertEqual(melo["timestamp"], "2026-05-29T21:30:00")
        self.assertEqual(melo["latitude"], 22.773208)
        self.assertEqual(melo["longitude"], -157.906738)

        rover = parse_latest_position(ROVER_END)
        self.assertEqual(rover["timestamp"], "2026-05-29T12:01:00")
        self.assertEqual(rover["latitude"], 22.772110)
        self.assertEqual(rover["device_id"], "4530400")

    def test_roman_round_trip(self):
        for number in (1, 4, 9, 19, 20, 21, 44, 99):
            self.assertEqual(roman_to_int(int_to_roman(number)), number)


if __name__ == "__main__":
    unittest.main()
