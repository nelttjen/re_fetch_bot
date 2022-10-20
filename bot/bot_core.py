from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

try:
    with open('token.txt', 'r', encoding='utf-8') as token_f:
        data = token_f.read()
except FileNotFoundError:
    raise Exception('Please create token.txt file with bot token in core folder')
if not data:
    raise Exception('token.txt file must contain bot token')

bot = Bot(token=data)
storage = MemoryStorage()
dispatcher = Dispatcher(bot, storage=storage)

DEFAULT_USERS = '474761641;648711203'
