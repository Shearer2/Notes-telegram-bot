import os
import psycopg2
import json
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


# Функция для получения id пользователей.
def information_id():
    # Получаем информацию из базы данных при помощи контекстного менеджера.
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT user_id FROM animation.anime"""
        )
        inf_user = list(map(lambda x: x[0], cursor.fetchall()))
    return inf_user


# Функция для получения имени пользователя по заданному id.
def information_name(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT name FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        name = cursor.fetchone()
    # Если имени нет в базе данных, то возвращаем False.
    if name is None:
        return False
    # Иначе возвращаем имя.
    return name[0]


# Функция для вывода списка аниме у данного пользователя.
def information_anime(user_id):
    # Добавляем счётчик для вывода информации с нумерацией.
    count = 0
    result = 'Ваш список аниме:\n'
    # Через контекстный менеджер получаем список аниме у данного пользователя по его id.
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT anime_list FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        anime_film = cursor.fetchone()
        # Если в базе данных присутствует словарь аниме и фильмов, то заносим его в переменную.
        if anime_film is not None:
            # Список аниме представлен в базе данных в json формате, поэтому переводим его в обычный словарь.
            anime = json.loads(anime_film[0])
        # Иначе создаём пустой словарь.
        else:
            anime = {}
    # Если словарь не пустой, то выводим текст со всеми аниме и фильмами.
    if anime:
        # Вытаскиваем данные по ключу (название аниме) и значению (сезон и серия), и добавляем их в переменную.
        for key, value in anime['Anime'].items():
            count += 1
            result += f'{count}) {key} {value}\n'
        result += '\nВаш список фильмов:\n'
        # Обнуляем счётчик.
        count = 0
        # Получаем данные по фильмам, вытаскивая ключ и значение.
        for key, value in anime['Films'].items():
            count += 1
            result += f'{count}) {key} {value}\n'
        return result
    # Иначе возвращаем напоминание, что анкета не была создана.
    else:
        return 'Вы не создали анкету.'


# Асинхронная функция для запуска базы данных.
async def db_start():
    # При помощи контекстного менеджера создаём таблицу в базе данных, если она ещё не была создана.
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS animation.anime(user_id bigserial PRIMARY KEY, name varchar(255), "
            "anime_list text)"
        )


# Создаём функцию, которая будет запускаться при команде старт и создавать запись.
async def create_profile(user_id):
    # Если id пользователя нет в базе данных.
    if user_id not in information_id():
        # Создаём пустой профиль, а при команде create начнём его заполнять.
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO animation.anime (user_id, name, anime_list)
                VALUES ({user_id}, '', '')
            """)


# Функция для удаления информации пользователя из базы данных.
async def delete_profile(user_id):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            DELETE FROM animation.anime WHERE user_id = '{user_id}'
        """)


# Заполняем профиль, для этого передаём состояние бота и идентификатор пользователя.
async def edit_profile(state, user_id):
    # Через контекстный менеджер получаем словарь аниме определённого пользователя.
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT anime_list FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        user = cursor.fetchone()
        # Если словарь не пустой, то переводим его из json формата в обычный словарь.
        if user[0]:
            user = json.loads(user[0])
        # Иначе создаём словарь с двумя ключами.
        else:
            user = {'Anime': {}, 'Films': {}}
    # Получаем имя пользователя.
    inf_name = information_name(user_id)
    # Создаём контекстный менеджер для работы с базой данных.
    async with state.proxy() as data:
        # Если пользователь вводил название аниме, то меняем словарь.
        if data['anime_list']:
            user['Anime'][data['anime_list']] = f"{data['season']} сезон {data['series']} серия."
        # Если пользователь вводил название фильма, то меняем словарь.
        if data['films']:
            user['Films'][data['films']] = f"{data['part']} часть."
        # Переводим словарь в json, второй параметр означает, что кодировку менять не нужно.
        json_data = json.dumps(user, ensure_ascii=False)
        # Если имя пользователя не указано, то обновляем имя пользователя и список аниме по указанному id.
        if not inf_name:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE animation.anime SET (name, anime_list) = ('{data['name']}', '{json_data}')"
                    f"WHERE user_id = '{user_id}'"
                )
        # Иначе обновляем только список аниме у заданного пользователя.
        else:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE animation.anime SET anime_list = '{json_data}'"
                    f"WHERE user_id = '{user_id}'"
                )
