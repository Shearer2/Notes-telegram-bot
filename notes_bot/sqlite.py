import os
import psycopg2
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


def information_id():
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT user_id FROM animation.anime"""
        )
        inf_user = list(map(lambda x: x[0], cursor.fetchall()))
    return inf_user


def information_name(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT name FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        name = cursor.fetchone()
    return name[0]


def information_anime(user_id):
    result = 'Ваш список аниме:\n'
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT anime_list FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        anime = cursor.fetchone()[0].split(', ')
    for i in anime:
        result += f'{i}\n'
    return result


# Асинхронная функция для запуска базы данных.
async def db_start():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS animation.anime(user_id bigserial PRIMARY KEY, name varchar(255), "
            "anime_list text)"
        )


# Создаём функцию, которая будет запускаться при команде старт и создавать запись.
async def create_profile(user_id):
    # Если пользователь уже создан возвращаем его, иначе добавляем в базу данных.
    # Метод fetchone берёт значение из базы данных и возвращает его.
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
    inf_name = information_name(user_id)
    # Создаём контекстный менеджер для работы с базой данных.
    async with state.proxy() as data:
        if user and user[0].startswith(', '):
            user[0] = user[0][2:]
        user.append(data['anime_list'])
        if not inf_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE animation.anime SET (name, anime_list) = ('{data['name']}', '{', '.join(user)}')"
                    f"WHERE user_id = '{user_id}'"
                )
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE animation.anime SET anime_list = '{', '.join(user)}'"
                    f"WHERE user_id = '{user_id}'"
                )
