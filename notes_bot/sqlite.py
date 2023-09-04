import os
import psycopg2
import asyncio
from dotenv import load_dotenv


load_dotenv()
# Подключаемся к нашей базе данных.
connection = psycopg2.connect(
        host=os.getenv('host'),
        user=os.getenv('user'),
        password=os.getenv('password'),
        database=os.getenv('db_name')
    )
# Нужно для отработки запроса и записи изменений в базу данных.
connection.autocommit = True


'''
async def information_user(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT anime_list FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        user = list(cursor.fetchone())
    return user
'''


# Асинхронная функция для запуска базы данных.
async def db_start():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS animation.anime(user_id serial PRIMARY KEY, name varchar(255), "
            "anime_list varchar(255))"
        )


# Создаём функцию, которая будет запускаться при команде старт и создавать запись.
async def create_profile(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT anime_list FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        user = cursor.fetchone()
    # Если пользователь уже создан возвращаем его, иначе добавляем в базу данных.
    # Метод fetchone берёт значение из базы данных и возвращает его.
    if not user:
        # Создаём пустой профиль, а при команде create начнём его заполнять.
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO animation.anime (user_id, name, anime_list)
                VALUES ({user_id}, '', '')
            """)


# Заполняем профиль, для этого передаём состояние бота и идентификатор пользователя.
async def edit_profile(state, user_id):

    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT anime_list FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        user = list(cursor.fetchone())
    # Создаём контекстный менеджер для работы с базой данных.
    async with state.proxy() as data:
        if user[0].startswith(', '):
            user = user[0][2:]
        user.append(data['anime_list'])
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE animation.anime SET (name, anime_list) = ('{data['name']}', '{', '.join(user)}')"
                f"WHERE user_id = '{user_id}'"
            )
