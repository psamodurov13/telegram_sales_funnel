import datetime
import os
from typing import Dict, List, Tuple
import sqlite3
from loguru import logger
from datetime import date, datetime

conn = sqlite3.connect("telegram_sales_funnel.db")
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


def edit(table: str, filter_column: str, filter_value: str, new_column: str, new_value: str):
    cursor.execute(f"UPDATE {table} SET {new_column} = {new_value} WHERE {filter_column} = {filter_value}")
    user_info = fetchall('users', [], f'{filter_column} = {filter_value}')[0]
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
    user_info = fetchall('users', [], f'telegram_id = {telegram_id}')[0]
    return user_info


def add_user(
        user_telegram_id,
        username,
        first_name='',
        last_name='',
        full_name='',
        created_at=datetime.now(),
        current_step=1
):
    check_id = fetchall('users', ['id', 'telegram_id'], f'telegram_id = {user_telegram_id}')
    logger.info(f'CHECK_ID - {check_id}')
    if not check_id:
        user_dict = {
            'telegram_id': user_telegram_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'current_step': current_step,
            'created_at': created_at,
        }
        insert('users', user_dict)
        logger.info(f'USER {user_telegram_id} WAS ADDED TO DB')
    else:
        logger.info('USER ALREADY IN DB')
    user_info = get_user(user_telegram_id)
    logger.info(f'NEW USER INFO - {user_info}')
    return user_info


def get_post(user_telegram_id, current_step=None):
    user_info = get_user(user_telegram_id)
    if not current_step:
        current_step = user_info['current_step']
    post_info = fetchall('posts', [], f'count = {current_step}')[0]
    logger.info(f'GET POST - COUNT {current_step} - {type(post_info)} - {post_info}')
    buttons_id = [str(button['button_id']) for button in fetchall('posts_buttons', ['button_id'], f'post_id = {post_info["id"]}')]
    logger.info(f'BUTTONS ID - {buttons_id}')
    buttons = fetchall('buttons', [], f'id in ({", ".join(buttons_id)})')
    logger.info(f'BUTTONS - {buttons}')
    post_info['buttons'] = buttons
    add_tags_id = fetchall('posts_add_tags', [], f'post_id = {post_info["id"]}')
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


check_db_exists()

if __name__ == '__main__':
    get_post(get_user(720023902))