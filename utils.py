from aiogram.utils.callback_data import CallbackData

from db import *
from aiogram import types

cd_next_post = CallbackData('cd_next_post', 'next_post')


def split_list(list_for_split, number):
    return [list_for_split[i:i + number] for i in range(0, len(list_for_split), number)]
