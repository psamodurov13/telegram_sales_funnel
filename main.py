import time
from loguru import logger
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import filters
from config import *
from markups import *
from aiogram.dispatcher import FSMContext
from utils import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, timedelta
import asyncio

logger.add('debug.log', format='{time} {level} {message}', level='INFO', rotation='15MB', compression='zip')
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def interval_schedule(message, post_info, interval):
    '''Функция отправки поста с определенным интервалом'''
    logger.info(f'INTERVAL SCHEDULE STARTED')
    await asyncio.sleep(interval)
    await send_post(message, post_info)


async def get_next_post(message, user_info, next_post_count):
    '''Функция для получения следующего поста'''
    logger.info(f'GET NEXT POST STARTED')
    post_info = get_post(user_info['telegram_id'], next_post_count)
    logger.info(f'POST INFO - {post_info}')
    return post_info


async def increase_count(message, count):
    '''Функция изменяющая текущий шаг у пользователя'''
    user_info = edit('users', 'telegram_id', message.chat.id, 'current_step', count)
    logger.info(f'COUNT WAS INCREASED')
    return user_info


async def to_next_post(message, count):
    '''Функция перехода к следующему посту'''
    user_info = await increase_count(message, count)
    post_info = await get_next_post(message, user_info, user_info['current_step'])
    if post_info['timer']:
        interval = post_info['timer']
    elif post_info['time']:
        post_time = datetime.strptime(post_info['time'], '%H:%M').time()
        now_time = datetime.now().time()
        if post_time > now_time:
            today = datetime.today()
            post_date_time = datetime(today.year, today.month, today.day, post_time.hour, post_time.minute)
        else:
            tomorrow = datetime.today() + timedelta(days=1)
            post_date_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, post_time.hour, post_time.minute)
        interval = post_date_time.timestamp() - time.time()
    else:
        interval = 60
        logger.debug(f'DEFAULT INTERVAL FOR {post_info}')
    logger.info(f'INTERVAL - {interval}')
    asyncio.create_task(interval_schedule(message, post_info, interval))


async def fill_name(text, name, for_change='{first_name}'):
    '''Функция заполнения имени в посте'''
    if for_change in text:
        text = text.replace(for_change, name)
    return text


async def add_tags(telegram_id, tag_list):
    user_info = get_user(telegram_id)
    logger.info(f'USER INFO {user_info}')
    for i in tag_list:
        columns_values = {
            'user_id': user_info['id'],
            'tag_id': i['tag_id']
        }
        logger.info(f'COLUMNS VALUES {columns_values}')
        insert('users_tags', columns_values)
        logger.info(f'TAG {i} WAS ADDED FOR USER {telegram_id}')


async def send_post(message, post_info):
    '''Функция отправки поста'''
    if post_info['buttons']:
        keyboard = get_keyboard(post_info['buttons'])
    else:
        keyboard = None
    if post_info['emoji']:
        await message.answer(post_info['emoji'])
    if post_info['photo'] or post_info['video']:
        if post_info['photo']:
            path_to_media = f'media/photo/{post_info["photo"]}'
            message_function = bot.send_photo
        elif post_info['video']:
            path_to_media = f'media/video/{post_info["video"]}'
            message_function = bot.send_video
        else:
            path_to_media = None
            message_function = None
        if path_to_media:
            with open(path_to_media, 'rb') as file:
                media_file = file.read()
        else:
            media_file = None
        if post_info['text']:
            caption = await fill_name(post_info['text'], message.chat.first_name)
        else:
            caption = None
        logger.info(f'POST DATA - {path_to_media} / {message_function} / {caption}')
        if message_function:
            await message_function(message.chat.id, media_file, caption=caption, parse_mode='HTML', reply_markup=keyboard)
    elif post_info['text']:
        text = await fill_name(post_info['text'], message.chat.first_name)
        await message.answer(text, parse_mode='HTML', reply_markup=keyboard)
    elif post_info['audio']:
        with open(f'media/audio/{post_info["audio"]}', 'rb') as file:
            await message.answer_audio(file)
    if post_info['add_tags_id']:
        await add_tags(message.chat.id, post_info['add_tags_id'])
    if post_info['default_next']:
        await to_next_post(message, post_info['default_next'])
        return


@dp.message_handler(commands='start')
async def start(message: types.Message, state: FSMContext):
    '''Функция выдающая ответ на команду start'''
    username = message.from_user['username']
    first_name = message.from_user['first_name']
    last_name = message.from_user['last_name']
    full_name = message.from_user.full_name
    logger.info(f'USERNAME - {username}, FIRST NAME - {first_name}, LAST NAME - {last_name}, FULL NAME - {full_name}')
    user_info = add_user(
        message.from_user['id'],
        message.from_user['username'],
        message.from_user['first_name'],
        message.from_user['last_name'],
        message.from_user.full_name,
    )
    post_info = get_post(user_info['telegram_id'])
    await send_post(message, post_info)


@dp.message_handler(content_types=['text'])
async def process_text_message(message: types.Message):
    '''Функция обработки текстовых сообщений'''
    post_info = get_post(message.from_user.id, 1000)
    await send_post(message, post_info)


@dp.message_handler(filters.IDFilter(user_id=ADMIN_TELEGRAM_ID), commands=['admin'])
async def get_users_count(message: types.Message):
    await message.answer('Меню администратора', reply_markup=get_admin_menu())


@dp.callback_query_handler(cd_next_post.filter())
async def bot_callback_next_post(callback: types.CallbackQuery, callback_data: dict):
    logger.info(f'CALLBACK DATA IN HANDLER - {callback}')
    post_info = get_post(callback['from']['id'], callback_data.get('next_post'))
    logger.info(f'POST INFO - {post_info}')
    await send_post(callback.message, post_info)

@logger.catch()
def main():
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()





