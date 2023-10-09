import time

from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ContentType
from loguru import logger
from aiogram.utils.exceptions import BotBlocked
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import filters
from config import *
from markups import *
from aiogram.dispatcher import FSMContext
from utils import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, timedelta
import asyncio
from mailing_state import *
import random as rd

logger.add('debug.log', format='{time} {level} {message}', level='INFO', rotation='15MB', compression='zip')
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
debug_mode = False
base_media_path = '/Users/psamodurov13/PycharmProjects/manage_telegrambot/manage_telegrambot/media/'


async def interval_schedule(message, post_info, interval):
    '''Функция отправки поста с определенным интервалом'''
    logger.info(f'INTERVAL SCHEDULE STARTED')
    await asyncio.sleep(interval)
    await send_post(message, post_info)


async def get_next_post(message, user_info, next_post_count):
    '''Функция для получения следующего поста'''
    logger.info(f'GET NEXT POST STARTED')
    logger.info(f"MESSAGE {message}")
    bot_info = await message.bot.get_me()
    post_info = get_post(message['chat']['id'], bot_info['username'], next_post_count)
    logger.info(f'POST INFO - {post_info}')
    return post_info


async def increase_count(message, count):
    '''Функция изменяющая текущий шаг у пользователя'''
    logger.info(f'START INCREASE COUNT - {count}, {message}')
    bot_info = await message.bot.get_me()
    subscriber_id = get_subscriber_id(message["chat"]["id"])
    bot_id = get_bot_id(bot_info["username"])
    logger.info(f'BOT - {bot_info}')
    current_step_id = fetchall('bots_currentsteps', [], f'bot_id = {bot_id} and subscriber_id = {subscriber_id}')[0]['id']
    logger.info(f'CURRENT STEP ID - {current_step_id}')
    # post_id = get_post(message['from']['id'], )
    user_info = edit('bots_currentsteps', 'id', current_step_id, 'current_step', count)
    logger.info(f'COUNT WAS INCREASED')
    return user_info


async def to_next_post(message, count):
    '''Функция перехода к следующему посту'''
    user_info = await increase_count(message, count)
    post_info = await get_next_post(message, user_info, user_info['current_step'])
    logger.info(f'USER_INFO - {user_info}')
    logger.info(f'POST_INFO - {post_info}')
    if post_info['timer'] and not post_info['time']:
        interval = post_info['timer']
    elif post_info['time']:
        if debug_mode:
            correction_time = timedelta(minutes=150)
        else:
            correction_time = timedelta(minutes=0)
        post_time = (datetime.strptime(post_info['time'], '%H:%M') + correction_time).time()
        if post_info['timer']:
            min_interval = timedelta(seconds=post_info['timer'])
            post_date = (datetime.now() + min_interval).date()
            now_time = (datetime.now() + min_interval).time()
        else:
            post_date = datetime.now().date()
            now_time = datetime.now().time()
        logger.info(f'POST DATE - {post_date}')
        logger.info(f'NOW TIME - {now_time}')
        if post_time > now_time:
            today = post_date
            post_date_time = datetime(today.year, today.month, today.day, post_time.hour, post_time.minute)
        else:
            tomorrow = post_date + timedelta(days=1)
            post_date_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, post_time.hour, post_time.minute)
        interval = post_date_time.timestamp() - time.time() + rd.randint(10, 50)/10
    else:
        # if user_info['current_step'] == 1:
        #     interval = 1
        # else:
        #     interval = 60
        interval = 2
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
    current_tags = [i['tags_id'] for i in fetchall('bots_subscribers_tags', [], f'subscribers_id = {user_info["id"]}')]
    logger.info(f'CURRENT TAGS {current_tags}')
    for i in tag_list:
        columns_values = {
            'subscribers_id': user_info['id'],
            'tags_id': i['tags_id']
        }
        logger.info(f'COLUMNS VALUES {columns_values}')
        if i['tags_id'] not in current_tags:
            insert('bots_subscribers_tags', columns_values)
            logger.info(f'TAG {i} WAS ADDED FOR USER {telegram_id}')
        else:
            logger.info(f'TAG {i} WAS NOT ADDED FOR USER {telegram_id}')





