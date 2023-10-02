import os
import hashlib
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from keyboard import get_kb, get_anime_films, get_github, get_projects, get_cancel
from postgresql import db_start, create_profile, delete_profile, edit_profile, information_id, information_name, \
    information_anime


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
<b>/delete</b> - <em>удалить анкету.</em>
<b>/output</b> - <em>вывести список.</em>
<b>/link</b> - <em>перейти в репозиторий github.</em>
<b>/projects</b> - <em>ознакомиться с проектами.</em>
<b>/description</b> - <em>описание проекта.</em>
<b>/help</b> - <em>вывести список команд.</em>
"""
# Создаём колбек данные, где первым параметром указываем название функции, в которой хранится инлайн клавиатура с
# колбеками, а вторым параметром разграничитель.
cb = CallbackData('get_anime_films', 'action')


# Класс для хранения всех состояний бота.
class ProfileStatesGroup(StatesGroup):
    name = State()
    # Расположил в таком порядке чтобы при команде смены состояния next оно переходило по очереди.
    anime_list = State()
    season = State()
    series = State()
    # Расположил так, чтобы при команде next состояние перешло на part.
    films = State()
    part = State()
    calbck = State()


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
    # Записываем в переменную имя данного пользователя по его id.
    inf_name = information_name(message.from_user.id)
    # Если имя у данного пользователя не указано, то создаём профиль.
    if not inf_name:
        # Создаём профиль.
        await create_profile(user_id=message.from_user.id)
        await message.answer('Создание профиля! Для начала отправьте ваше имя.',
                             reply_markup=get_cancel())
        # Устанавливаем состояние имя при помощи метода set.
        await ProfileStatesGroup.name.set()
    # Иначе переходим к выбору аниме или фильма для сохранения информации.
    else:
        await message.reply('Выберите то, что вы хотите сохранить:', reply_markup=get_anime_films())
        # Переходим в callback запрос.
        await ProfileStatesGroup.calbck.set()


# Обработчик команды удаления анкеты.
@dp.message_handler(commands=['delete'])
async def bot_delete(message: types.Message) -> None:
    # Если id пользователя есть в базе данных, то удаляем анкету.
    if message.from_user.id in information_id():
        await delete_profile(user_id=message.from_user.id)
        await message.answer('Ваша анкета была удалена!')
    # Иначе отправляем сообщение.
    else:
        await message.answer('Вы не создали анкету!')


# Обработчик команды для вывода информации.
@dp.message_handler(commands=['output'])
async def bot_input(message: types.Message) -> None:
    # Записываем в переменную имя данного пользователя по его id.
    inf_name = information_name(message.from_user.id)
    # Если имя данного пользователя имеется в базе данных, то мы выводим информацию.
    if inf_name:
        # Отправляем в функцию id пользователя для вывода информации.
        await message.answer(information_anime(user_id=message.from_user.id))
    # Иначе отправляем сообщение.
    else:
        await message.answer('Вы не создали анкету!')


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
    # Выводим инлайн клавиатуру с колбеком для выбора того, что мы хотим сохранить.
    await message.reply('Выберите то, что вы хотите сохранить:', reply_markup=get_anime_films())
    await ProfileStatesGroup.calbck.set()


# Создаём колбек функцию, чтобы узнать что нажал пользователь.
@dp.callback_query_handler(state=ProfileStatesGroup.calbck)
async def anime_film(callback: types.CallbackQuery) -> None:
    # Если пользователь нажал Аниме, то переходим к вводу названия, сезона и серии аниме.
    if callback.data == 'anime':
        # Заменяю сообщение с инлайн клавиатурой на данный текст, при нажатии на кнопку с колбеком.
        await callback.message.edit_text('Отправьте название аниме, которое вы хотите сохранить.')
        await ProfileStatesGroup.anime_list.set()
    # Если пользователь нажал Фильм, то переходим к вводу названия и части фильма.
    elif callback.data == 'film':
        await callback.message.edit_text('Отправьте название фильма, который вы посмотрели.')
        await ProfileStatesGroup.films.set()


# Состояние для отправки пользователем названия аниме.
@dp.message_handler(state=ProfileStatesGroup.anime_list)
async def state_anime(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь название аниме.
    async with state.proxy() as data:
        data['anime_list'] = message.text
    await message.reply('Отправьте сезон, на котором остановились.', reply_markup=get_cancel())
    await ProfileStatesGroup.next()


# Состояние для сохранения сезона данного аниме.
@dp.message_handler(state=ProfileStatesGroup.season)
async def state_season(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь сезон, на котором остановились.
    async with state.proxy() as data:
        data['season'] = message.text
    await message.reply('Отправьте серию, которую посмотрели.')
    await ProfileStatesGroup.next()


# Состояние для сохранения серии.
@dp.message_handler(state=ProfileStatesGroup.series)
async def state_series(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь серию, на которой остановились.
    async with state.proxy() as data:
        data['series'] = message.text
        # Чтобы не возникала ошибка, что ключ не найден, добавляем пустую строку в качестве значения ключа.
        data['films'] = ''
    # После того как весь процесс по созданию профиля завершён, будем сохранять его в базу данных.
    await edit_profile(state, user_id=message.from_user.id)
    await message.reply('Ваша информация сохранена.', reply_markup=get_kb())
    # Завершаем состояние.
    await state.finish()


# Состояние для сохранения фильма.
@dp.message_handler(state=ProfileStatesGroup.films)
async def state_films(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь фильм, который посмотрели.
    async with state.proxy() as data:
        data['films'] = message.text
    await message.reply('Отправьте часть, которую посмотрели.', reply_markup=get_cancel())
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.part)
async def state_part(message: types.Message, state: FSMContext) -> None:
    # Добавляем в словарь часть фильма, которую посмотрели.
    async with state.proxy() as data:
        data['part'] = message.text
        # Чтобы не возникала ошибка, что ключ не найден, задаём названию аниме пустую строку.
        data['anime_list'] = ''
    # Сохраняем результат в базу данных.
    await edit_profile(state, user_id=message.from_user.id)
    await message.reply('Ваша информация сохранена.', reply_markup=get_kb())
    # Завершаем состояние.
    await state.finish()


# Создаём инлайн запрос.
@dp.inline_handler()
async def inline_notes(inline_query: types.InlineQuery) -> None:
    # Получаем текст пользователя.
    text = inline_query.query
    # Формируем контент ответного сообщения. Достаём список фильмов и сериалов из базы данных по id пользователя.
    input_content = InputTextMessageContent(information_anime(user_id=inline_query['from']['id']))
    # Для отправки сообщения у него должен быть id, который создаём данным образом.
    result_id = hashlib.md5(text.encode()).hexdigest()
    # Для отправки текстового сообщения используется Article.
    item = InlineQueryResultArticle(
        input_message_content=input_content,
        id=result_id,
        title='Заметки',
        description='Ваш список',
        thumb_url='https://www.iguides.ru/upload/iblock/3a3/3a315b451eb73ac37392b3ff6802bb35.png'
    )
    # Отвечаем на инлайн запрос, передавая id сообщения, элементы, которыми будем отвечать, и время, за которое будут
    # кешироваться данные.
    await bot.answer_inline_query(inline_query_id=inline_query.id,
                                  results=[item],
                                  cache_time=1)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
