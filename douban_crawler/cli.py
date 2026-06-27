import argparse
import sys

from douban_crawler import default
from douban_crawler.core import crawl


def add_crawl_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-q", "--query-tags", default=default.QUERY_TAGS, help=default.QUERY_TAGS_HELP)
    parser.add_argument("-r", "--rating-range", default=default.RATING_RANGE, help=default.RATING_RANGE_HELP)
    parser.add_argument(
        "-s", "--sorting-preference", default=default.SORTING_PREFERENCE, help=default.SORTING_PREFERENCE_HELP
    )
    parser.add_argument("-o", "--output", default=default.OUTPUT_PATH, help="Output JSONL file path")
    parser.add_argument(
        "--delay",
        type=float,
        default=default.REQUEST_DELAY,
        help=f"Min random pause between search pages (max ~×{default.DELAY_MAX_FACTOR}, see default.py)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=default.MAX_WORKERS,
        help="Parallel mobile detail fetches per search page",
    )


def run_crawl(args: argparse.Namespace) -> None:
    crawl(
        output_path=args.output,
        sort=args.sorting_preference,
        tags=args.query_tags,
        rating_range=args.rating_range,
        delay=args.delay,
        workers=args.workers,
    )


def run_crawl_argv(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Crawler for the movie.douban.com website",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    add_crawl_args(parser)
    args = parser.parse_args(argv)
    run_crawl(args)


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="dc", description="Douban crawler and dashboard")
    sub = parser.add_subparsers(dest="command", required=True)

    crawl_parser = sub.add_parser(
        "crawl",
        help="Crawl movies to JSONL",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    add_crawl_args(crawl_parser)

    dash_parser = sub.add_parser("dashboard", help="Open the filter dashboard")
    dash_parser.add_argument("--port", type=int, default=8050)
    dash_parser.add_argument("--no-debug", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "crawl":
        run_crawl(args)
    elif args.command == "dashboard":
        from douban_crawler.dashboard import run

        run(debug=not args.no_debug, port=args.port)


if __name__ == "__main__":
    main()
