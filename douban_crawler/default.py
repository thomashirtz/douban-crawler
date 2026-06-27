from pathlib import Path

QUERY_TAGS = "华语,电视剧"
RATING_RANGE = None
SORTING_PREFERENCE = "T"

# ponytail: repo root, not cwd — so data never lands inside douban_crawler/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = str(PROJECT_ROOT / "data" / "movies.jsonl")

USER_AGENT = "learning_chinese_with_movies"
REQUEST_TIMEOUT = 30
REQUEST_RETRIES = 5
MAX_WORKERS = 4

# random pause between normal requests (seconds)
DELAY_MIN = 1.5
DELAY_MAX = 4.0
# random pause before retry after an error
RETRY_DELAY_MIN = 3.0
RETRY_DELAY_MAX = 12.0

# legacy CLI --delay sets minimum; max = delay * DELAY_MAX_FACTOR
DELAY_MAX_FACTOR = 2.5
REQUEST_DELAY = DELAY_MIN

QUERY_TAGS_HELP = """Tags used for the query. It is possible to choose 0 or 1 tag from each list.
The tags need to be separated by commas.

Types: 电影,电视剧,综艺,动画,纪录片,短片
Genres: 剧情,爱情,喜剧,科幻,动作,悬疑,犯罪,恐怖,青春,励志,战争,文艺,
        黑色,幽默,传记,情色,暴力,音乐,家庭
Region: 大陆,美国,香港,台湾,日本,韩国,英国,法国,德国,意大利,西班牙,
        印度,泰国,俄罗斯,伊朗,加拿大,澳大利亚,爱尔兰,瑞典,巴西,丹麦
Features: 经典,冷门佳片,魔幻,黑帮,女性

'中国大陆,电视剧' is a valid set of query tags.
"""

RATING_RANGE_HELP = """Rating range used for the queries.

The rating range must be specified this way: 'low,high'
Setting 0 as the lower bound will discard any movie that has no rating yet.

'5,10' is a valid rating range.
"""

SORTING_PREFERENCE_HELP = """Sorting preferences. Need to be chosen among several choices:

Highest amount of rating: 'T'
Highest rating: 'S'
Latest release: 'R'
Recently popular: 'U'

'U' is a valid sorting preference.
"""
