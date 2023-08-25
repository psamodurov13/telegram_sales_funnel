import time
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from loguru import logger
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import filters
from config import *
from markups import *
from db import *
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logger.add('debug.log', format='{time} {level} {message}', level='INFO', rotation='15MB', compression='zip')
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands='start')
async def start(message: types.Message, state: FSMContext):
    '''Функция выдающая ответ на команду start'''
    if message.from_user['username']:
        username = message.from_user['username']
    elif message.from_user['first_name']:
        username = message.from_user['first_name']
    else:
        username = message.from_user['id']
    add_user(message.from_user['id'], username)
    await message.answer('привет. Как дела')


@dp.message_handler(filters.IDFilter(user_id=ADMIN_TELEGRAM_ID), commands=['admin'])
async def get_users_count(message: types.Message):
    await message.answer('Меню администратора', reply_markup=get_admin_menu())


# @dp.message_handler(lambda message: message.text.startswith('/del'))
# async def del_expense(message: types.Message):
#     """Удаляет сотрудника по идентификатору"""
#     row_id = int(message.text[4:])
#     answer_message = delete_employee(row_id)
#     await message.answer(answer_message)
#
#
# @dp.message_handler(content_types=['text'])
# @auth
# async def process_text_message(message: types.Message, state: FSMContext):
#     logger.info(f'MESSAGE - {message}')
#     '''Функция обработки текстовых сообщений'''
#     amount = check_amount_message(message.text)
#     if amount:
#         async with state.proxy() as data:
#             data['amount'] = amount
#             input_currency = data['input_currency']
#             output_currency = data['output_currency']
#             pay_type = data.get('pay_type', list(currencies[input_currency]["pay_type"].keys())[0] if input_currency in currencies else None)
#             currency_for_amount = data['currency_for_amount']
#         currency_code = get_currency_code(currency_for_amount)
#         logger.info(f'PAY TYPE {pay_type}')
#         input_pay_type_name = get_pay_type_name(input_currency, pay_type)
#         logger.info(f'INPUT PAY TYPE {input_pay_type_name}')
#         output_pay_type_name = get_pay_type_name(output_currency, pay_type)
#         logger.info(f'OUTPUT PAY TYPE {output_pay_type_name}')
#         if currency_code:
#             input_currency_quantity, output_currency_quantity = get_exchange_rate(
#                 input_currency, input_pay_type_name,
#                 output_currency, output_pay_type_name,
#                 currency_for_amount, amount, pay_type
#             )
#             if input_currency_quantity is not None and output_currency_quantity is not None:
#                 real_exchange_rate = input_currency_quantity / output_currency_quantity
#                 async with state.proxy() as data:
#                     data['real_exchange_rate'] = real_exchange_rate
#                     data['current_percent'] = default_percent
#                     data['input_pay_type_name'] = input_pay_type_name
#                     data['output_pay_type_name'] = output_pay_type_name
#                     if currency_for_amount == input_currency:
#                         data['input_currency_quantity'] = input_currency_quantity
#                         data['output_currency_quantity'] = None
#                     else:
#                         data['input_currency_quantity'] = None
#                         data['output_currency_quantity'] = output_currency_quantity
#                 input_currency_quantity, output_currency_quantity, exchange_rate_for_message = get_change_offer(
#                     input_currency, input_currency_quantity, output_currency, output_currency_quantity,
#                     real_exchange_rate, default_percent, currency_for_amount
#                 )
#                 await message.answer(f'Обмен {input_currency}' + (f' ({input_pay_type_name})' if input_pay_type_name else '') +
#                                      f' - {output_currency}' + (f' ({output_pay_type_name})' if output_pay_type_name else '') + '\n' +
#                                      f'Курс: {exchange_rate_for_message}\n\n'
#                                      f'Отдаете: {input_currency_quantity} {get_currency_code(input_currency)}' +
#                                      (f' ({input_pay_type_name})' if input_pay_type_name else '') + '\n' +
#                                      f'Получаете: {output_currency_quantity} {get_currency_code(output_currency)}' +
#                                      (f' ({output_pay_type_name})' if output_pay_type_name else ''),
#                                      reply_markup=transfer_types_keyboard())
#                 await message.answer('------', reply_markup=percents_buttons())
#             else:
#                 await message.answer(f'Ошибка. Нет подходящих предложений для этой суммы /start', reply_markup=transfer_types_keyboard())
#
#         else:
#             await message.answer('Ошибка', reply_markup=transfer_types_keyboard())
#         # await state.finish()
#     else:
#         # change_pair = get_currencies_from_message(message.text)
#         change_pair, pay_type, currency_for_amount = parse_currencies_from_message(message.text)
#         if change_pair:
#             # записываем данные в хранилище
#             async with state.proxy() as data:
#                 data['input_currency'] = change_pair[0]
#                 data['output_currency'] = change_pair[1]
#                 data['pay_type'] = pay_type
#                 data['currency_for_amount'] = currency_for_amount
#             if change_pair[0] in currencies and len(currencies[change_pair[0]]['pay_type']) > 1 and pay_type is None:
#                 await message.answer(f"Выберите способ ввода",
#                                      reply_markup=choice_pay_type_keyboard(currencies[change_pair[0]]['pay_type']))
#             elif change_pair[1] in currencies and len(currencies[change_pair[1]]['pay_type']) > 1 and pay_type is None:
#                 await message.answer(f"Выберите способ вывода",
#                                      reply_markup=choice_pay_type_keyboard(currencies[change_pair[1]]['pay_type']))
#             # else:
#             #     await message.answer(f"Выберите валюту для ввода суммы",
#             #                          reply_markup=choice_currency_for_amount(change_pair))
#             elif currency_for_amount:
#                 await message.answer(f'Введите сумму в {currency_for_amount}', reply_markup=amount_keyboard())
#             else:
#                 await message.answer(f'Ошибка', reply_markup=transfer_types_keyboard())
#         else:
#             await message.answer(f"Ошибка, либо недостаточно прав", reply_markup=transfer_types_keyboard())
#
#
# @dp.callback_query_handler(markups.cd_confirm_user.filter())
# async def bot_callback_confirm_user(callback: types.CallbackQuery, callback_data: dict):
#     logger.info(f'CALLBACK DATA IN HANDLER - {callback}')
#     action = callback_data.get('action')
#     telegram_id = callback_data.get('telegram_id')
#     username = callback_data.get('username')
#     logger.info(f'RESPONSE - {action}, {telegram_id}')
#     if action == 'Accept':
#         db.add_user(telegram_id, username, True)
#         await callback.message.answer('Доступ разрешен')
#         await bot.send_message(telegram_id, 'Доступ разрешен')
#     elif action == 'Decline':
#         db.add_user(telegram_id, username, False)
#         await callback.message.answer('Доступ заблокирован')
#         await bot.send_message(telegram_id, 'Доступ заблокирован')
#     else:
#         await callback.message.answer('Ошибка')
#
#
# @dp.callback_query_handler(markups.cd_choice_pay_type.filter())
# async def bot_callback_choice_pay_type(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
#     logger.info(f'CALLBACK DATA IN HANDLER - {callback}')
#     pay_type = callback_data.get('pay_type')
#     logger.info(f'RESPONSE - {pay_type}')
#     async with state.proxy() as data:
#         logger.info(f'CURRENT STORAGE DATA {data}')
#         data['pay_type'] = pay_type
#         input_currency = data['input_currency']
#         output_currency = data['output_currency']
#     await callback.message.answer('Выберите валюту для ввода суммы',
#                                   reply_markup=choice_currency_for_amount([input_currency, output_currency]))
#
#
# @dp.callback_query_handler(markups.cd_choice_currency_for_amount.filter())
# async def bot_callback_choice_currency_for_amount(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
#     logger.info(f'CALLBACK DATA IN HANDLER - {callback}')
#     currency = callback_data.get('currency')
#     logger.info(f'RESPONSE - {currency}')
#     async with state.proxy() as data:
#         data['currency_for_amount'] = currency
#     currency_code = get_currency_code(currency)
#     if currency_code:
#         await callback.message.answer(f'Валюта для суммы получена. Введите сумму в {currency_code}',
#                                       reply_markup=amount_keyboard())
#     else:
#         await callback.message.answer(f'Ошибка', reply_markup=transfer_types_keyboard())
#
#
# @dp.callback_query_handler(markups.cd_percents.filter())
# async def bot_callback_percents(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
#     logger.info(f'CALLBACK DATA IN HANDLER - {callback}')
#     percent = float(callback_data.get('percent'))
#     logger.info(f'RESPONSE - {percent}')
#     async with state.proxy() as data:
#         real_exchange_rate = data['real_exchange_rate']
#         data['current_percent'] = default_percent
#         input_currency = data['input_currency']
#         output_currency = data['output_currency']
#         currency_for_amount = data['currency_for_amount']
#         input_pay_type_name = data['input_pay_type_name']
#         output_pay_type_name = data['output_pay_type_name']
#         if currency_for_amount == input_currency:
#             input_currency_quantity = data['input_currency_quantity']
#             output_currency_quantity = None
#         else:
#             input_currency_quantity = None
#             output_currency_quantity = data['output_currency_quantity']
#     input_currency_quantity, output_currency_quantity, exchange_rate_for_message = get_change_offer(
#         input_currency, input_currency_quantity, output_currency, output_currency_quantity,
#         real_exchange_rate, percent, currency_for_amount
#     )
#     await callback.message.answer(f'Обмен {input_currency}' + (f' ({input_pay_type_name})' if input_pay_type_name else '') +
#                          f' - {output_currency}' + (f' ({output_pay_type_name})' if output_pay_type_name else '')
#                          + '\n'
#                            f'Курс: {exchange_rate_for_message}\n\n'
#                            f'Отдаете: {input_currency_quantity} {get_currency_code(input_currency)}' + (
#                              f' ({input_pay_type_name})' if input_pay_type_name else '') + '\n' +
#                          f'Получаете: {output_currency_quantity} {get_currency_code(output_currency)}' + (
#                              f' ({output_pay_type_name})' if output_pay_type_name else ''),
#                          reply_markup=transfer_types_keyboard())
#     await callback.message.answer(f'------', reply_markup=percents_buttons())

@logger.catch()
def main():
    executor.start_polling(dp)


if __name__ == '__main__':
    main()




