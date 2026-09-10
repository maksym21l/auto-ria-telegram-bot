from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='▶️ Моніторинг'),
            KeyboardButton(text='🤖 Авто моніторинг')
        ],
        [
            KeyboardButton(text='🔧 Налаштування'),
            KeyboardButton(text='❓ Допомога')
        ]
    ],
    resize_keyboard=True
)


btn = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Ціна"), KeyboardButton(text="📆 Рік")],
        [KeyboardButton(text="📍 Місто"), KeyboardButton(text="🚗 Марка")],
        [KeyboardButton(text="✅ Готово")]
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

pagination_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='▶️ Продовжити')],
        [KeyboardButton(text="⛔ Зупинити")]
    ],
    resize_keyboard=True
)

auto_monitoring_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚗 Переглянути авто")],
        [KeyboardButton(text="⛔ До головного меню")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
