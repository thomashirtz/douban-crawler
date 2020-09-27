import requests
import json
import re
import pandas as pd
from lxml import etree
import time
import pickle


# Change the user agent name before starting crawling
request_headers = {'User-Agent': 'learning_chinese_with_tv_shows'}

# Sorting parameters
query_tags = '中国大陆,电视剧'
rating_range = '5,10'
sorting_preference = 'R'

# Saving paramters
filename = 'recent_tvshows.pkl'
saving_frequency = 2


def pickle_data(file_name, data):
    with open(file_name, 'wb') as f:
        pickle.dump(data, f)


def main():
    counter = 0
    data_list = []

    while True:
        start_offset = counter*20
        search_page_url = "https://movie.douban.com/j/new_search_subjects?"
        query_string = {
            'sort': sorting_preference,
            'tags': query_tags,
            'start': start_offset,
            'range': rating_range
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

            # Print out some information in the console to keep track of the progress.
            print(data['title'], data['rate'], data['rating_people'], data['directors'], data['genres'], data['production_countries_regions'], data['initial_release_date'])

            # Append the movie to the list
            data_list.append(pd.DataFrame([data], columns=list(data.keys())))
            time.sleep(0.1)

        counter += 1

        # Save progress to a pickle file
        if counter % saving_frequency == 0:
            print("--------------- Saving Data ---------------")
            pickle_data(filename, pd.concat(data_list, ignore_index=True))


if __name__ == '__main__':
    main()
