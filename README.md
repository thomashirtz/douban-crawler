# douban-crawler

This repository contain a very simple crawler for retrieving movies from the site douban. This is a modified version of [this](https://github.com/jctian96/douban-web-crawler) webcrawler. Therefore, all the credits goes to [jctian96](https://github.com/jctian96). I decided to keep the core code of his crawler but simplify it to get the data crawled directly into dataframes. 

## Crawler principle

The principle is to create a query on this webpage [https://movie.douban.com/j/new_search_subjects?](https://movie.douban.com/j/new_search_subjects?) with some search queries such as type, rating score, etc.  
The different query can be found using this url [https://movie.douban.com/tag/#/](https://movie.douban.com/tag/#/). By selecting a query it is possible to know how to change the URL to affine the research. To combine several tags, for example '中国大陆' and '电视剧', a comma need to be used '中国大陆,电视剧'  

the different tags and tags are :
* Types: 电影,电视剧,综艺,动画,纪录片,短片
* Genres: 剧情,爱情,喜剧,科幻,动作,悬疑,犯罪,恐怖,青春,励志,战争,文艺,黑色,幽默,传记,情色,暴力,音乐,家庭
* Region: 大陆,美国,香港,台湾,日本,韩国,英国,法国,德国,意大利,西班牙,印度,泰国,俄罗斯,伊朗,加拿大,澳大利亚,爱尔兰,瑞典,巴西,丹麦
* Features: 经典,冷门佳片,魔幻,黑帮,女性

Many pages on douban have some sort of mitigation to crawl. The page will not load before a certain action is taken. The use of the previously mentionned link is very useful to avoid this issue.  
Moreover, if you sort by "Recent" as I generally do, there is a lot of TV shows without any rating, using the query "rating" with a value superior to 0 allows to avoid the issue of downloading Material that doesn't have any rating.

It does not seem possible to choose several tags per category. For example it is not possible to choose "电影,电视剧", it will only search one of them (The first one I believe). However it is possible to choose '电影,美国' since 'Movie and United States does not belong to the same category.
