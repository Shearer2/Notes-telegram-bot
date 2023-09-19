import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from keyboard import get_kb, get_github, get_projects, get_cancel
from postgresql import db_start, create_profile, edit_profile, information_id, information_anime


async def on_startup(_):
    await db_start()


# Загружаем переменные среды, которые нужно скрыть от постронних глаз.
load_dotenv()

# Создаём память для хранения состояний.
storage = MemoryStorage()
# Передаём в бота api токен из окружения.
bot = Bot(token=os.getenv('TOKEN_API'))
dp = Dispatcher(bot, storage=storage)
# Текст с доступными командами.
help_inf = """
<b>/start</b> - <em>начать работу с ботом.</em>
<b>/create</b> - <em>создать анкету или добавить информацию к созданной анкете.</em>
<b>/output</b> - <em>вывести список.</em>
<b>/link</b> - <em>перейти в репозиторий github.</em>
<b>/projects</b> - <em>ознакомиться с проектами.</em>
<b>/description</b> - <em>описание проекта.</em>
<b>/help</b> - <em>вывести список команд.</em>
"""


# Класс для хранения всех состояний бота.
class ProfileStatesGroup(StatesGroup):
    name = State()
    anime_list = State()
    season = State()
    series = State()


# Делаем обработчик команды cancel, а чтобы указать любое возможное состояние достаточно указать *.
@dp.message_handler(commands=['cancel'], state='*')
async def bot_cancel(message: types.Message, state: FSMContext) -> None:
    # Переходим в конечное состояние, чтобы отменить процесс создания или заполнения анкеты.
    await state.finish()
    await message.reply('Вы прервали создание анкеты.',
                        reply_markup=get_kb())


# Обработчик команды старт.
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    await message.answer('Добро пожаловать! Чтобы создать профиль для хранения информации нажмите /create.',
                         reply_markup=get_kb())


# Обработчик команды создания или заполнения анкеты.
@dp.message_handler(commands=['create'])
async def bot_create(message: types.Message) -> None:
    # Записываем в переменную все доступные id уже зарегистрированных пользователей.
    inf_user = information_id()
    # Если id нет среди зарегистрированных, то создаём профиль.
    if message.from_user.id not in inf_user:
        # Создаём профиль.
        await create_profile(user_id=message.from_user.id)
        await message.answer('Создание профиля! Для начала отправьте ваше имя.',
                             reply_markup=get_cancel())
        # Устанавливаем состояние имя при помощи метода set.
        await ProfileStatesGroup.name.set()
    # Иначе добавляем в созданный профиль новые данные.
    else:
        await message.reply('Отправьте название аниме, которое вы хотите сохранить.', reply_markup=get_cancel())
        await ProfileStatesGroup.anime_list.set()


# Обработчик команды для вывода информации.
@dp.message_handler(commands=['output'])
async def bot_input(message: types.Message) -> None:
    # Отправляем в функцию id пользователя для вывода информации.
    await message.answer(information_anime(user_id=message.from_user.id))


# Обработчик команды для вывода репозиториев github.
@dp.message_handler(commands=['link'])
async def bot_link(message: types.Message) -> None:
    await message.answer('Репозиторий github:', reply_markup=get_github())


# Обработчик команды для вывода проектов в телеграме.
@dp.message_handler(commands=['projects'])
async def bot_projects(message: types.Message) -> None:
    await message.answer('Мои проекты:', reply_markup=get_projects())


# Описание бота.
@dp.message_handler(commands=['description'])
async def bot_description(message: types.Message) -> None:
    await message.answer('Данный бот предназначен для хранения вашей информации и выводе её при необходимости.')


# Отправка всех доступных команды пользователю.
@dp.message_handler(commands=['help'])
async def bot_help(message: types.Message) -> None:
    await message.answer(help_inf, parse_mode='HTML')


# Состояние name, так как мы изменили его на следующее.
@dp.message_handler(state=ProfileStatesGroup.name)
async def state_name(message: types.Message, state: FSMContext) -> None:
    # Используем контекстный менеджер для добавления в словарь имени пользователя.
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply('Отправьте название аниме, которое вы хотите сохранить.')
    # Переходим к следующему состоянию.
    await ProfileStatesGroup.next()


# Состояние для отправки пользователем названия аниме.
@dp.message_handler(state=ProfileStatesGroup.anime_list)
async def state_anime(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь название аниме.
    async with state.proxy() as data:
        data['anime_list'] = message.text
    await message.reply('Отправьте сезон, на котором остановились.')
    await ProfileStatesGroup.next()


# Состояние для сохранения сезона данного аниме.
@dp.message_handler(state=ProfileStatesGroup.season)
async def state_season(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь сезон, на котором остановились.
    async with state.proxy() as data:
        data['season'] = message.text
    await message.reply('Отправьте серию, на которой остановились.')
    await ProfileStatesGroup.next()


# Состояние для сохранения серии.
@dp.message_handler(state=ProfileStatesGroup.series)
async def state_series(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь серию, на которой остановились.
    async with state.proxy() as data:
        data['series'] = message.text
    # После того как весь процесс по созданию профиля завершён, будем сохранять его в базу данных.
    await edit_profile(state, user_id=message.from_user.id)
    await message.reply('Ваша информация сохранена.')
    # Завершаем состояние.
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
