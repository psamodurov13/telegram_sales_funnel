import asyncio

from flask import Flask, jsonify, current_app
from flask import request
from flask import abort
from main import *
from config import prod
app = Flask(__name__)
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor()
if prod:
    base_media_path = '/home/manage_telegrambot/manage_telegrambot/manage_telegrambot'
else:
    base_media_path = '/Users/psamodurov13/PycharmProjects/manage_telegrambot/manage_telegrambot'

future = ''


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/restart/<token>')
def restart_bots(token):
    global future

    if token == API_TOKEN:
        try:
            from main import bot_objects
            logger.info(f'BOT OBJECTS - {bot_objects}')
            if future:
                future.cancel()
                logger.info(f'future.cancel() вызван')
                time.sleep(10)
                logger.info(f'таймер завершился')
            future = executor.submit(main)
            time.sleep(1)
            from main import bot_objects
            logger.info(f'BOT OBJECTS 2 - {bot_objects}')
            return {'result': True, 'message': 'BOT WAS RESTARTED'}
        except Exception:
            logger.exception(Exception)
            return {'result': False, 'message': Exception}
    else:
        return {'result': False, 'message': 'ACCESS DENIED'}


async def send_mailing_post(telegram_id, mailing_info, tg_bot, test_mode=False):
    '''Функция отправки рассылки'''
    if 'button_text' in mailing_info.keys() and 'button_url' in mailing_info.keys():
        if mailing_info['button_text'] and mailing_info['button_url']:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(mailing_info['button_text'], url=mailing_info['button_url']))
        else:
            keyboard = None
    else:
        keyboard = None
    if mailing_info['photo'] or mailing_info['video']:
        if mailing_info['photo']:
            path_to_media = mailing_info['photo']
            message_function = tg_bot.send_photo
        elif mailing_info['video']:
            path_to_media = mailing_info['video']
            message_function = tg_bot.send_video
        else:
            path_to_media = None
            message_function = None
        if path_to_media:
            with open(f'{base_media_path}{path_to_media}', 'rb') as file:
                media_file = file.read()
        else:
            media_file = None
        if mailing_info['text']:
            caption = mailing_info['text']
        else:
            caption = None
        logger.info(f'POST DATA - {path_to_media} / {message_function} / {caption}')
        if message_function:
            await message_function(telegram_id, media_file, caption=caption, parse_mode='HTML',
                                   reply_markup=keyboard)
    elif mailing_info['text']:
        text = mailing_info['text']
        await tg_bot.send_message(telegram_id, text, parse_mode='HTML', reply_markup=keyboard)


async def confirm_mailing(mailing_pk, data, interval, users_telegram_id_id, bot_username):
    bot = None
    from main import bot_objects
    for bot_object in bot_objects:
        logger.info(f'BOT {bot_object}')
        bot_info = await bot_object.get_me()
        if bot_info.username == bot_username:
            bot = bot_object
            logger.info(f'BOT WAS DEFINED')
    await send_mailing_post(ADMIN_TELEGRAM_ID, data, bot)
    await bot.send_message(ADMIN_TELEGRAM_ID, f'Подтверждаете отправку?', reply_markup=get_confirm_keyboard_from_admin(mailing_pk))


async def launch_mailing(mailing_pk, data, interval, users_telegram_id_id, bot_username):
    logger.info(f'INTERVAL SCHEDULE STARTED')
    await asyncio.sleep(interval)
    success_mails = 0
    errors_mails = 0
    bot = None
    from main import bot_objects
    for bot_object in bot_objects:
        logger.info(f'BOT {bot_object}')
        bot_info = await bot_object.get_me()
        if bot_info.username == bot_username:
            bot = bot_object
            logger.info(f'BOT WAS DEFINED')
    for user_ids in users_telegram_id_id:
        try:
            await send_mailing_post(user_ids[0], data, bot)
            column_values = {
                'mailing_id': mailing_pk,
                'subscriber_id': user_ids[1],
                'result': 1,
            }
            time.sleep(rd.randint(10, 50) / 10)
            insert('bots_mailingdelivery', column_values)
            success_mails += 1
        except Exception:
            logger.exception(Exception)
            column_values = {
                'mailing_id': mailing_pk,
                'subscriber_id': user_ids[1],
                'result': 0,
                'error': Exception.__name__
            }
            insert('bots_mailingdelivery', column_values)
            errors_mails += 1

    await bot.send_message(ADMIN_TELEGRAM_ID, f'''Рассылка завершена. 
Доставлено - {success_mails}, 
недоставлено - {errors_mails}''')
    # return success_mails, errors_mails


