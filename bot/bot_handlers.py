import pyquery as pq

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext

from .bot_core import dispatcher, DEFAULT_USERS
from .bot_actions import check_user_access, add_user
from .bot_buttons import get_start_keyboard, get_cancel_keyboard


class Stages(StatesGroup):
    id_wait = State()


@dispatcher.message_handler(commands='start', state='*')
async def start(message: types.Message):
    requested_from = message.from_user.id
    if check_user_access(requested_from):
        await message.reply('Вы авторизованы!', reply_markup=get_start_keyboard())
        return
    await message.reply('Доступ запрещен')


@dispatcher.message_handler(commands='cancel', state='*')
@dispatcher.message_handler(Text('отмена', ignore_case=True), state='*')
async def cancel_inputs(message: types.Message, state: FSMContext):
    if await state.get_state() is not None:
        await state.finish()
    await message.reply('Главное меню', reply_markup=get_start_keyboard())


@dispatcher.message_handler(commands='add_user', state='*')
@dispatcher.message_handler(Text(equals='Добавить пользователя в бота', ignore_case=True), state='*')
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


@dispatcher.message_handler(commands='start_fetch', state='*')
@dispatcher.message_handler(Text(equals='Начать проверку', ignore_case=True), state='*')
def start_fetch(message: types.Message):
    pass