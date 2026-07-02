#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.request


SCHOLAR_URL = "https://scholar.google.com/citations?user={user}&hl=en"


def clean_number(value):
    return int(re.sub(r"[^\d]", "", value))


def fetch_profile(user):
    request = urllib.request.Request(
        SCHOLAR_URL.format(user=user),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_profile(page):
    meta_match = re.search(r"Cited by\s*([\d,]+)", page)
    stats = [
        clean_number(html.unescape(value))
        for value in re.findall(r'<td class="gsc_rsb_std">([^<]+)</td>', page)
    ]
    total = clean_number(meta_match.group(1)) if meta_match else (stats[0] if stats else 0)
    h_index = stats[2] if len(stats) >= 3 else 0

    years = [
        clean_number(value)
        for value in re.findall(r'<span class="gsc_g_t"[^>]*>(\d{4})</span>', page)
    ]
    per_year = [
        clean_number(html.unescape(value))
        for value in re.findall(r'<span class="gsc_g_al">([^<]+)</span>', page)
    ]

    if not years or not per_year:
        raise ValueError("Could not parse citation history from Google Scholar profile")

    n = min(len(years), len(per_year))
    return {
        "updated": dt.date.today().isoformat(),
        "total": total,
        "hIndex": h_index,
        "years": years[:n],
        "perYear": per_year[:n],
    }


def main():
    parser = argparse.ArgumentParser(description="Update local Google Scholar citation stats JSON.")
    parser.add_argument("--user", default="gfAtyY4AAAAJ", help="Google Scholar user id")
    parser.add_argument("--output", default="data/citations.json", help="Output JSON path")
    args = parser.parse_args()

    try:
        data = parse_profile(fetch_profile(args.user))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"Failed to update citations: {exc}", file=sys.stderr)
        return 1

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")

    print(
        "Updated citation stats: "
        f"{data['total']} citations, h-index {data['hIndex']}, "
        f"{len(data['years'])} yearly bars"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