async def send_mailing_post(telegram_id, mailing_info, test_mode=False):
    '''Функция отправки рассылки'''
    if mailing_info['button_text'] and mailing_info['button_url']:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(mailing_info['button_text'], url=mailing_info['button_url']))
    else:
        keyboard = None
    if mailing_info['photo'] or mailing_info['video']:
        if mailing_info['photo']:
            path_to_media = mailing_info['photo']
            message_function = bot.send_photo
        elif mailing_info['video']:
            path_to_media = mailing_info['video']
            message_function = bot.send_video
        else:
            path_to_media = None
            message_function = None
        if path_to_media:
            with open(path_to_media, 'rb') as file:
                media_file = file.read()
        else:
            media_file = None
        if mailing_info['text']:
            caption = mailing_info['text']
        else:
            caption = None
        logger.info(f'POST DATA - {path_to_media} / {message_function} / {caption}')
        if message_function:
            await message_function(telegram_id, media_file, caption=caption, parse_mode='HTML', reply_markup=keyboard)
    elif mailing_info['text']:
        text = mailing_info['text']
        await bot.send_message(telegram_id, text, parse_mode='HTML', reply_markup=keyboard)



async def launch_mailing(mailing_pk, data, interval, users_telegram_id_id):
    logger.info(f'INTERVAL SCHEDULE STARTED')
    await asyncio.sleep(interval)
    success_mails = 0
    errors_mails = 0
    for user_ids in users_telegram_id_id:
        try:
            await send_mailing_post(user_ids[0], data)
            column_values = {
                'mailing_id': mailing_pk,
                'user_id': user_ids[1],
                'result': 1,
            }
            time.sleep(rd.randint(10, 50)/10)
            insert('mailings_users', column_values)
            success_mails += 1
        except Exception:
            column_values = {
                'mailing_id': mailing_pk,
                'user_id': user_ids[1],
                'result': 0,
                'error': Exception.__name__
            }
            insert('mailings_users', column_values)
            errors_mails += 1
    return success_mails, errors_mails


@logger.catch()
def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)


bots_info = fetchall('bots_bot', [])
bots = []
dispatchers = []
logger.info(f'BOTS - {bots_info}')

# Создаем экземпляры ботов и диспетчеров для каждого токена
for bot_info in bots_info:
    bot = Bot(token=bot_info['token'])
    dispatcher = Dispatcher(bot)
    dispatcher.middleware.setup(LoggingMiddleware())
    bots.append(bot)
    dispatchers.append(dispatcher)

logger.info(f'BOTS - {bots}')
logger.info(f'DISP - {dispatchers}')

