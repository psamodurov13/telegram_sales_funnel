from utils import *
from pprint import pprint
from aiogram.utils.callback_data import CallbackData
from db import *
from aiogram import types

cd_next_post = CallbackData('cd_next_post', 'next_post')

cd_admin = CallbackData('admin', 'action')


def get_admin_menu():
    admin_menu = types.InlineKeyboardMarkup()
    users_count = types.InlineKeyboardButton(text='Количество пользователей', callback_data=cd_admin.new(
        action='UsersCount',
    ))
    admin_menu.add(users_count)
    return admin_menu


def get_keyboard(buttons):
    keys = []
    for button in buttons:
        if button['button_url']:
            key = types.InlineKeyboardButton(text=button['button_text'], url=button['button_url'])
        elif button['next_post']:
            key = types.InlineKeyboardButton(text=button['button_text'], callback_data=cd_next_post.new(
                next_post=button['next_post']
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
