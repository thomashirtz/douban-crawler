# douban-crawler

This repository contain a very simple crawler for retrieving movies from the site douban. This is a modified version of [this](https://github.com/jctian96/douban-web-crawler) webcrawler. Therefore all the credits goes to him. I decided to change some parts because 

The principle is to create a query on this webpage [https://movie.douban.com/j/new_search_subjects?](https://movie.douban.com/j/new_search_subjects?) with some search queries such as type, rate, etc.  
The different query can be found using this url [https://movie.douban.com/tag/#/](https://movie.douban.com/tag/#/). By selecting a query it is possible to know how to change the URL to affine the research. To combine several tags, for example '中国大陆' and '电视剧', a comma need to be used '中国大陆,电视剧'  
Many pages on douban have some sort of mitigation to crawl. The page will not load before a certain action is taken. The use of the previously mentionned link is very useful to avoid this issue.  
Moreover, if you sort by "Recent" as I generally do, there is a lot of TV shows without any rating, using the query "rating" with a value superior to 0 allows to avoid the issue of downloading Material that doesn't have any rating.

It does not seem possible to choose several tags per category. For example it is not possible to choose "电影,电视剧", it will only search one of them (The first one I believe). However it is possible to choose '电影,美国' since 'Movie and United States does not belong to the same category.
