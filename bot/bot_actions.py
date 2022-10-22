import os.path

import requests


def add_user(new_user: int) -> None:
    user_list = get_current_user_list()
    user_list.append(str(new_user))
    with open('users.txt', 'w', encoding='utf-8') as out:
        out.write(';'.join(user_list))


def get_current_user_list():
    with open('users.txt', 'r', encoding='utf-8') as file:
        user_list = file.read().split(';')
    return user_list


def check_user_access(user_id: int) -> bool:
    return str(user_id) in get_current_user_list()


def test_func():
    endpoint = 'https://api.mangaupdates.com/v1/releases/search'
    payload = {
        "search": "",
        "search_type": "series",
        "page": 1,
        "perpage": 1000,
        "orderby": "date",
    }
    response = requests.post(endpoint, json=payload)
    with open('test.json', 'w', encoding='utf-8') as f:
        f.write(response.text)