# Обработчики команд и сообщений для каждого бота
for dp in dispatchers:
    # @dp.message_handler(commands=['start'])
    # async def on_start(message: types.Message):
    #     await message.answer("Привет! Это один из ваших ботов.")
    async def send_post(message, post_info):
        '''Функция отправки поста'''
        logger.info(f'MESSAGE - {message}')
        logger.info(f'POST_INFO - {post_info}')
        if post_info['buttons']:
            keyboard = get_keyboard(post_info['buttons'])
        else:
            keyboard = None
        if post_info['emoji']:
            await message.answer(post_info['emoji'])
        if post_info['photo'] or post_info['video']:
            photos = []
            if post_info['photo']:
                if ',' in post_info['photo']:
                    photos.extend([f'media/photo/{i}' for i in post_info['photo'].split(',')])
                path_to_media = f'{base_media_path}{post_info["photo"]}'
                message_function = message.bot.send_photo
            elif post_info['video']:
                path_to_media = f'{base_media_path}{post_info["video"]}'
                message_function = message.bot.send_video
            else:
                path_to_media = None
                message_function = None
            if path_to_media and not photos:
                with open(path_to_media, 'rb') as file:
                    media_file = file.read()
            else:
                media_file = None
            if post_info['text']:
                caption = await fill_name(post_info['text'], message.chat.first_name)
                caption = caption.replace('<br />', '\n')
            else:
                caption = None
            logger.info(f'POST DATA - {path_to_media} / {message_function} / {caption}')
            if photos:
                media = types.MediaGroup()
                for i, path_to_media in enumerate(photos):
                    media.attach_photo(types.InputFile(path_to_media))
                await message.bot.send_media_group(message.chat.id, media=media)
                await message.bot.send_message(message.chat.id, text=caption, parse_mode='HTML', reply_markup=keyboard)
            elif message_function:
                await message_function(message.chat.id, media_file, caption=caption, parse_mode='HTML',
                                       reply_markup=keyboard)
        elif post_info['text']:
            text = await fill_name(post_info['text'], message.chat.first_name)
            text = text.replace('<br />', '\n')
            await message.answer(text, parse_mode='HTML', reply_markup=keyboard)
        elif post_info['audio']:
            with open(f'{base_media_path}{post_info["audio"]}', 'rb') as file:
                await message.answer_audio(file)
        if post_info['add_tags_id']:
            await add_tags(message.chat.id, post_info['add_tags_id'])
        if post_info['default_next_integer']:
            await to_next_post(message, post_info['default_next_integer'])
            return


    @dp.message_handler(filters.IDFilter(user_id=ADMIN_TELEGRAM_ID), commands=['admin'])
    async def get_admin_menu(message: types.Message):
        '''Функция вывода меню администратора'''
        await message.answer('Меню администратора', reply_markup=types.ReplyKeyboardRemove())
        await message.answer('Выберите пункт', reply_markup=get_admin_menu_keyboard())


    @dp.message_handler(commands='start')
    async def start(message: types.Message, state: FSMContext):
        '''Функция выдающая ответ на команду start'''
        logger.info(f'START MESSAGE - {message}')
        username = message.from_user['username']
        first_name = message.from_user['first_name']
        last_name = message.from_user['last_name']
        full_name = message.from_user.full_name
        info = await message.bot.get_me()
        bot_username = info.username
        logger.info(f'DP - {info.username}')
        logger.info(
            f'USERNAME - {username}, FIRST NAME - {first_name}, LAST NAME - {last_name}, FULL NAME - {full_name}')
        user_info = add_user(
            message.from_user['id'],
            message.from_user['username'],
            message.from_user['first_name'],
            message.from_user['last_name'],
            bot_username
        )
        post_info = get_post(user_info['telegram_id'], info.username)
        current_step = get_current_step(user_info['telegram_id'], info.username)
        await send_post(message, post_info)
        # await to_next_post(message, post_info['default_next_integer'])
        # await message.answer('Ответ')


    @dp.message_handler(content_types=['text'])
    async def process_text_message(message: types.Message):
        '''Функция обработки текстовых сообщений'''
        post_info = get_post(message.from_user.id, 1000)
        await send_post(message, post_info)


    @dp.callback_query_handler(cd_admin.filter())
    async def bot_callback_users_count(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
        users_count = len(fetchall('users', []))
        logger.info(f'USERS COUNT - {users_count}')
        action = callback_data['action']
        if action == 'UsersCount':
            await bot.send_message(callback.message.chat.id, f'Всего пользователей - {str(users_count)}',
                                   reply_markup=get_admin_menu_keyboard())
        elif action == 'Mailing':
            # await bot.send_message(callback.message.chat.id, f'Выберите пункт для заполнения',
            #                        reply_markup=get_create_mailing_keyboard())
            await bot.send_message(callback.message.chat.id, f'Введите название рассылки',
                                   reply_markup=types.ReplyKeyboardRemove())
            await CallbackCreateMailing.name_state.set()


    @dp.callback_query_handler(cd_create_mailing.filter())
    async def bot_callback_create_mailing(callback: types.CallbackQuery, callback_data: dict):
        field = callback_data['field']
        logger.info(f'FIELD - {field}')
        if field == 'name':
            await bot.send_message(callback.message.chat.id, 'Введите название рассылки')
            await CallbackCreateMailing.name_state.set()
        elif field == 'text':
            await bot.send_message(callback.message.chat.id, 'Введите текст рассылки')
            await CallbackCreateMailing.text_state.set()
        elif field == 'datetime':
            await bot.send_message(callback.message.chat.id,
                                   'Введите дату и время рассылки в формате "ДД.ММ.ГГГГ ЧЧ.ММ"')
            await CallbackCreateMailing.datetime_state.set()
        elif field == 'photo':
            await bot.send_message(callback.message.chat.id, 'Отправьте фото для рассылки')
            await CallbackCreateMailing.photo_state.set()
        elif field == 'video':
            await bot.send_message(callback.message.chat.id, 'Отправьте видео для рассылки')
            await CallbackCreateMailing.video_state.set()
        elif field == 'audio':
            await bot.send_message(callback.message.chat.id, 'Отправьте аудио для рассылки')
            await CallbackCreateMailing.audio_state.set()
        elif field == 'tag_id':
            await bot.send_message(callback.message.chat.id, 'Выберите тег для рассылки',
                                   reply_markup=get_tags_keyboard())
            await CallbackCreateMailing.tags_state.set()


    @dp.message_handler(state=CallbackCreateMailing.name_state)
    async def set_mailing_name(message: types.Message, state: FSMContext):
        answer = message.text
        logger.info(f'ANSWER - {answer}')
        await state.update_data(name=answer)
        await message.answer("Введите текст", reply_markup=types.ReplyKeyboardRemove())
        await CallbackCreateMailing.next()


    @dp.message_handler(state=CallbackCreateMailing.text_state)
    async def set_mailing_text(message: types.Message, state: FSMContext):
        answer = message.text
        logger.info(f'ANSWER - {answer}')
        await state.update_data(text=answer)
        await message.answer(f'Введите дату и время рассылки в формате "ДД.ММ.ГГГГ ЧЧ:ММ"',
                             reply_markup=types.ReplyKeyboardRemove())
        await CallbackCreateMailing.next()


    @dp.message_handler(state=CallbackCreateMailing.datetime_state)
    async def set_mailing_datetime(message: types.Message, state: FSMContext):
        answer = message.text
        logger.info(f'ANSWER - {answer}')
        try:
            datetime_for_mailing = datetime.strptime(answer, '%d.%m.%Y %H:%M')
            await state.update_data(datetime=answer)
            await message.answer(f"Отправьте фото для рассылки",
                                 reply_markup=skip_keyboard
                                 )
            await CallbackCreateMailing.next()
        except ValueError:
            logger.debug(f'EXCEPTION')
            await message.answer(f'Формат некорректный, введите дату и время рассылки в формате "ДД.ММ.ГГГГ ЧЧ:ММ"',
                                 reply_markup=types.ReplyKeyboardRemove())
            await CallbackCreateMailing.datetime_state.set()


    @dp.message_handler(content_types=['photo', 'text'], state=CallbackCreateMailing.photo_state)
    async def set_mailing_photo(message: types.Message, state: FSMContext):
        if message.photo or message.text == 'Пропустить':
            if message.text == 'Пропустить':
                await state.update_data(photo=None)
            elif message.photo:
                data = await state.get_data()
                logger.info(f'DATA - {data}')
                await message.photo[-2].download(destination_dir='media/mailings/')
                file_info = await message.photo[-2].get_file()
                path_to_photo = f'media/mailings/{file_info["file_path"]}'
                await state.update_data(photo=path_to_photo)
            await message.answer(f'Отправьте видео для рассылки', reply_markup=skip_keyboard)
            await CallbackCreateMailing.next()
        else:
            await message.answer(f'Формат некорректный, отправьте фото для рассылки', reply_markup=skip_keyboard)
            await CallbackCreateMailing.photo_state.set()


    @dp.message_handler(content_types=['video', 'text'], state=CallbackCreateMailing.video_state)
    async def set_mailing_video(message: types.Message, state: FSMContext):
        if message.text == 'Пропустить':
            await state.update_data(video=None)
            await message.answer('Выберите тег для рассылки', reply_markup=types.ReplyKeyboardMarkup())
            await message.answer(f'Список тегов', reply_markup=get_tags_keyboard())
            await CallbackCreateMailing.next()
        elif message.video:
            data = await state.get_data()
            video_id = message.video.file_id
            file = await bot.get_file(video_id)
            logger.info(f'FILE {file}')
            path_to_file = f'media/mailings/{file.file_path}'
            logger.info(f'FILE {path_to_file}')
            await bot.download_file(file.file_path, destination_dir='media/mailings/')
            await state.update_data(video=path_to_file)
            await message.answer('Выберите тег для рассылки', reply_markup=types.ReplyKeyboardMarkup())
            await message.answer(f'Список тегов', reply_markup=get_tags_keyboard())
            await CallbackCreateMailing.next()
        else:
            await message.answer(f'Формат некорректный, отправьте видео для рассылки', reply_markup=skip_keyboard)
            await CallbackCreateMailing.video_state.set()


    @dp.callback_query_handler(state=CallbackCreateMailing.tags_state)
    async def set_mailing_tags(callback: types.CallbackQuery, state: FSMContext):
        logger.info(f'CALLBACK - {callback.data}')
        tag_id = int(callback.data.replace('cd_create_mailing_tags:', ''))
        if tag_id == 0:
            await state.update_data(tags_id=None)
        else:
            await state.update_data(tags_id=tag_id)
        data = await state.get_data()
        logger.info(f'FINAL DATA = {data}')
        await bot.send_message(callback.message.chat.id,
                               'Введите текст кнопки и ссылку кнопки в формате "{button_text}/{button_url}"')
        await CallbackCreateMailing.next()


    @dp.message_handler(state=CallbackCreateMailing.button_state)
    async def set_mailing_button(message: types.Message, state: FSMContext):
        if message.text == 'Пропустить':
            await state.update_data(button=None)
            await CallbackCreateMailing.next()
        if '/' in message.text:
            button_text, button_url = message.text.split('/', maxsplit=1)
            await state.update_data(button_text=button_text, button_url=button_url)
            final_data = await state.get_data()
            logger.info(f'FINAL DATA - {final_data}')

            await message.answer('Предварительный просмотр', reply_markup=types.ReplyKeyboardRemove())
            await send_mailing_post(ADMIN_TELEGRAM_ID, final_data)
            await message.answer(f'Подтверждаете отправку?', reply_markup=get_confirm_keyboard())
            await CallbackCreateMailing.next()
        else:
            await message.answer(
                'Формат некорректный. Введите текст кнопки и ссылку кнопки в формате "{button_text}/{button_url}"',
                reply_markup=skip_keyboard)
            await CallbackCreateMailing.button_state.set()


    @dp.callback_query_handler(state=CallbackCreateMailing.confirm_state)
    async def set_mailing_confirm(callback: types.CallbackQuery, state: FSMContext):
        logger.info(f'CALLBACK - {callback.data}')
        result = callback.data.replace('cd_confirm:', '')
        if result == 'accept':
            logger.info(f'CONFIRM MAILING')
            data = await state.get_data()
            start_mailing_time = datetime.strptime(data['datetime'], '%d.%m.%Y %H:%M')
            interval = start_mailing_time.timestamp() - time.time()
            await bot.send_message(callback.message.chat.id,
                                   f'Рассылка запланирована и будет запущена через {interval} секунд')
            logger.info(f'START INTERVAL FOR MAILING - {interval}')
            if data["tags_id"]:
                user_ids = [i['id'] for i in fetchall('users_tags', ['id'], f'tag_id = {data["tags_id"]}')]
            else:
                user_ids = [i['id'] for i in fetchall('users', ['id'])]
            logger.info(f'USER IDS - {user_ids}')
            users_telegram_id_id = [[i['telegram_id'], i['id']] for i in fetchall('users', ['telegram_id', 'id'],
                                                                                  f'id in ({", ".join([str(p) for p in user_ids])})')]
            logger.info(f'USERS TELEGRAM ID - {users_telegram_id_id}')
            insert('mailings', data)
            mailing_pk = max([i['id'] for i in fetchall('mailings', ['id'])])
            logger.info(f'MAILING PK - {mailing_pk}')
            success, errors = await launch_mailing(mailing_pk, data, interval, users_telegram_id_id)
            # await state.update_data(tags_id=None)
            await bot.send_message(callback.message.chat.id, f'''Рассылка завершена. 
    Доставлено - {success}, 
    недоставлено - {errors}''')
        else:
            logger.info(f'DECLINE MAILING')
            # await state.update_data(tags_id=tag_id)
        await state.finish()


    @dp.callback_query_handler(cd_next_post.filter())
    async def bot_callback_next_post(callback: types.CallbackQuery, callback_data: dict):
        logger.info(f'CALLBACK IN HANDLER - {callback}')
        logger.info(f'CALLBACK DATA IN HANDLER - {callback_data}')
        next_post_id = callback_data.get('next_post')

        logger.info(f'NEXT POST ID {next_post_id}')
        post_info = get_post(callback['from']['id'], callback['message']['from']['username'], next_post_id, get_by_id=True)
        logger.info(f'POST INFO - {post_info}')
        await send_post(callback.message, post_info)


async def on_startup(bot):
    # users = [i['telegram_id'] for i in fetchall('users', ['telegram_id'])]
    users = [720023902, 5779698994]
    for user in users:
        try:
            await bot.send_message(user, 'Перезапустились. Отправь команду /start')
            await asyncio.sleep(rd.randint(10, 50) / 10)
        except Exception:
            continue


# Запускаем ботов
async def start_bots():
    tasks = []
    for dispatcher in dispatchers:
        task = dispatcher.start_polling()
        tasks.append(task)
        logger.info(f'TASK ADDED')
    for bot in bots:
        await on_startup(bot)
        logger.info(f'ON STARTUP LAUNCHED')
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bots())
    loop.run_forever()





