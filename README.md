# douban-crawler

A simple crawler for [Douban movies](https://movie.douban.com). Modified from [jctian96/douban-web-crawler](https://github.com/jctian96/douban-web-crawler); credits to [jctian96](https://github.com/jctian96).

Results are stored as JSONL (no database). Browse and filter them in a small Dash dashboard.

## Setup

Dependencies are declared in [`pyproject.toml`](pyproject.toml). From the project root:

```bash
pip install -e .
```

This installs the package and registers the `dc` command.
## Usage

Edit defaults in [`douban_crawler/default.py`](douban_crawler/default.py), or override via CLI flags.

```bash
# Crawl → data/movies.jsonl
dc crawl

# Custom query
dc crawl -q 电影,美国 -s S -r 7,10

# Dashboard → http://127.0.0.1:8050
dc dashboard
```

Backward-compatible:

```bash
python -m douban_crawler          # same as dc crawl
python -m douban_crawler.cli dashboard
```

### CLI options (`dc crawl`)

| Flag | Default | Description |
|------|---------|-------------|
| `-q`, `--query-tags` | `华语,电视剧` | Comma-separated Douban tags |
| `-r`, `--rating-range` | none | e.g. `5,10` or `0,10` to skip unrated |
| `-s`, `--sorting-preference` | `T` | `T` (most ratings), `S` (highest), `R` (latest), `U` (recent) |
| `-o`, `--output` | `data/movies.jsonl` | Output file |
| `--workers` | `4` | Parallel mobile detail fetches per search page |
| `--delay` | `1.5` | Min random pause between pages (max ~×2.5) |

### Dashboard options (`dc dashboard`)

| Flag | Default | Description |
|------|---------|-------------|
| `--port` | `8050` | Port to listen on |
| `--no-debug` | off | Disable Dash debug/reloader |

## Tags

Pick 0 or 1 tag per category, comma-separated. See [Douban tag page](https://movie.douban.com/tag/#/) for combinations.

- **Types:** 电影, 电视剧, 综艺, 动画, 纪录片, 短片
- **Genres:** 剧情, 爱情, 喜剧, 科幻, 动作, 悬疑, 犯罪, 恐怖, 青春, 励志, 战争, 文艺, 黑色, 幽默, 传记, 情色, 暴力, 音乐, 家庭
- **Region:** 大陆, 美国, 香港, 台湾, 日本, 韩国, 英国, 法国, 德国, 意大利, 西班牙, 印度, 泰国, 俄罗斯, 伊朗, 加拿大, 澳大利亚, 爱尔兰, 瑞典, 巴西, 丹麦
- **Features:** 经典, 冷门佳片, 魔幻, 黑帮, 女性

Example: `中国大陆,电视剧` is valid. `电影,美国` is valid (different categories). `电影,电视剧` is not (same category).

## Notes

Each title is enriched via the mobile API (`m.douban.com/rexxar/api/v2/...`) for vote count, genres, country, and release date (+1 HTTP per movie, parallelized with `--workers`).

Change `USER_AGENT` in `default.py` before crawling. Each crawl overwrites the output file. Failed requests retry up to 5 times with random waits; tune `DELAY_MIN` / `DELAY_MAX` / `RETRY_DELAY_*` in `default.py` if Douban rate-limits you.

Output goes to `data/movies.jsonl` at the **project root** (next to `pyproject.toml`), not inside the package — works regardless of which directory you run `dc` from.

`script_writers` is not exposed by the mobile API.
