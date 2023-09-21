from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Клавиатура, которая отображается снизу экрана.
def get_kb() -> ReplyKeyboardMarkup:
    # Создаём список, в котором внутренние списки означают количество строк и сколько в каждой строке элементов.
    kb = [
        [
            KeyboardButton(text='/create'),
            KeyboardButton(text='/output'),
            KeyboardButton(text='/link')
        ],
        [
            KeyboardButton(text='/projects'),
            KeyboardButton(text='/description'),
            KeyboardButton(text='/help')
        ],
        [
            KeyboardButton(text='/delete')
        ],
    ]

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return keyboard


# Прикреплённая к сообщению клавиатура для показа репозиториев на github.
def get_github() -> InlineKeyboardMarkup:
    urlkb = InlineKeyboardMarkup(row_width=1)
    urlbtn = InlineKeyboardButton(text='Github', url='https://github.com/Shearer2?tab=repositories')
    urlkb.add(urlbtn)

    return urlkb


# Прикреплённая к сообщению клавиатура для показа всех проектов в телеграм.
def get_projects() -> InlineKeyboardMarkup:
    # Параметр означает количество столбцов.
    urlkb = InlineKeyboardMarkup(row_width=1)
    urlbtn = InlineKeyboardButton(text='Линия слова', url='https://t.me/s/Line_words_bot/')
    urlbtn1 = InlineKeyboardButton(text='Заметки', url='https://t.me/s/saved_notes_bot/')
    urlbtn2 = InlineKeyboardButton(text='Висельница', url='https://t.me/s/Game_Gallow_Bot/')
    urlkb.add(urlbtn, urlbtn1, urlbtn2)

    return urlkb


# Кнопка для выхода из режима создания и заполнения анкеты.
def get_cancel() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='/cancel')
        ],
    ]

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return keyboard
