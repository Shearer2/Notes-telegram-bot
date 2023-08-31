import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from sqlite import db_start, create_profile, edit_profile


async def on_startup(_):
    await db_start()


# Загружаем переменные среды, которые нужно скрыть от постронних глаз.
load_dotenv()

storage = MemoryStorage()
bot = Bot(token=os.getenv('TOKEN_API'))
dp = Dispatcher(bot, storage=storage)


# Класс для хранения всех состояний бота.
class ProfileStatesGroup(StatesGroup):
    #photo = State()
    name = State()
    #age = State()
    #description = State()
    anime_list = State()


def get_kb() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='/create'),
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
    await create_profile(user_id=message.from_user.id)


@dp.message_handler(commands=['create'])
async def bot_create(message: types.Message) -> None:
    await message.answer('Создание профиля! Для начала отправьте ваше имя.',
                         reply_markup=get_cancel())
    # Устанавливаем состояние photo при помощи метода set.
    #await ProfileStatesGroup.photo.set()
    await ProfileStatesGroup.name.set()


# Устанавливаем фильтр, если отправленное сообщение не является фотографией, то вывести, что это не фотография.
#@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.photo)
#async def check_photo(message: types.Message) -> None:
#    await message.reply('Это не фотография.')

'''
# Обрабатываем фото и указываем состояние state, чтобы хендлер обрабатывал входящие фото только в состоянии state.
@dp.message_handler(content_types=['photo'], state=ProfileStatesGroup.photo)
async def state_photo(message: types.Message, state: FSMContext) -> None:
    # Используем менеджер контекста чтобы открыть локальное хранилище данных для хранения информации.
    async with state.proxy() as data:
        # В ключе photo сохраняем идентификатор фотографии.
        data['photo'] = message.photo[0].file_id

    await message.reply('Теперь отправь своё имя.')
    # Изменяем состояние на следующее.
    await ProfileStatesGroup.next()
'''
'''
@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) > 100, state=ProfileStatesGroup.age)
async def check_age(message: types.Message) -> None:
    await message.reply('Введите реальный возраст.')
'''


# Состояние name, так как мы изменили его на следующее.
@dp.message_handler(state=ProfileStatesGroup.name)
async def state_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text

    #await message.reply('Теперь отправь свой возраст.')
    await message.reply('Отправьте название аниме.')
    await ProfileStatesGroup.next()


'''
# Состояние age, так как мы изменили его на следующее.
@dp.message_handler(state=ProfileStatesGroup.age)
async def state_age(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['age'] = message.text

    await message.reply('Теперь отправь своё описание.')
    await ProfileStatesGroup.next()
'''


#@dp.message_handler(state=ProfileStatesGroup.description)
@dp.message_handler(state=ProfileStatesGroup.anime_list)
async def state_description(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        #data['description'] = message.text
        data['anime_list'] = message.text
        # Фото будет отображаться только при таком вызове, при использовании message.answer будет отправлен
        # идентификатор фото, а не оно само.
        #await bot.send_photo(chat_id=message.from_user.id,
        #                     photo=data['photo'],
        #                     caption=f"{data['name']}, {data['age']}\n{data['description']}")
    # После того как весь процесс по созданию профиля завершён, будем сохранять его в базу данных.
    await edit_profile(state, user_id=message.from_user.id)
    await message.reply('Ваша информация сохранена.')
    # Завершаем состояние.
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
