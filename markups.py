from aiogram import types
from aiogram.utils.callback_data import CallbackData
from utils import *
from pprint import pprint

cd_admin = CallbackData('admin', 'action')


def get_admin_menu():
    admin_menu = types.InlineKeyboardMarkup()
    users_count = types.InlineKeyboardButton(text='Количество пользователей', callback_data=cd_admin.new(
        action='UsersCount',
    ))
    admin_menu.add(users_count)
    return admin_menu