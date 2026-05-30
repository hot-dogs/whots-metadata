"""Parse WHOTS metadata from the WHOI WHOTS data page.

The parser is intentionally independent of Scrapy so it can be tested directly
and reused by downstream projects such as HOT Forecast.
"""

from __future__ import annotations

from datetime import UTC, datetime
from html import unescape
import re
from typing import Any
from urllib.parse import urljoin


SOURCE_URL = "https://uop.whoi.edu/currentprojects/WHOTS/whotsdata.html"
DATA_URL = "https://uop.whoi.edu/currentprojects/WHOTS/data/"
SCHEMA_VERSION = "whots-metadata.v1"


ROMAN_VALUES = {
    "M": 1000,
    "D": 500,
    "C": 100,
    "L": 50,
    "X": 10,
    "V": 5,
    "I": 1,
}


def parse_whots_metadata(
    html: str,
    *,
    source_url: str = SOURCE_URL,
    scraped_at_utc: str | None = None,
    data_index_html: str | None = None,
    data_url: str = DATA_URL,
) -> dict[str, Any]:
    """Return structured WHOTS metadata parsed from a WHOTS HTML page."""

    scraped_at_utc = scraped_at_utc or _utc_now()
    deployments = _parse_deployments(html, source_url)
    current = deployments[0] if deployments else None
    previous = deployments[1] if len(deployments) > 1 else None
    location_text = _deployment_location_text(html)

    if current and location_text:
        current["deployment_location_text"] = location_text

    metadata = {
        "schema_version": SCHEMA_VERSION,
        "source_url": source_url,
        "data_directory_url": data_url,
        "scraped_at_utc": scraped_at_utc,
        "page_last_updated": _page_last_updated(html),
        "ndbc_station_id": _ndbc_station_id(html),
        "current": current,
        "previous": previous,
        "deployments": deployments,
        "source_health": {
            "whots_page": {"status": "OK", "url": source_url},
            "data_directory": {"status": "NOT_CHECKED", "url": data_url},
        },
        "warnings": [],
    }

    if data_index_html:
        attach_position_sources(metadata, data_index_html, data_url=data_url)

    return refresh_warnings(metadata)


