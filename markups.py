from utils import *
from pprint import pprint
from aiogram.utils.callback_data import CallbackData
from db import *
from aiogram import types

cd_next_post = CallbackData('cd_next_post', 'next_post')
cd_admin = CallbackData('admin', 'action')
cd_create_mailing = CallbackData('cd_create_mailing', 'field')
cd_create_mailing_tags = CallbackData('cd_create_mailing_tags', 'tag_id')
cd_confirm = CallbackData('cd_confirm', 'result')
cd_confirm_from_admin = CallbackData('cd_confirm_from_admin', 'result', 'mailing_pk')


def get_admin_menu_keyboard():
    types.ReplyKeyboardRemove()
    admin_menu = types.InlineKeyboardMarkup()
    users_count = types.InlineKeyboardButton(text='Количество пользователей', callback_data=cd_admin.new(
        action='UsersCount',
    ))
    mailings = types.InlineKeyboardButton(text='Запустить рассылку', callback_data=cd_admin.new(
        action='Mailing'
    ))
    admin_menu.add(users_count)
    admin_menu.add(mailings)
    return admin_menu


def get_create_mailing_keyboard():
    name_field = types.InlineKeyboardButton(text='Имя рассылки', callback_data=cd_create_mailing.new(field='name'))
    text_field = types.InlineKeyboardButton(text='Текст рассылки', callback_data=cd_create_mailing.new(field='text'))
    datetime_field = types.InlineKeyboardButton(text='Дата и время рассылки', callback_data=cd_create_mailing.new(field='datetime'))
    photo_field = types.InlineKeyboardButton(text='Фото', callback_data=cd_create_mailing.new(field='photo'))
    audio_field = types.InlineKeyboardButton(text='Аудио', callback_data=cd_create_mailing.new(field='audio'))
    video_field = types.InlineKeyboardButton(text='Видео', callback_data=cd_create_mailing.new(field='video'))
    tag_field = types.InlineKeyboardButton(text='Тег', callback_data=cd_create_mailing.new(field='tag_id'))
    keyboard = types.InlineKeyboardMarkup()
    for i in [name_field, text_field, datetime_field, photo_field, audio_field, video_field, tag_field]:
        keyboard.add(i)
    return keyboard


def get_tags_keyboard():
    tags = fetchall('bots_tags', ['id', 'name'])
    keyboard = types.InlineKeyboardMarkup()
    for tag in tags:
        keyboard.add(types.InlineKeyboardButton(text=tag['name'], callback_data=cd_create_mailing_tags.new(
            tag_id=tag['id']
        )))
    keyboard.add(types.InlineKeyboardButton(text='Все пользователи', callback_data=cd_create_mailing_tags.new(
            tag_id=0
        )))
    return keyboard


def get_confirm_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Да', callback_data=cd_confirm.new(
        result='accept'
    )))
    keyboard.add(types.InlineKeyboardButton(text='Heт', callback_data=cd_confirm.new(
        result='decline'
    )))
    return keyboard


def get_confirm_keyboard_from_admin(mailing_pk):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Да', callback_data=cd_confirm_from_admin.new(
        result='accept_admin',
        mailing_pk=mailing_pk,
        # data=data,
        # interval=interval,
        # users_telegram_id_id=users_telegram_id_id
    )))
    keyboard.add(types.InlineKeyboardButton(text='Heт', callback_data=cd_confirm_from_admin.new(
        result='decline',
        mailing_pk=mailing_pk,
        # data=data,
        # interval=interval,
        # users_telegram_id_id=users_telegram_id_id
    )))
    return keyboard


def get_keyboard(buttons):
    keys = []
    for button in buttons:
        logger.info(f'BUTTON {button}')
        if button['button_url']:
            key = types.InlineKeyboardButton(text=button['button_text'], url=button['button_url'])
        elif button['next_post_id']:
            key = types.InlineKeyboardButton(text=button['button_text'], callback_data=cd_next_post.new(
                next_post=button['next_post_id']
            ))
        else:
            key = None
        if key:
            keys.append(key)
        else:
            logger.debug(f'KEY WITH ERROR {button}')
    if len(buttons) > 2:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        for item in split_list(keys, 2):
            keyboard.row(*item)
    else:
        keyboard = types.InlineKeyboardMarkup()
        for item in keys:
            keyboard.add(item)
    return keyboard


skip_keyboard = types.ReplyKeyboardMarkup(keyboard=[
    [types.KeyboardButton(text='Пропустить')]
])
