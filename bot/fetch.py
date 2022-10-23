import csv
import logging
import os
import requests
import pyquery as pq


from .bot_buttons import get_start_keyboard


def check_folder():
    if not os.path.exists('results'):
        os.mkdir('results')


def link_generator(pages, start) -> str:
    endpoint = 'https://www.mangaupdates.com/series.html'
    errors = 0
    args = {
        'page': 0,
        'perpage': 100,
        'orderby': 'rating'
    }
    for i in range(start, pages + 1):
        print(f'iter: {i}')
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


async def get_chapters_link(source):
    response = requests.get(source)
    if response.status_code != 200:
        return None, None
    query_main = pq.PyQuery(response.text)
    elements = query_main.find(".sContent > a").items()
    names = list(query_main.find('.sContent').items())[3].text().split('\n')
    original_name = query_main.find('.releasestitle.tabletitle').text()
    for elem in elements:
        # print(elem.attr('href'))
        if elem.attr('href').startswith('https://www.mangaupdates.com/releases.html?search=') and \
                '&stype=series' in elem.attr('href'):
            return elem.attr('href'), names, original_name
    return None, None, None


async def get_series_id(link):
    return link.replace('https://www.mangaupdates.com/releases.html?', '').split('&')[0].split('=')[1]


async def get_chapter_info(series_id):
    link = f'https://www.mangaupdates.com/releases.html?search={series_id}&perpage=100&stype=series'
    response = requests.get(link)
    if response.status_code != 200:
        return None, None
    query = pq.PyQuery(response.text)
    with open('test.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    ratings = list(query.find('.col-1.text.text-center > span').items())
    volumes = [item for i, item in enumerate(query.find('.col-1.text.text-center').items())
               if i % 2 == 0 and item.text()]
    _volumes = []
    for item in volumes:
        try:
            _volumes.append(int(item.text()))
        except ValueError:
            continue
    curr_array = []
    for i in range(len(ratings)):
        item = ratings[i]
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
        return None, None
    if _volumes:
        max_volume = max(_volumes)
    else:
        max_volume = 0
    return max(curr_array), max_volume


async def find_remanga(orig_name):
    endpoint = f'https://api.remanga.org/api/search/?query={orig_name}&count=8&field=titles&page=1'
    response = requests.get(endpoint).json()
    items = []
    for item in response['content']:
        title_id = item['id']
        title_eng = item['en_name'].lower()
        chapters = item['count_chapters']
        _dir = item['dir']
        items.append({
            'title_id': title_id,
            'title_eng': title_eng,
            'chapters': chapters,
            'dir': _dir
        })
    return items


async def compare_remanga(names, chapter, remanga_items, required_rating=0.51) -> list:
    items_return = []

    for item in remanga_items:
        max_rating = 0.0
        name = item['title_eng']
        for mu_name in names:
            list_of_words = mu_name.lower().split(' ')
            count = 0
            for word in list_of_words:
                if word in name:
                    count += 1
            cur_rating = count / len(list_of_words)
            max_rating = max(max_rating, cur_rating)
        if max_rating >= required_rating:
            chapters_re = item['chapters']
            if chapters_re > chapter:
                items_return.append(item)
    return items_return


async def generate_csv(list1, list2, volumes):

    def generate_rows(list_data, list_to):
        for item in list_data:
            orinigal_name = item['orig_name'].replace(',', '')
            orig_link = item['link']
            orig_chaps = item['max_chaps']
            for row in item['remanga_data']:
                title_id = row['title_id']
                title_re = row['title_eng'].replace(',', '')
                chapters_re = row['chapters']
                dir_re = 'https://remanga.org/manga/' + row['dir']
                list_to.append([orinigal_name, title_re, orig_chaps, chapters_re, title_id, dir_re, orig_link])

    rows = []
    first_row = ['Оригинальное навание', 'Название remanga',
                 'Оригинальое кол-во глав', 'Кол-во глав Remanga', 'ID remanga', 'DIR remanga', 'Ссылка оригинал']
    delim_row = ['======', '======', '======', f'Количество томов больше чем {volumes}', '======', '======', '======']

    rows.append(first_row)
    generate_rows(list1, rows)
    rows.append(delim_row)
    rows.append(first_row)
    generate_rows(list2, rows)
    with open('output.csv', 'w', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerows(rows)


async def perform_check(start_page=1, pages=9999, max_vol=3, percent=0.51, msg=None, bot=None):
    check_folder()
    links = link_generator(start=start_page, pages=pages)
    items_less, items_more = [], []
    for item in links:
        # name берется с ссылки
        # original_name = ' '.join(item.split('/')[-1].split('-'))
        # со страницы
        try:
            chapter_link, all_names, original_name = await get_chapters_link(item)
        except Exception as e:
            logging.error(f'{item} - ERROR: get_chapters_link: {e}')
            continue
        if not chapter_link:
            logging.warning(f'{item} - No chapter link, skipping')
            continue

        series_id = await get_series_id(chapter_link)
        logging.info(f'{item} - series_id: {series_id}')

        try:
            chapter, max_volume = await get_chapter_info(series_id)
        except Exception as e:
            logging.error(f'{item} - ERROR: get_chapter_info: {e}')
            continue
        if not chapter:
            logging.warning(f'{item} - Can`t find latest chapter, skipping')
            continue
        logging.info(f'{item} - latest chapter is: {chapter}')

        try:
            remanga_data = await find_remanga(orig_name=original_name)
        except Exception as e:
            logging.error(f'{item} - ERROR: find_remanga: {e}')
            continue

        try:
            result = await compare_remanga(all_names, chapter, remanga_data, required_rating=percent)
        except Exception as e:
            logging.error(f'{item} - ERROR: compare_remanga: {e}')
            continue
        if result:
            __dict = {
                'link': item,
                'orig_name': original_name,
                'max_chaps': chapter,
                'remanga_data': result
            }
            if max_volume > max_vol:
                items_more.append(__dict)
            else:
                items_less.append(__dict)
    await generate_csv(items_less, items_more, max_vol)
    await msg.reply('Проверка завершена, отправка файла...', reply_markup=get_start_keyboard())
    with open('output.csv', 'rb') as file:
        await bot.send_document(msg.from_user.id, file)