def legacy_items_from_metadata(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the historical ``results/items.json`` shape.

    Existing users expect a list containing ``CURRENT`` and ``PREVIOUS`` objects
    with ``number``, ``sys1``, ``sys2``, ``link1``, and ``link2`` keys. We keep
    those keys and append richer metadata for consumers that can use it.
    """

    items: list[dict[str, Any]] = []
    for key in ("current", "previous"):
        deployment = metadata.get(key)
        if not deployment:
            continue
        role = str(deployment["role"])
        item = {
            "number": _two_digit_number(deployment.get("number")),
            "sys1": deployment.get("sys1"),
            "sys2": deployment.get("sys2"),
            "link1": _legacy_non_qc_url(deployment.get("sys1_complete_url")),
            "link2": _legacy_non_qc_url(deployment.get("sys2_complete_url")),
            "deployment_label": deployment.get("deployment_label"),
            "roman": deployment.get("roman"),
            "deployed_utc": deployment.get("deployed_utc"),
            "deployment_location_text": deployment.get("deployment_location_text"),
            "ndbc_station_id": metadata.get("ndbc_station_id"),
            "page_last_updated": metadata.get("page_last_updated"),
            "sys1_daily_url": deployment.get("sys1_daily_url"),
            "sys2_daily_url": deployment.get("sys2_daily_url"),
            "sys1_complete_url": deployment.get("sys1_complete_url"),
            "sys2_complete_url": deployment.get("sys2_complete_url"),
            "plot_urls": deployment.get("plot_urls", []),
            "position_sources": deployment.get("position_sources", {}),
        }
        items.append({role: item})

    return items


def int_to_roman(number: int) -> str:
    """Convert a positive integer to an uppercase Roman numeral."""

    if number < 1:
        raise ValueError("Roman numerals require a positive integer")

    mapping = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    result = []
    remaining = number
    for value, numeral in mapping:
        count, remaining = divmod(remaining, value)
        result.append(numeral * count)
    return "".join(result)


def roman_to_int(numeral: str) -> int:
    """Convert a Roman numeral to an integer."""

    total = 0
    previous = 0
    for char in reversed(numeral.upper()):
        value = ROMAN_VALUES[char]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total


def attach_position_sources(
    metadata: dict[str, Any],
    data_index_html: str,
    *,
    data_url: str = DATA_URL,
) -> dict[str, Any]:
    """Attach WHOTS GPS/position source URLs discovered from the data directory."""

    entries = _data_directory_entries(data_index_html, data_url)
    metadata.setdefault("source_health", {})["data_directory"] = {
        "status": "OK",
        "url": data_url,
        "files_discovered": len(entries),
    }
    for deployment in metadata.get("deployments", []):
        roman = deployment.get("roman")
        if not roman:
            continue
        deployment["position_sources"] = _position_sources_for_roman(entries, roman)

    current = metadata.get("current")
    previous = metadata.get("previous")
    if current:
        current["position_sources"] = current.get("position_sources", {})
    if previous:
        previous["position_sources"] = previous.get("position_sources", {})
    return refresh_warnings(metadata)


def refresh_warnings(metadata: dict[str, Any]) -> dict[str, Any]:
    """Refresh metadata warnings from the current parsed source state."""

    metadata["warnings"] = _warnings(metadata.get("deployments", []), metadata=metadata)
    return metadata


def parse_latest_position(text: str) -> dict[str, Any] | None:
    """Parse the latest latitude/longitude row from a WHOTS position text file."""

    latest: dict[str, Any] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("%"):
            continue
        parsed = _parse_position_row(stripped)
        if not parsed:
            continue
        if latest is None or parsed["sort_key"] >= latest["sort_key"]:
            latest = parsed

    if not latest:
        return None
    latest.pop("sort_key", None)
    return latest


def _data_directory_entries(html: str, data_url: str) -> dict[str, dict[str, str | None]]:
    entries: dict[str, dict[str, str | None]] = {}
    pattern = re.compile(
        r'<tr[^>]*>.*?<a\s+href=["\'](?P<href>[^"\']+)["\'][^>]*>.*?</a>'
        r'</td><td[^>]*>\s*(?P<modified>[^<]*)\s*</td><td[^>]*>\s*(?P<size>[^<]*)\s*</td>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(html):
        href = unescape(match.group("href"))
        if href.startswith("?") or href.startswith("/"):
            continue
        entries[href] = {
            "file_name": href,
            "url": urljoin(data_url, href),
            "last_modified": _clean_text(match.group("modified")) or None,
            "size": _clean_text(match.group("size")) or None,
        }
    return entries


def _position_sources_for_roman(
    entries: dict[str, dict[str, str | None]],
    roman: str,
) -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    prefix = f"WHOTS-{roman}_"
    for file_name, entry in entries.items():
        if not file_name.startswith(prefix) or not file_name.endswith(".txt"):
            continue
        raw_name = file_name.removeprefix(prefix).removesuffix(".txt")
        is_end_file = raw_name.endswith("_end")
        source_name = raw_name.removesuffix("_end")
        source_key = source_name.lower()
        if source_key not in {"melo", "rover", "beacon", "argos_gps", "sable"}:
            continue

        source = sources.setdefault(
            source_key,
            {
                "kind": source_key,
                "url": None,
                "file_name": None,
                "last_modified": None,
                "size": None,
                "end_url": None,
                "end_file_name": None,
                "end_last_modified": None,
                "end_size": None,
            },
        )
        if is_end_file:
            source["end_url"] = entry["url"]
            source["end_file_name"] = entry["file_name"]
            source["end_last_modified"] = entry["last_modified"]
            source["end_size"] = entry["size"]
        else:
            source["url"] = entry["url"]
            source["file_name"] = entry["file_name"]
            source["last_modified"] = entry["last_modified"]
            source["size"] = entry["size"]
    return dict(sorted(sources.items()))


def _parse_position_row(line: str) -> dict[str, Any] | None:
    parts = line.split()
    if len(parts) < 7:
        return None
    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
    except ValueError:
        return None

    try:
        if ":" in parts[3]:
            hour, minute, second = (int(value) for value in parts[3].split(":"))
            yearday = float(parts[4])
            latitude = float(parts[5])
            longitude = float(parts[6])
            consumed = 7
        else:
            hour = int(parts[3])
            minute = int(parts[4])
            second = 0
            latitude = float(parts[5])
            longitude = float(parts[6])
            yearday = float(parts[7]) if len(parts) > 7 else None
            consumed = 8
    except (ValueError, IndexError):
        return None

    timestamp = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
    result: dict[str, Any] = {
        "timestamp": timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "yearday": yearday,
        "raw": line,
        "sort_key": (year, month, day, hour, minute, second, yearday or 0.0),
    }
    if len(parts) > consumed:
        result["extra_fields"] = parts[consumed:]
    if len(parts) >= 11 and parts[-1].isdigit():
        result["device_id"] = parts[-1]
    return result


def _parse_deployments(html: str, source_url: str) -> list[dict[str, Any]]:
    deployments: list[dict[str, Any]] = []
    for match in _deployment_blocks(html):
        label = match.group("label")
        number = int(match.group("number"))
        block = match.group("block")
        roman = int_to_roman(number)
        complete_links = _logger_links(block, source_url, suffix="QC.txt")
        daily_links = _logger_links(block, source_url, suffix="QC_daily.txt")

        deployments.append(
            {
                "role": "CURRENT" if not deployments else "PREVIOUS",
                "deployment_label": label,
                "number": number,
                "roman": roman,
                "deployed_utc": _deployed_utc(block),
                "deployment_location_text": None,
                "sys1": _logger_name(complete_links, daily_links, 1),
                "sys2": _logger_name(complete_links, daily_links, 2),
                "sys1_daily_url": _logger_url(daily_links, 1),
                "sys2_daily_url": _logger_url(daily_links, 2),
                "sys1_complete_url": _logger_url(complete_links, 1),
                "sys2_complete_url": _logger_url(complete_links, 2),
                "plot_urls": _plot_urls(block, source_url, roman),
                "position_sources": {},
            }
        )

    return deployments


def _deployment_blocks(html: str) -> list[re.Match[str]]:
    pattern = re.compile(
        r"(?P<block><tr[^>]*>\s*<td[^>]*>\s*"
        r"<strong>\s*(?P<label>WHOTS-(?P<number>\d+))\s*</strong>"
        r".*?</tr>)",
        re.IGNORECASE | re.DOTALL,
    )
    return list(pattern.finditer(html))


def _logger_links(
    block: str,
    source_url: str,
    *,
    suffix: str,
) -> dict[int, dict[str, str]]:
    links: dict[int, dict[str, str]] = {}
    pattern = re.compile(
        r'<a[^>]+href=["\'](?P<href>[^"\']*WHOTS-[^"\']*MET_sys(?P<sys>[12])'
        + re.escape(suffix)
        + r')["\'][^>]*>(?P<text>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(block):
        sys_number = int(match.group("sys"))
        links[sys_number] = {
            "name": _clean_text(match.group("text")),
            "url": urljoin(source_url, match.group("href")),
        }
    return links


def _plot_urls(block: str, source_url: str, roman: str) -> list[str]:
    urls: list[str] = []
    pattern = re.compile(r'<a[^>]+href=["\'](?P<href>[^"\']+)["\']', re.IGNORECASE)
    for match in pattern.finditer(block):
        href = match.group("href")
        href_lower = href.lower()
        if f"whots-{roman.lower()}" not in href_lower:
            continue
        if "whotsplot" not in href_lower and "images/" not in href_lower:
            continue
        url = urljoin(source_url, href)
        if url not in urls:
            urls.append(url)
    return urls


def _deployed_utc(block: str) -> str | None:
    text = _clean_text(block)
    match = re.search(r"Deployed:\s*([^<]*?\bUTC)", text, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1).strip()
    for fmt in ("%B %d, %Y at %H:%M UTC", "%b %d, %Y at %H:%M UTC"):
        try:
            parsed = datetime.strptime(raw, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
        return parsed.isoformat().replace("+00:00", "Z")
    return raw


def _page_last_updated(html: str) -> str | None:
    text = _clean_text(html)
    match = re.search(r"Last updated:\s*(\d{4}/\d{2}/\d{2})", text, re.IGNORECASE)
    return match.group(1) if match else None


def _ndbc_station_id(html: str) -> str | None:
    match = re.search(r"station=([0-9A-Za-z]+)", html, re.IGNORECASE)
    return match.group(1).upper() if match else None


def _deployment_location_text(html: str) -> str | None:
    text = _clean_text(html)
    match = re.search(
        r"WHOTS\s+\d+\s+buoy was deployed.*?at approximately\s+(.+?)(?:\.|$)",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _warnings(
    deployments: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> list[str]:
    warnings: list[str] = []
    if metadata:
        data_directory = metadata.get("source_health", {}).get("data_directory", {})
        data_status = data_directory.get("status")
        if data_status == "NOT_CHECKED":
            warnings.append("WHOTS data directory was not checked; position_sources may be empty.")
        elif data_status != "OK":
            warnings.append("WHOTS data directory could not be fetched; position_sources may be empty.")
    if not deployments:
        return warnings + ["No WHOTS deployment rows were found."]
    for deployment in deployments[:2]:
        label = deployment.get("deployment_label", "UNKNOWN")
        for key in (
            "sys1",
            "sys2",
            "sys1_daily_url",
            "sys2_daily_url",
            "sys1_complete_url",
            "sys2_complete_url",
        ):
            if not deployment.get(key):
                warnings.append(f"{label}: missing {key}")
    return warnings


def _logger_name(
    complete_links: dict[int, dict[str, str]],
    daily_links: dict[int, dict[str, str]],
    sys_number: int,
) -> str | None:
    return (
        complete_links.get(sys_number, {}).get("name")
        or daily_links.get(sys_number, {}).get("name")
    )


def _logger_url(links: dict[int, dict[str, str]], sys_number: int) -> str | None:
    return links.get(sys_number, {}).get("url")


def _legacy_non_qc_url(url: str | None) -> str | None:
    if not url:
        return None
    return url.replace("QC.txt", ".txt")


def _two_digit_number(number: object) -> str | None:
    if number is None:
        return None
    return f"{int(number):02d}"


def _clean_text(html: str) -> str:
    html = re.sub(r"<br\s*/?>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    return " ".join(unescape(text).split())


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
