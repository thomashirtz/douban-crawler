import json
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from douban_crawler import default

SEARCH_URL = "https://movie.douban.com/j/new_search_subjects"
ABSTRACT_URL = "https://movie.douban.com/j/subject_abstract"
MOBILE_API = "https://m.douban.com/rexxar/api/v2/{kind}/{subject_id}"
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
)

_local = threading.local()


def _headers():
    return {"User-Agent": default.USER_AGENT, "Referer": "https://movie.douban.com/"}


def _mobile_headers(subject_id: str) -> dict:
    return {
        "User-Agent": MOBILE_UA,
        "Referer": f"https://m.douban.com/movie/subject/{subject_id}/",
    }


def _session() -> requests.Session:
    if not getattr(_local, "session", None):
        session = requests.Session()
        session.headers.update(_headers())
        _local.session = session
    return _local.session


def _random_pause(lo: float, hi: float) -> None:
    time.sleep(random.uniform(lo, hi))


def _retryable(err: Exception) -> bool:
    if isinstance(err, requests.HTTPError) and err.response is not None:
        return err.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(err, (requests.Timeout, requests.ConnectionError, json.JSONDecodeError, ValueError, TypeError))


def _get_json(
    url: str,
    params: dict | None = None,
    *,
    expect_key: str | None = None,
    headers: dict | None = None,
) -> dict:
    last_err: Exception | None = None
    for attempt in range(1, default.REQUEST_RETRIES + 1):
        try:
            _random_pause(default.DELAY_MIN * 0.2, default.DELAY_MAX * 0.4)
            response = _session().get(
                url, params=params, headers=headers, timeout=default.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            payload = json.loads(response.text)
            if not isinstance(payload, dict):
                raise ValueError(f"expected object, got {type(payload).__name__}")
            if expect_key is not None and expect_key not in payload:
                raise ValueError(f"missing {expect_key!r} in response: {str(payload)[:300]}")
            return payload
        except (requests.RequestException, json.JSONDecodeError, ValueError, TypeError) as err:
            last_err = err
            if not _retryable(err):
                raise
            print(f"request failed ({attempt}/{default.REQUEST_RETRIES}): {err}")
            if attempt < default.REQUEST_RETRIES:
                _random_pause(default.RETRY_DELAY_MIN, default.RETRY_DELAY_MAX)
    raise last_err  # type: ignore[misc]


def _try_mobile(subject_id: str, kind: str) -> dict | None:
    """Single mobile endpoint attempt; 400/404 = wrong kind, no retry spam."""
    url = MOBILE_API.format(kind=kind, subject_id=subject_id)
    last_err: Exception | None = None
    for attempt in range(1, default.REQUEST_RETRIES + 1):
        try:
            _random_pause(default.DELAY_MIN * 0.2, default.DELAY_MAX * 0.4)
            response = _session().get(
                url, headers=_mobile_headers(subject_id), timeout=default.REQUEST_TIMEOUT
            )
            if response.status_code in (400, 404):
                return None
            response.raise_for_status()
            payload = json.loads(response.text)
            if isinstance(payload, dict) and payload.get("id"):
                return payload
            return None
        except (requests.RequestException, json.JSONDecodeError) as err:
            if not _retryable(err):
                return None
            last_err = err
            if attempt < default.REQUEST_RETRIES:
                _random_pause(default.RETRY_DELAY_MIN, default.RETRY_DELAY_MAX)
    print(f"mobile {kind}/{subject_id} failed: {last_err}")
    return None


def _parse_rate(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _subject_id(search_item: dict) -> str:
    if search_item.get("id"):
        return str(search_item["id"])
    return search_item["url"].rstrip("/").split("/")[-1]


def _names(items) -> list[str]:
    if not items:
        return []
    if isinstance(items[0], dict):
        return [x["name"] for x in items if x.get("name")]
    return [str(x) for x in items]


def _parse_release_date(subject: dict) -> str:
    for raw in subject.get("pubdate") or subject.get("pubdates") or []:
        match = re.search(r"(\d{4}-\d{2}-\d{2})|(\d{4}-\d{2})", str(raw))
        if match:
            return match.group()
    year = subject.get("year")
    return str(year) if year else ""


def fetch_mobile_detail(subject_id: str) -> dict:
    for kind in ("tv", "movie"):
        payload = _try_mobile(subject_id, kind)
        if payload:
            return payload
    return {}


def _apply_mobile(data: dict, subject: dict) -> None:
    rating = subject.get("rating") or {}
    data["rate"] = _parse_rate(rating.get("value") or data["rate"])
    if rating.get("count") is not None:
        data["rating_people"] = str(rating["count"])
    data["genres"] = subject.get("genres") or []
    countries = subject.get("countries") or []
    data["production_countries_regions"] = ", ".join(countries)
    data["initial_release_date"] = _parse_release_date(subject)
    data["directors"] = _names(subject.get("directors")) or data["directors"]
    data["actors"] = _names(subject.get("actors")) or data["actors"]


def _apply_abstract(data: dict) -> None:
    payload = _get_json(ABSTRACT_URL, {"subject_id": data["douban_id"]})
    if payload.get("r") != 0:
        raise ValueError(f"abstract error: {payload.get('r')}")
    subject = payload.get("subject") or {}
    data["directors"] = subject.get("directors") or data["directors"]
    data["actors"] = subject.get("actors") or data["actors"]
    data["genres"] = subject.get("types") or []
    data["production_countries_regions"] = subject.get("region") or ""
    data["initial_release_date"] = subject.get("release_year") or ""
    data["rate"] = _parse_rate(subject.get("rate") or data["rate"])


def movie_from_search(search_item: dict) -> dict:
    return {
        "title": search_item["title"],
        "rate": _parse_rate(search_item.get("rate")),
        "url": search_item["url"],
        "directors": search_item.get("directors") or [],
        "script_writers": [],
        "actors": search_item.get("casts") or [],
        "genres": [],
        "production_countries_regions": "",
        "initial_release_date": "",
        "rating_people": "",
        "douban_id": _subject_id(search_item),
    }


def movie_from_apis(search_item: dict) -> dict:
    data = movie_from_search(search_item)
    try:
        subject = fetch_mobile_detail(data["douban_id"])
        if subject:
            _apply_mobile(data, subject)
        else:
            _apply_abstract(data)
    except Exception as err:
        print(f"enrich failed for {data['title']}: {err}, keeping search fields")
    return data


def enrich_batch(search_items: list[dict], workers: int) -> list[dict]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(movie_from_apis, search_items))


def fetch_page(start: int, sort: str, tags: str, rating_range: str | None) -> list[dict]:
    payload = _get_json(
        SEARCH_URL,
        {"sort": sort, "tags": tags, "range": rating_range, "start": start},
        expect_key="data",
    )
    data = payload.get("data")
    return data if isinstance(data, list) else []


def load_movies(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    movies = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                movies.append(json.loads(line))
    return movies


def crawl(
    output_path: str | Path | None = None,
    sort: str | None = None,
    tags: str | None = None,
    rating_range: str | None = None,
    delay: float | None = None,
    workers: int | None = None,
) -> None:
    output_path = Path(output_path or default.OUTPUT_PATH)
    sort = sort if sort is not None else default.SORTING_PREFERENCE
    tags = tags if tags is not None else default.QUERY_TAGS
    if rating_range is None:
        rating_range = default.RATING_RANGE
    delay_min = delay if delay is not None else default.DELAY_MIN
    delay_max = max(delay_min * default.DELAY_MAX_FACTOR, default.DELAY_MAX)
    workers = workers if workers is not None else default.MAX_WORKERS

    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen_urls: set[str] = set()
    counter = 0

    with output_path.open("w", encoding="utf-8") as out:
        while True:
            try:
                movies = fetch_page(counter * 20, sort, tags, rating_range)
            except Exception as err:
                print(f"search page {counter} failed: {err}")
                break

            if not movies:
                print("--------------- No more movies ---------------")
                break

            batch = [m for m in movies if m["url"] not in seen_urls]
            for data in enrich_batch(batch, workers):
                print(
                    data["title"],
                    data["rate"],
                    data["rating_people"],
                    data["directors"],
                    data["genres"],
                    data["production_countries_regions"],
                    data["initial_release_date"],
                )
                out.write(json.dumps(data, ensure_ascii=False) + "\n")
                seen_urls.add(data["url"])

            counter += 1
            _random_pause(delay_min, delay_max)
