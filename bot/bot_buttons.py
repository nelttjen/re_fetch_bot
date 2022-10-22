from aiogram import types


def get_start_keyboard():
    keyb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('Добавить пользователя в бота')
    button2 = types.KeyboardButton('Начать проверку')
    button3 = types.KeyboardButton('/test')
    keyb.add(button)
    keyb.add(button2)
    keyb.add(button3)
    return keyb


def get_cancel_keyboard():
    keyb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel = types.KeyboardButton('Отмена')
    keyb.add(cancel)
    return keyb