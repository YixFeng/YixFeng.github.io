#!/usr/bin/env python3
import argparse
import datetime as dt
import html
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


SCHOLAR_HOSTS = (
    "scholar.google.com",
    "scholar.google.co.uk",
    "scholar.google.ca",
    "scholar.google.com.au",
)
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
)


def clean_number(value):
    return int(re.sub(r"[^\d]", "", value))


def fetch_profile_once(user, host, user_agent):
    query = urllib.parse.urlencode({"user": user, "hl": "en", "pagesize": 100})
    request = urllib.request.Request(
        f"https://{host}/citations?{query}",
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": user_agent,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_profile(user, attempts=2):
    errors = []
    for attempt in range(attempts):
        for host in SCHOLAR_HOSTS:
            try:
                return fetch_profile_once(user, host, random.choice(USER_AGENTS))
            except (urllib.error.URLError, TimeoutError) as exc:
                errors.append(f"{host}: {exc}")
        if attempt + 1 < attempts:
            time.sleep(2 ** attempt)
    raise RuntimeError("; ".join(errors))


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
    parser.add_argument(
        "--keep-existing-on-error",
        action="store_true",
        help="Keep a valid existing output file and exit successfully when Scholar is unavailable",
    )
    args = parser.parse_args()

    try:
        data = parse_profile(fetch_profile(args.user))
    except (RuntimeError, ValueError) as exc:
        if args.keep_existing_on_error:
            try:
                with open(args.output, encoding="utf-8") as handle:
                    existing = json.load(handle)
                if all(key in existing for key in ("total", "hIndex", "years", "perYear")):
                    print(
                        "::warning title=Google Scholar unavailable::"
                        f"Keeping citation data from {existing.get('updated', 'the previous run')}. {exc}"
                    )
                    return 0
            except (OSError, ValueError, TypeError):
                pass
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
