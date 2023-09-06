import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from sqlite import db_start, create_profile, edit_profile, information_id, information_anime


async def on_startup(_):
    await db_start()


# Загружаем переменные среды, которые нужно скрыть от постронних глаз.
load_dotenv()

storage = MemoryStorage()
bot = Bot(token=os.getenv('TOKEN_API'))
dp = Dispatcher(bot, storage=storage)


# Класс для хранения всех состояний бота.
class ProfileStatesGroup(StatesGroup):
    name = State()
    anime_list = State()


def get_kb() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='/create'),
            KeyboardButton(text='/input'),
            KeyboardButton(text='/help')
        ],
    ]

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return keyboard


def get_cancel() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='/cancel')
        ],
    ]

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return keyboard


# Делаем обработчик команды cancel, а чтобы указать любое возможное состояние достаточно указать *.
@dp.message_handler(commands=['cancel'], state='*')
async def bot_cancel(message: types.Message, state: FSMContext) -> None:
    if state is None:
        return

    await state.finish()
    await message.reply('Вы прервали создание анкеты.',
                        reply_markup=get_kb())


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    await message.answer('Добро пожаловать! Чтобы создать профиль для хранения информации нажмите /create.',
                         reply_markup=get_kb())
    # Создаём профиль.
    #await create_profile(user_id=message.from_user.id)


@dp.message_handler(commands=['create'])
async def bot_create(message: types.Message) -> None:
    inf_user = information_id()
    if message.from_user.id not in inf_user:
        # Создаём профиль.
        await create_profile(user_id=message.from_user.id)
        await message.answer('Создание профиля! Для начала отправьте ваше имя.',
                             reply_markup=get_cancel())
        # Устанавливаем состояние имя при помощи метода set.
        await ProfileStatesGroup.name.set()
    else:
        await message.reply('Отправьте название аниме и серии, на которой вы остановились.')
        await ProfileStatesGroup.anime_list.set()


@dp.message_handler(commands=['input'])
async def bot_input(message: types.Message) -> None:
    await message.answer(information_anime(user_id=message.from_user.id))


# Состояние name, так как мы изменили его на следующее.
@dp.message_handler(state=ProfileStatesGroup.name)
async def state_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text

    await message.reply('Отправьте название аниме и серии, на которой вы остановились.')
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.anime_list)
async def state_description(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['anime_list'] = message.text
    # После того как весь процесс по созданию профиля завершён, будем сохранять его в базу данных.
    await edit_profile(state, user_id=message.from_user.id)
    await message.reply('Ваша информация сохранена.')
    # Завершаем состояние.
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
