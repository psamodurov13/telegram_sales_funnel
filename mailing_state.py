from aiogram.dispatcher.filters.state import StatesGroup, State


class CallbackCreateMailing(StatesGroup):
    name_state = State()
    text_state = State()
    datetime_state = State()
    photo_state = State()
    video_state = State()
    tags_state = State()
    button_state = State()
    confirm_state = State()
