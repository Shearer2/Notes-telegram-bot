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


# Асинхронная функция для запуска базы данных.
async def db_start():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS animation.anime(user_id serial PRIMARY KEY, name varchar(255), "
            "anime_list varchar(255))"
        )



    '''global db, cur
    # Экземпляр базы данных.
    db = sq.connect('animation.db')
    # Создаём курсор для выполнения операций с базой данных.
    cur = db.cursor()

    # Создаём таблицы в базе данных.
    # Если таблица anime не существует, то создаём её с полями user_id, name, anime_list.
    cur.execute("CREATE TABLE IF NOT EXISTS anime(user_id TEXT PRIMARY KEY, name TEXT, anime_list TEXT)")
    db.commit()'''


# Создаём функцию, которая будет запускаться при команде старт и создавать запись.
async def create_profile(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""SELECT 1 FROM animation.anime WHERE user_id = '{user_id}'"""
        )
        user = cursor.fetchone()
    # Если пользователь уже создан возвращаем его, иначе добавляем в базу данных.
    # Метод fetchone берёт значение из базы данных и возвращает его.
    #user = cur.execute(f"SELECT 1 FROM anime WHERE user_id == '{user_id}'").fetchone()
    if not user:
        # Создаём пустой профиль, а при команде create начнём его заполнять.
        #cur.execute("INSERT INTO anime VALUES(?, ?, ?)", (user_id, '', ''))
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO animation.anime (user_id, name, anime_list)
                VALUES ({user_id}, '', '')
            """)
        # Вызываем commit для завершения нашей операции.
        #db.commit()


# Заполняем профиль, для этого передаём состояние бота и идентификатор пользователя.
async def edit_profile(state, user_id):
    # Создаём контекстный менеджер для работы с базой данных.
    async with state.proxy() as data:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE animation.anime SET (name, anime_list) = ('{data['name']}', '{data['anime_list']}')"
                f"WHERE user_id = '{user_id}'"
            )
        #cur.execute(f"UPDATE anime SET name = '{data['name']}', anime_list = '{data['anime_list']}' WHERE user_id == '{user_id}'")
        #db.commit()
