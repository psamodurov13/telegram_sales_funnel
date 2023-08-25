import os
from typing import Dict, List, Tuple
import sqlite3
from loguru import logger
from datetime import date

conn = sqlite3.connect("telegram_sales_funnel.db")
cursor = conn.cursor()


def insert(table: str, column_values: Dict):
    columns = ', '.join( column_values.keys() )
    values = [tuple(column_values.values())]
    placeholders = ", ".join( "?" * len(column_values.keys()) )
    cursor.executemany(
        f"INSERT INTO {table} "
        f"({columns}) "
        f"VALUES ({placeholders})",
        values)
    conn.commit()


def fetchall(table: str, columns: List[str], where: str = None) -> List[Tuple]:
    columns_joined = ", ".join(columns)
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


def edit(table: str, filter_column: str, filter_value: str, new_column: str, new_value: str):
    cursor.execute(f"UPDATE {table} SET {new_column} = {new_value} WHERE {filter_column} = {filter_value}")
    conn.commit()


def get_all_users():
    return fetchall('users', ['id', 'telegram_id', 'created_at'])


def add_user(user_telegram_id, username, first_name='', last_name='', current_step=1):
    check_id = fetchall('users', ['telegram_id'], f'telegram_id = {user_telegram_id}')
    logger.info(f'CHECK_ID - {check_id}')
    if not check_id:
        user_dict = {
            'telegram_id': user_telegram_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'current_step': current_step,
            'created': date.today(),
        }
        insert('users', user_dict)
        logger.info(f'USER {user_telegram_id} WAS ADDED TO DB')
    else:
        logger.info('USER ALREADY IN DB')


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