@app.route('/start-mailing', methods=['POST'])
def start_mailing():
    from main import client_loop
    logger.info(f'CLIENT LOOP {client_loop}')
    mailing_pk = request.json['mailing_pk']
    mailing_info = request.json['mailing_info']
    interval = request.json['interval']
    users_telegram_id_id = request.json['users_telegram_id_id']
    bot_username = request.json['bot_username']
    try:
        logger.info(f'REQUEST - {request.json}')
        if not request.json:
            abort(400)
        send_fut = asyncio.run_coroutine_threadsafe(confirm_mailing(
            mailing_pk, mailing_info, interval, users_telegram_id_id, bot_username
        ), client_loop)
        logger.info(f'REQUEST WAS SENT')
        send_fut.result()
        return {'result': True}
    except Exception:
        logger.exception(Exception)
        return {'result': False}


async def fill_name(text, name, for_change='{first_name}'):
    '''Функция заполнения имени в посте'''
    if for_change in text:
        text = text.replace(for_change, name)
    return text


async def send_post(post_info, bot_username, chat=ADMIN_TELEGRAM_ID):
    '''Функция отправки поста'''
    bot = None
    from main import bot_objects
    for bot_object in bot_objects:
        logger.info(f'BOT {bot_object}')
        bot_info = await bot_object.get_me()
        if bot_info.username == bot_username:
            bot = bot_object
            logger.info(f'BOT WAS DEFINED')
    logger.info(f'POST_INFO - {post_info}')
    if post_info['buttons']:
        keyboard = get_keyboard(post_info['buttons'])
    else:
        keyboard = None
    if post_info['emoji']:
        await bot.send_message(chat, post_info['emoji'])
    if post_info['photo'] or post_info['video']:
        photos = []
        if post_info['photo']:
            if post_info['photo2'] or post_info['photo3'] or post_info['photo4'] or post_info['photo5']:
                for i in ['photo', 'photo2', 'photo3', 'photo4', 'photo5']:
                    if post_info[i]:
                        photos.append(f'{base_media_path}{post_info[i]}')
                # photos.extend([f'media/photo/{i}' for i in post_info['photo'].split(',')])
            path_to_media = f'{base_media_path}{post_info["photo"]}'
            message_function = bot.send_photo
        elif post_info['video']:
            path_to_media = f'{base_media_path}{post_info["video"]}'
            message_function = bot.send_video
        else:
            path_to_media = None
            message_function = None
        if path_to_media and not photos:
            with open(path_to_media, 'rb') as file:
                media_file = file.read()
        else:
            media_file = None
        if post_info['text']:
            caption = await fill_name(post_info['text'], ADMIN_TELEGRAM_FIRSTNAME)
            caption = caption.replace('<br />', '\n')
        else:
            caption = None
        logger.info(f'POST DATA - {path_to_media} / {message_function} / {caption}')
        if photos:
            media = types.MediaGroup()
            for i, path_to_media in enumerate(photos):
                media.attach_photo(types.InputFile(path_to_media))
            await bot.send_media_group(chat, media=media)
            await bot.send_message(chat, text=caption, parse_mode='HTML', reply_markup=keyboard)
        elif message_function:
            await message_function(chat, media_file, caption=caption, parse_mode='HTML',
                                   reply_markup=keyboard)
    elif post_info['text']:
        text = await fill_name(post_info['text'], ADMIN_TELEGRAM_FIRSTNAME)
        text = text.replace('<br />', '\n')
        await bot.send_message(chat, text, parse_mode='HTML', reply_markup=keyboard)
    elif post_info['audio']:
        with open(f'{base_media_path}{post_info["audio"]}', 'rb') as file:
            await bot.send_audio(chat, file)


@app.route('/send-test-message', methods=['POST'])
def send_test_message():
    from main import client_loop
    logger.info(f'CLIENT LOOP {client_loop}')
    post_pk = request.json['post_pk']
    post_info = request.json['post_info']
    bot_username = request.json['bot_username']
    try:
        logger.info(f'REQUEST - {request.json}')
        if not request.json:
            abort(400)
        send_fut = asyncio.run_coroutine_threadsafe(send_post(
            post_info, bot_username
        ), client_loop)
        logger.info(f'REQUEST WAS SENT')
        send_fut.result()
        return {'result': True}
    except Exception:
        logger.exception(Exception)
        return {'result': False}







# with app.app_context():
#     global future
#     # restart_bots(API_TOKEN)
#     future = executor.submit(main)


if __name__ == '__main__':
    app.run(debug=True)
    # asyncio.run(app.run())