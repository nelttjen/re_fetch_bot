import logging
import os
import requests
import pyquery as pq


def check_folder():
    if not os.path.exists('results'):
        os.mkdir('results')


def link_generator(start=1) -> str:
    endpoint = 'https://www.mangaupdates.com/series.html'
    errors = 0
    args = {
        'page': 0,
        'perpage': 100,
        'orderby': 'rating'
    }
    for i in range(start, 9999):
        print(f'iter {i}')
        args['page'] = i
        response = requests.get(endpoint, params=args)
        if response.status_code == 400:
            break
        if response.status_code != 200:
            errors += 1
            logging.error(f'Page {i}: ERROR')
            continue
        query = pq.PyQuery(response.text)
        elements = query.find('.d-flex.flex-column.h-100 > .text > a').items()
        for item in elements:
            link = item.attr('href')
            yield link


def get_chapters_link(source):
    response = requests.get(source)
    if response.status_code != 200:
        return None
    query_main = pq.PyQuery(response.text)
    elements = query_main.find(".sContent > a").items()
    for elem in elements:
        # print(elem.attr('href'))
        if elem.attr('href').startswith('https://www.mangaupdates.com/releases.html?search=') and \
                '&stype=series' in elem.attr('href'):
            return elem.attr('href')
    return None


def get_series_id(link):
    return link.replace('https://www.mangaupdates.com/releases.html?', '').split('&')[0].split('=')[1]


def get_latest_chapter(series_id):
    link = f'https://www.mangaupdates.com/releases.html?search={series_id}&perpage=100&stype=series'
    response = requests.get(link)
    if response.status_code != 200:
        return None
    query = pq.PyQuery(response.text)
    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    ratings = list(query.find('.col-1.text.text-center > span').items())[::1]
    curr_array = []
    for item in ratings:
        if item.text():
            if '-' in item.text():
                real_text = item.text().split('-')[1]
            else:
                real_text = item.text()
            real_chapter = ''
            for char in real_text:
                if char in '0123456789':
                    real_chapter += char
                else:
                    break
            if real_chapter:
                curr_array.append(int(real_chapter))
    if not curr_array:
        return None
    return max(curr_array)


async def perform_check():
    check_folder()
    links = link_generator(start=1)
    for item in links:
        # name берется с ссылки
        original_name = ' '.join(item.split('/')[-1].split('-'))
        chapter_link = get_chapters_link(item)
        if not chapter_link:
            logging.warning(f'{item} - No chapter link, skipping')
            continue
        series_id = get_series_id(chapter_link)
        logging.info(f'{item} - series_id: {series_id}')
        chapter = get_latest_chapter(series_id)
        if not chapter:
            logging.warning(f'{item} - Can`t find latest chapter, skipping')
            continue
        logging.info(f'{item} - latest chapter is: {chapter}')