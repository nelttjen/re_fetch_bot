import asyncio

import pyquery as pq

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from .bot_core import dispatcher, bot, DEFAULT_USERS
from .bot_actions import check_user_access, add_user, test_func
from .fetch import perform_check
from .bot_buttons import get_start_keyboard, get_cancel_keyboard


class Stages(StatesGroup):
    id_wait = State()

    ask_start_stop = State()
    ask_percent = State()
    ask_volume = State()


user_info = {}


def login_required(func):
    async def wraps(message: types.Message):
        if not check_user_access(message.from_user.id):
            await message.reply('Доступ запрещен', reply_markup=types.ReplyKeyboardRemove())
            return
        await func(message)

    return wraps


@dispatcher.message_handler(commands='start', state='*')
@login_required
async def start(message: types.Message):
    await message.reply('Вы авторизованы!', reply_markup=get_start_keyboard())


@dispatcher.message_handler(commands='cancel', state='*')
@dispatcher.message_handler(Text('отмена', ignore_case=True), state='*')
async def cancel_inputs(message: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await message.reply('Главное меню', reply_markup=get_start_keyboard())


@dispatcher.message_handler(commands='add_user', state='*')
@dispatcher.message_handler(Text(equals='Добавить пользователя в бота', ignore_case=True), state='*')
@login_required
async def new_user_call(message: types.Message):
    if str(message.from_user.id) not in DEFAULT_USERS.split(';'):
        await message.reply('Эта функция вам недоступна. Свяжитесь с администраторами бота.')
        return
    await Stages.id_wait.set()
    await message.reply('Добавить пользователя по ID\n\nID можно узнать: @getmyid_bot, @username_to_id_bot',
                        reply_markup=get_cancel_keyboard())


@dispatcher.message_handler(state=Stages.id_wait)
async def add_by_user_id(message: types.Message, state: FSMContext):
    try:
        add_user(int(message.text))
        await state.finish()
        await message.reply('Пользователь добавлен.', reply_markup=get_start_keyboard())
    except ValueError:
        await message.reply('ID должно быть числом')


@dispatcher.message_handler(commands='fetch', state='*')
@dispatcher.message_handler(Text(equals='Начать проверку', ignore_case=True), state='*')
@login_required
async def start_fetch_call(message: types.Message):
    await Stages.ask_start_stop.set()
    await message.reply('Выберите сколько страниц нужно спарсить. (1 страница - 100 тайтлов)\n'
                        'Формат ввода: начало-конец\n'
                        'Пример: 1-4\n'
                        'Значение по умолчанию: все', reply_markup=get_cancel_keyboard())
    fetch_data = {
        'start': 1,
        'stop': 9999,
        'percent': 0.51,
        'max_vol': 3,
    }
    global user_info
    user_info[message.from_user.id] = fetch_data


@dispatcher.message_handler(state=Stages.ask_start_stop)
async def start_stop_call(message: types.Message, state: FSMContext):
    try:
        __start, __stop = list(map(int, message.text.split('-')))
        global user_info
        user_info[message.from_user.id]['start'] = __start
        user_info[message.from_user.id]['stop'] = __stop
        await state.finish()
        await Stages.ask_percent.set()
        await message.reply('Введите процент совпадения названия с названием Реманги.\n'
                            'Напрмер: 0.5 или 50% - 1 слово из 2, 0.25 или 25% - 1 слово из 4\n'
                            'Формат ввода: чилло 0.0-1.0 или число 0-100 с знаком % на конце\n'
                            'Пример: 0.5 или 50%\n'
                            'Значение по умолчанию: 0.51')
    except ValueError:
        await message.reply('Неправильный формать ввода\n'
                            'Формат ввода: начало-конец\n '
                            'Пример: 1-4')


@dispatcher.message_handler(state=Stages.ask_percent)
async def percent_call(message: types.Message, state: FSMContext):
    if message.text.endswith('%'):
        try:
            percent = int(message.text[:-1])
            assert 0 <= percent <= 100
            percent /= 100
        except (ValueError, AssertionError):
            await message.reply('Неправильный формат ввода\n'
                                'Формат ввода: чилло 0.0-1.0 или число 0-100 с знаком % на конце\n'
                                'Пример: 0.5 или 50%\n')
            return
    else:
        try:
            percent = float(message.text)
            assert 0 <= percent <= 1.0
        except (ValueError, AssertionError):
            await message.reply('Неправильный формат ввода\n'
                                'Формат ввода: чилло 0.0-1.0 или число 0-100 с знаком % на конце\n'
                                'Пример: 0.5 или 50%\n')
            return
    global user_info
    user_info[message.from_user.id]['percent'] = percent
    await state.finish()
    await message.reply('Введите максимальное количество томов, которые будут помещены вверх.\n'
                        'Если количество томов больше, чем заданое число, тайтл будет помещен в нижний блок\n'
                        'Формат ввода: целое число, >= 0\n'
                        'Значение по умолчанию: 3')
    await Stages.ask_volume.set()


@dispatcher.message_handler(state=Stages.ask_volume)
async def run_after_volume(message: types.Message, state: FSMContext):
    try:
        max_vol = int(message.text)
        assert max_vol >= 0
        global user_info
        user_info[message.from_user.id]['max_vol'] = max_vol

        await state.finish()
        await message.reply('Проверка началась. Вы получите csv файл по окончанию проверки. '
                            'Во время выполнения бот будет недоступен. Пожалуйста, подождите...', reply_markup=types.ReplyKeyboardRemove())
        payload = user_info[message.from_user.id]
        __start, __stop, __percent, __max_vol = payload['start'], payload['stop'], payload['percent'], payload[
            'max_vol']
        await perform_check(start_page=__start, pages=__stop, max_vol=__max_vol, percent=__percent,
                            msg=message, bot=bot)

    except (ValueError, AssertionError):
        await message.reply('Неправильный формат ввода\n'
                            'Формат ввода: целое число, >= 0\n')


# @dispatcher.message_handler(commands='fetch', state='*')
# @dispatcher.message_handler(Text(equals='Начать проверку', ignore_case=True), state='*')
# @login_required
# async def start_fetch(message: types.Message):
#     if running.get(message.from_user.id):
#         await message.reply('Проверка уже запущена. Пожалуйста, дождитесь её завершения')
#         return

#     running[message.from_user.id] = True
#     try:
#         asyncio.create_task(perform_check())
#         # result = await perform_check()
#         await bot.send_message(message.from_user.id, 'Про')
#     except Exception as e:
#         await message.reply('При проверке что-то пошло не так :(')
#         running[message.from_user.id] = False
#         print(e)


@dispatcher.message_handler(commands='test', state='*')
@login_required
async def test_func_call(message: types.Message):
    test_func()
