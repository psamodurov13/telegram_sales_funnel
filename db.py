import datetime
import os
from typing import Dict, List, Tuple
import sqlite3
from loguru import logger
from datetime import date, datetime
from config import prod

# conn = sqlite3.connect("telegram_sales_funnel.db")
if prod:
    path_to_db = '/home/manage_telegrambot/manage_telegrambot/manage_telegrambot/db.sqlite3'
else:
    path_to_db = '/Users/psamodurov13/PycharmProjects/manage_telegrambot/manage_telegrambot/db.sqlite3'
conn = sqlite3.connect(path_to_db, check_same_thread=False)
cursor = conn.cursor()


def insert(table: str, column_values: Dict):
    columns = ', '.join(column_values.keys())
    values = [tuple(column_values.values())]
    placeholders = ", ".join( "?" * len(column_values.keys()) )
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def fetchall(table: str, columns: List[str], where: str = None) -> List:
    logger.info(f'FETCHALL - table: {table}, columns: {columns}, where: {where}')
    if columns:
        columns_joined = ", ".join(columns)
    else:
        columns_joined = '*'
        columns = get_columns(table)
    query = f"SELECT {columns_joined} FROM {table}"
    if where:
        query += f' WHERE {where}'
    logger.info(f'QUERY - {query}')
    cursor.execute(query)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        dict_row = {}
        for index, column in enumerate(columns):
            dict_row[column] = row[index]
        result.append(dict_row)
    return result


def delete(table: str, row_id: int) -> None:
    row_id = int(row_id)
    cursor.execute(f"delete from {table} where id={row_id}")
    conn.commit()


def edit(table: str, filter_column: str, filter_value: str, new_column: str, new_value):
    logger.info(f'QUERY UPDATE {table} SET {new_column} = {new_value} WHERE {filter_column} = {filter_value}')
    if filter_column in ['telegram_id', 'is_completed']:
        cursor.execute(f"UPDATE {table} SET {new_column} = {new_value} WHERE {filter_column} = {filter_value}")
    else:
        cursor.execute(f"UPDATE {table} SET {new_column} = '{new_value}' WHERE {filter_column} = {filter_value}")
    user_info = fetchall('bots_currentsteps', [], f'{filter_column} = {filter_value}')[0]
    logger.info(f'NEW USER INFO - {user_info}')
    conn.commit()
    return user_info


def get_all_users():
    return fetchall('users', ['id', 'telegram_id', 'created_at'])


def get_columns(table_name):
    columns = cursor.execute(f'select name from pragma_table_info("{table_name}")')
    result = [i[0] for i in columns.fetchall()]
    return result


def get_user(telegram_id):
    user_info = fetchall('bots_subscribers', [], f'telegram_id = {telegram_id}')[0]
    return user_info


def get_bot_id(bot_username):
    bot_id = fetchall('bots_bot', [], f'username = "{bot_username}"')[0]['id']
    return bot_id


def get_subscriber_id(telegram_id):
    subscriber_id = fetchall('bots_subscribers', ['id'], f'telegram_id = {telegram_id}')[0]['id']
    return subscriber_id


def add_user(
        user_telegram_id,
        username,
        first_name='',
        last_name='',
        bot_username=None,
        created_at=datetime.now(),
        current_step='start',
):
    check_id = fetchall('bots_subscribers', ['id', 'telegram_id'], f'telegram_id = {user_telegram_id}')
    logger.info(f'CHECK_ID - {check_id}')
    bot_id = get_bot_id(bot_username)
    logger.info(f'BOT ID - {bot_id}')
    if not check_id:
        user_dict = {
            'telegram_id': user_telegram_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            # 'current_step': current_step,
            'created_at': created_at,
        }
        insert('bots_subscribers', user_dict)
        subscriber_id = get_subscriber_id(user_telegram_id)
        current_step_post = fetchall('bots_post', [], f"count = 'start' and bot_id = {bot_id}")[0]
        insert('bots_currentsteps', {
            'bot_id': bot_id,
            'subscriber_id': subscriber_id,
            'current_step': current_step_post['count'],
            'is_completed': 0
        })
        logger.info(f'USER {user_telegram_id} WAS ADDED TO DB')

        # insert('bots_currentsteps', {'current_step': current_step, 'bot_': bot_id})
        logger.info(f'CURRENT STEP WAS SETUP')
    else:
        subscriber_id = get_subscriber_id(user_telegram_id)
        logger.info('USER ALREADY IN DB')
        check_current_step_for_bot = fetchall('bots_currentsteps', [], f'bot_id = {bot_id} and subscriber_id = {subscriber_id}')
        if not check_current_step_for_bot:
            start_step = fetchall('bots_post', [], f"count = 'start' and bot_id = {bot_id}")[0]
            insert('bots_currentsteps', {
                'bot_id': bot_id,
                'subscriber_id': subscriber_id,
                'current_step': start_step['count'],
                'is_completed': 0
            })
            logger.info(f'USER {user_telegram_id} WAS ADDED TO DB EARLY, BUT NOW NEW CURRENT STEP ROW WAS CREATED IN DB')
    user_info = get_user(user_telegram_id)
    logger.info(f'NEW USER INFO - {user_info}')
    return user_info


