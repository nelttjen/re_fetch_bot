import logging
import os

from aiogram import executor

from bot.bot_core import dispatcher, DEFAULT_USERS


def init_logger():
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger()
    logger_handler = logging.StreamHandler()
    logger.addHandler(logger_handler)
    logger.removeHandler(logger.handlers[0])

    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s: %(message)s")
    logger_handler.setFormatter(formatter)


def init():
    if not os.path.exists('./users.txt'):
        with open('./users.txt', 'w') as f:
            f.write(DEFAULT_USERS)
    init_logger()
    import bot.bot_handlers


if __name__ == '__main__':
    init()
    executor.start_polling(dispatcher, skip_updates=True)