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


running = {}


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
@login_required
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
@login_required
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
async def start_fetch(message: types.Message):
    if running.get(message.from_user.id):
        await message.reply('Проверка уже запущена. Пожалуйста, дождитесь её завершения')
    await message.reply('Проверка началась. Вы получите csv файл по окончанию проверки. Пожалуйста, подождите...')
    running[message.from_user.id] = True
    try:
        result = await perform_check()
        await bot.send_message(message.from_user.id, 'Про')
    except Exception as e:
        await message.reply('При проверке что-то пошло не так :(')
        running[message.from_user.id] = False
        print(e)


@dispatcher.message_handler(commands='test', state='*')
@login_required
async def test_func_call(message: types.Message):
    test_func()