def get_current_step(telegram_id, bot_username, parameter_to_return='id'):
    bot_id = get_bot_id(bot_username)
    logger.info(f'BOT ID {bot_id}')
    subscriber_id = get_subscriber_id(telegram_id)
    current_steps = fetchall('bots_currentsteps', [],
                             f'subscriber_id = {subscriber_id} and bot_id = {bot_id}')
    if current_steps:
        current_step = current_steps[0][parameter_to_return]
    else:
        start_step = fetchall('bots_currentsteps', [],
                             f"subscriber_id = {subscriber_id} and bot_id = {bot_id} and current_step = 'start' ")[0]
        current_step = start_step[parameter_to_return]
    return current_step


def get_post(user_telegram_id, bot_username, current_step=None, get_by_id=False):
    logger.info(f'GET POST STARTED - {user_telegram_id} / {bot_username} / {current_step}')
    user_info = get_user(user_telegram_id)
    bot_id = get_bot_id(bot_username)
    logger.info(f'BOT_ID - {bot_id}')
    subscriber_id = get_subscriber_id(user_telegram_id)
    logger.info(f'SUBSCRIBER_ID - {subscriber_id}')
    if not current_step:
        current_steps = fetchall('bots_currentsteps', [],
                                f'subscriber_id = {subscriber_id} and bot_id = {bot_id}')
        logger.info(f'CURRENT_STEP - {current_steps}')
        if current_steps:
            count = current_steps[0]['current_step']
            # post = fetchall('bots_post', [], f"count = '{count}' and bot_id = {bot_id}")[0]
            current_step = count
        else:
            # start_step = fetchall('bots_post', [], f"count = 'start' and bot_id = {bot_id}")[0]
            # current_step = start_step['id']
            current_step = 'start'
        logger.info(f'CURRENT STEP ID - {current_step}')
    # else:
    #     current_step = fetchall('bots_post', [], f"count = 'start' and bot_id = {bot_id}")[0]['id']
    if get_by_id:
        post_info = fetchall('bots_post', [], f"id = {current_step} and bot_id = {bot_id}")[0]
    else:
        post_info = fetchall('bots_post', [], f"count = '{current_step}' and bot_id = {bot_id}")[0]
    logger.info(f'GET POST - COUNT {current_step} - {type(post_info)} - {post_info}')
    buttons_objects = fetchall('bots_post_buttons', ['buttons_id'], f'post_id = {post_info["id"]}')
    logger.info(f'BUTTONS OBJECTS - {buttons_objects}')
    buttons_id = [str(button['buttons_id']) for button in buttons_objects]
    logger.info(f'BUTTONS ID - {buttons_id}')
    buttons = fetchall('bots_buttons', [], f'id in ({", ".join(buttons_id)})')
    logger.info(f'BUTTONS - {buttons}')
    post_info['buttons'] = buttons
    add_tags_id = fetchall('bots_post_add_tags', [], f'post_id = {post_info["id"]}')
    logger.info(f'ADD TAGS ID - {add_tags_id}')
    post_info['add_tags_id'] = add_tags_id
    return post_info


def get_cursor():
    return cursor


def _init_db():
    """Инициализирует БД"""
    # with open("createdb.sql", "r") as f:
    #     sql = f.read()
    from createdb import query as sql
    from createdb import get_query_for_posts
    logger.info(sql)
    cursor.executescript(sql)
    get_query_for_posts()
    logger.info(f'DATABASE WAS CREATED')
    conn.commit()


def check_db_exists():
    """Проверяет, инициализирована ли БД, если нет — инициализирует"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()
    logger.info(f'DATABASE WAS CREATED')


# check_db_exists()

if __name__ == '__main__':
    get_post(get_user(720023902))