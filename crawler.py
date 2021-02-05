import re
import json
import time
import requests
from lxml import etree
import argparse

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy import create_engine, Column, Integer, String, Float


# Parser
query_tags_help = """Tags used for the query. It is possible to choose 0 or 1 tag from each list.
The tags need to be separated by commas.

Types: 电影,电视剧,综艺,动画,纪录片,短片
Genres: 剧情,爱情,喜剧,科幻,动作,悬疑,犯罪,恐怖,青春,励志,战争,文艺,
        黑色,幽默,传记,情色,暴力,音乐,家庭
Region: 大陆,美国,香港,台湾,日本,韩国,英国,法国,德国,意大利,西班牙,
        印度,泰国,俄罗斯,伊朗,加拿大,澳大利亚,爱尔兰,瑞典,巴西,丹麦
Features: 经典,冷门佳片,魔幻,黑帮,女性

'中国大陆,电视剧' is a valid set of query tags.

"""

rating_range_help = """ Rating range used for the queries.

The rating range must be specified this way: 'low,high'
Setting 0 as the lower bound will discard any movie that has no rating yet.

'5,10' is a valid rating range.

"""

sorting_preference_help = """ Sorting preferences. Need to be chosen among several choices:

Highest amount of rating: 'T'
Highest rating: 'S'
Latest release: 'R'
Recently popular: 'U'

'U' is a valid sorting preference.
"""

parser = argparse.ArgumentParser(description='Crawler for the movie.douban.com website',
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-q', '--query-tags', type=str, metavar='', help=query_tags_help, default='中国大陆,电视剧')
parser.add_argument('-r', '--rating-range', type=str, metavar='', help=rating_range_help, default=None)
parser.add_argument('-s', '--sorting-preference', type=str, metavar='', help=sorting_preference_help, default='R')
args = parser.parse_args()


Base = declarative_base()


class Movie(Base):
    __tablename__ = "movie"

    id = Column('id', Integer, primary_key=True)
    title = Column('title', String, index=True)
    rate = Column('rate', Float)
    url = Column('url', String)
    actors = Column('actors', String)
    genres = Column('genres', String)
    directors = Column('directors', String)
    script_writers = Column('script_writers', String)
    rating_people = Column('rating_people', String)
    initial_release_date = Column('initial_release_date', String, index=True)
    production_countries_regions = Column('production_countries_regions', String)

    def __repr__(self):
        return f"<Movie(id='{self.id}', name='{self.title}', initial_release_date='{self.initial_release_date}')>"


def database_initialization(database_name, echo: bool = False, drop_all=False):
    engine_url = f"sqlite:///{database_name}.db"
    engine = create_engine(engine_url, echo=echo)
    if drop_all:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine


def silent_insert(session, instance):
    try:
        session.add(instance)
        session.commit()
    except (IntegrityError, InvalidRequestError):
        print("Instance already present in the table")


# Change the user agent name before starting crawling
request_headers = {'User-Agent': 'learning_chinese_with_movies'}


def main(sorting_preference, query_tags, rating_range):
    counter = 0
    session, _ = database_initialization(database_name='database', drop_all=True)

    while True:
        start_offset = counter*20
        search_page_url = "https://movie.douban.com/j/new_search_subjects?"
        query_string = {
            'sort': sorting_preference,
            'tags': query_tags,
            'range': rating_range,
            'start': start_offset
        }

        response = requests.get(url=search_page_url, params=query_string, headers=request_headers)
        parsed_response = json.loads(response.text)

        if not any(parsed_response['data']):
            print("--------------- No more movies ---------------")
            break

        for movie in parsed_response['data']:
            # Send a GET request to the page of each movie.
            movie_page = requests.get(url=movie['url'], headers=request_headers)
            structure = etree.HTML(movie_page.text)

            # Extract the title, the url and audience rating of the movie from the search page.
            data = {'title': movie['title'], 'rate': movie['rate'], 'url': movie['url']}

            # Some art works do not have one or more of the following properties that need to be extracted from the movie page.
            keys = ['rating_people', 'directors', 'script_writers', 'actors', 'genres', 'production_countries_regions', 'initial_release_date']
            for key in keys:
                data[key] = ''

            # Extract the following additional information from the movie page using xpath and regular expressions
            try:
                data['rating_people'] = structure.xpath('//a[@class="rating_people"]/span/text()')[0]
            except: pass
            try:
                data['directors'] = structure.xpath('//div[@id="info"]/span/span/a[@rel="v:directedBy"]/text()')
            except: pass
            try:
                data['script_writers'] = structure.xpath('//div[@id="info"]/span[position()=2]/span[position()=2]/a/text()')
            except: pass
            try:
                data['actors'] = structure.xpath('//div[@id="info"]/span[@class="actor"]/span[@class="attrs"]/a/text()')
            except: pass
            try:
                data['genres'] = structure.xpath('//div[@id="info"]/span[@property="v:genre"]/text()')
            except: pass
            try:
                data['production_countries_regions'] = re.findall(pattern='制片国家/地区:</span>(.*?)<br/>', string=movie_page.text, flags=re.S)[0]
            except: pass
            try:
                initial_release_date_raw = structure.xpath('//div[@id="info"]/span[@property="v:initialReleaseDate"]/text()')[0]
                data['initial_release_date'] = re.search(pattern=r'(\d{4}-\d{2}-\d{2})|(\d{4}-\d{2})', string=initial_release_date_raw).group()
            except: pass

            for key in ['actors', 'genres', 'directors', 'script_writers']:
                data[key] = str(data[key])

            # Print out some information in the console to keep track of the progress.
            print(data['title'], data['rate'], data['rating_people'], data['directors'], data['genres'], data['production_countries_regions'], data['initial_release_date'])

            # Insert the instance to the database
            silent_insert(session, Movie(**data))
            time.sleep(0.1)

        counter += 1


if __name__ == '__main__':
    main(sorting_preference=args.sorting_preference, query_tags=args.query_tags, rating_range=args.rating_range)
