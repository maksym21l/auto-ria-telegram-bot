import asyncio
import re
import traceback

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bs4 import BeautifulSoup
import aiohttp
from datetime import datetime, timedelta

from parsers import CAR_BRANDS
from kb import menu, btn, pagination_kb, auto_monitoring_kb, back_kb
from database.db import (
    create_db,
    drop_db,
    AsyncSessionLocal,
    Filter,
    SentCar,
    CountCar,
)
from sqlalchemy import select, delete


# --- Клас для станів ---
class FilterForm(StatesGroup):
    min_price = State()
    max_price = State()
    min_year = State()
    max_year = State()
    city = State()
    mark = State()

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                         '(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0'
           }

current_year = datetime.now().year + 1

def parse_ua_relative_datetime(text: str) -> datetime | None:
    """
    Перетворює український відносний час публікації у datetime.
    Підтримуються лише хвилини та години.
    Інші формати ігноруються (повертає None).
    """

    if not text:
        return None

    text = text.strip().lower()
    now = datetime.now()

    # хвилину тому
    if text == "хвилину тому":
        return now - timedelta(minutes=1)

    # годину тому
    if text == "годину тому":
        return now - timedelta(hours=1)

    # N хвилин тому
    match_minutes = re.match(r"(\d+)\s+хвилин(и)?\s+тому", text)
    if match_minutes:
        minutes = int(match_minutes.group(1))
        return now - timedelta(minutes=minutes)

    # N годин тому
    match_hours = re.match(r"(\d+)\s+годин(и)?\s+тому", text)
    if match_hours:
        hours = int(match_hours.group(1))
        return now - timedelta(hours=hours)

    # решта форматів не беремо
    return None



# --- Словник міст і областей ---
city_to_state_id = {
    "Вінниця": 1, "Житомир": 2, "Тернопіль": 3, "Хмельницьк": 4, "Львів": 5,
    "Чернігів": 6, "Харків": 7, "Суми": 8, "Рівне": 9,
    "Київ": 10, "Дніпро": 11, "Одеса": 12, "Донецьк": 13,
    "Запоріжжя": 14, "Івано-Франківськ": 15, "Кіровоград": 16, "Волинь": 18,
    "Миколаїв": 19, "Полтава": 20, "Закарпаття": 22,
    "Херсон": 23, "Черкаси": 24, "Чернівці": 25, "Луганськ": 26
}

# --- Ініціалізація бота ---
bot = Bot(token='7834132939:AAEW-A4HH56k5z9RG-4eDUq4cadm7SDfZmA')
dp = Dispatcher()

# --- Старт ---
@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer(
        '🚗 AutoMonitor Bot\n\n'
        'Допоможу знайти авто швидше за інших.\n\n'
        '🔍 Що я вмію:\n'
        '• Моніторю нові оголошення\n'
        '• Фільтрую за ціною, роком, містом\n'
        '• Надсилаю тільки нові варіанти\n\n'
        '⚡ Ти отримуєш авто одразу після публікації\n\n'
        'Натисни кнопку нижче, щоб налаштувати пошук 👇',
        reply_markup=menu
    )

async def show_filter(message: types.Message, user_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == user_id)
        )
        quality = result.scalar_one_or_none()

    if not quality:
        await message.answer("❌ Ви ще не задали фільтр", reply_markup=btn)
        return

    city_name = next(
        (k for k, v in city_to_state_id.items() if v == quality.city),
        "Невідоме місто"
    )
    mark_name = next(
        (k for k, v in CAR_BRANDS.items() if v == quality.mark_car),
        "Невідома марка"
    )

    await message.answer(
        f'💰 Ціна: {quality.min_price} - {quality.max_price}\n'
        f'📆 Рік: {quality.min_year} - {quality.max_year}\n'
        f'📍 Місто: {city_name}\n'
        f'🚗 Марка: {mark_name}',
        reply_markup=btn
    )

# --- Налаштування ---
@dp.message(lambda message: message.text == '🔧 Налаштування')
async def settings(message: types.Message):
    user = message.from_user.id

    await show_filter(message, user)


@dp.message(lambda message: message.text == '⬅️ Назад')
async def back(message: types.Message, state: FSMContext):
    await message.answer(reply_markup=btn)
    user = message.from_user.id

    await message.answer(
        '<b>🔧 Налаштування пошуку</b>\n\nОбери, що хочеш змінити:',
        reply_markup=btn,
        parse_mode='HTML'
    )
    await show_filter(message, user)


# --- Ціна ---
@dp.message(lambda message: message.text == '💰 Ціна')
async def price(message: types.Message, state: FSMContext):
    await message.answer('Введи мінімальну ціну:', reply_markup=back_kb)
    await state.set_state(FilterForm.min_price)

@dp.message(StateFilter(FilterForm.min_price))
async def set_min_price(message: types.Message, state: FSMContext):
    try:
        min_price = int(message.text)
    except ValueError:
        await message.answer('❌ Введи число, наприклад: 8000')
        return

    await state.update_data(min_price=min_price)

    await message.answer('Введи максимальну ціну:')
    await state.set_state(FilterForm.max_price)

@dp.message(StateFilter(FilterForm.max_price))
async def set_max_price(message: types.Message, state: FSMContext):
    try:
        max_price = int(message.text)
    except ValueError:
        await message.answer('❌ Введи число, наприклад: 12000')
        return

    data = await state.get_data()
    min_price = data.get('min_price')

    if min_price is None:
        await message.answer('❌ Помилка: мінімальна ціна не задана')
        await state.clear()
        return

    if max_price <= min_price:
        await message.answer(
            '❌ Максимальна ціна не може бути меншою або рівною мінімальній'
        )
        return

    # 🔹 зберігаємо у FSM
    await state.update_data(max_price=max_price)
    user_id = message.from_user.id

    # 🔹 ЗАПИС У БД (ASYNC правильно)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == user_id)
        )
        filter_db = result.scalar_one_or_none()

        if not filter_db:
            filter_db = Filter(user_id=user_id)
            db.add(filter_db)

        filter_db.min_price = min_price
        filter_db.max_price = max_price

        await db.commit()

    await show_filter(message, message.from_user.id)

    # FSM завершено
    await state.clear()



# --- Рік ---
@dp.message(lambda message: message.text == '📆 Рік')
async def set_year(message: types.Message, state: FSMContext):
    await message.answer('Введи мінімальний рік:')
    await state.set_state(FilterForm.min_year)

@dp.message(StateFilter(FilterForm.min_year))
async def set_min_year(message: types.Message, state: FSMContext):
    try:
        min_year = int(message.text)
        if min_year < 1900:
            await message.answer('❌ Рік не може бути меншим за 1900')
            return
    except ValueError:
        await message.answer('❌ Введи число, наприклад: 2000')
        return

    # ✅ Зберігаємо ТІЛЬКИ в FSM
    await state.update_data(min_year=min_year)

    await message.answer('Введи максимальний рік:')
    await state.set_state(FilterForm.max_year)


@dp.message(StateFilter(FilterForm.max_year))
async def set_max_year(message: types.Message, state: FSMContext):
    max_year = int(message.text)

    data = await state.get_data()
    min_year = data['min_year']

    user_id = message.from_user.id

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == user_id)
        )
        filter_db = result.scalar_one_or_none()

        if not filter_db:
            filter_db = Filter(user_id=user_id)
            db.add(filter_db)

        filter_db.min_year = min_year
        filter_db.max_year = max_year
        await db.commit()

    await show_filter(message, user_id)
    await state.clear()



# --- Місто ---
rows = []
keys = list(city_to_state_id.keys())
for i in range(0, len(keys), 3):
    rows.append([types.KeyboardButton(text=k) for k in keys[i:i+3]])

city_buttons = types.ReplyKeyboardMarkup(
    keyboard=rows,
    resize_keyboard=True,
    one_time_keyboard=True
)

@dp.message(lambda message: message.text == '📍 Місто')
async def ask_city(message: types.Message, state: FSMContext):
    await message.answer("Оберіть область/місто:", reply_markup=city_buttons)
    await state.set_state(FilterForm.city)

@dp.message(StateFilter(FilterForm.city))
async def set_city(message: types.Message, state: FSMContext):
    city_name = message.text

    if city_name not in city_to_state_id:
        await message.answer("❌ Обери місто зі списку кнопок.")
        return

    city_id = city_to_state_id[city_name]
    user_id = message.from_user.id

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == user_id)
        )
        filter_db = result.scalar_one_or_none()

        if not filter_db:
            filter_db = Filter(user_id=user_id)
            db.add(filter_db)

        filter_db.city = city_id
        await db.commit()

    await show_filter(message, user_id)
    await state.clear()



# Формуємо кнопки для марок
rows_mark = []
keys_mark = list(CAR_BRANDS.keys())

for i in range(0, len(keys_mark), 3):
    rows_mark.append([types.KeyboardButton(text=k) for k in keys_mark[i:i + 3]])

mark_buttons = types.ReplyKeyboardMarkup(
    keyboard=rows_mark,
    resize_keyboard=True,
    one_time_keyboard=True
)


# Обробка вибору марки
@dp.message(lambda message: message.text == '🚗 Марка')
async def car_mark(message: types.Message, state: FSMContext):
    await message.answer("Оберіть марку автомобіля:", reply_markup=mark_buttons)
    await state.set_state(FilterForm.mark)


@dp.message(StateFilter(FilterForm.mark))
async def set_mark(message: types.Message, state: FSMContext):
    mark_name = message.text

    if mark_name not in CAR_BRANDS:
        await message.answer("❌ Обери марку зі списку кнопок.")
        return

    mark_id = CAR_BRANDS[mark_name]
    user_id = message.from_user.id

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == user_id)
        )
        filter_db = result.scalar_one_or_none()

        if not filter_db:
            filter_db = Filter(user_id=user_id)
            db.add(filter_db)

        filter_db.mark_car = mark_id
        await db.commit()

    await show_filter(message, user_id)
    await state.clear()



@dp.message(lambda message: message.text == '✅ Готово')
async def done(message: types.Message, state: FSMContext):
    await message.answer(
        f"✅ Фільтр збережено та готовий до моніторингу\n\n",
        reply_markup=menu
    )

    await state.clear()


# --- Допомога ---
@dp.message(lambda message: message.text == '❓ Допомога')
async def help(message: types.Message):
    await message.answer(
        "❓ Як це працює\n\n"
        "1️⃣ Ти задаєш фільтри\n"
        "2️⃣ Я перевіряю нові оголошення\n"
        "3️⃣ Надсилаю тільки ті, що підходять\n",
        reply_markup=menu
    )

# --- Моніторинг ---
@dp.message(lambda message: message.text == '▶️ Моніторинг')
async def start_monitoring(message: types.Message):
    try:
        await message.answer("🔎 Запускаю моніторинг", reply_markup=menu)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Filter).where(Filter.user_id == message.from_user.id)
            )
            filters = result.scalar_one_or_none()
        if not filters:
            await message.answer("❌ Фільтр не знайдено, спершу налаштуй його")
            return

        base_url = (
            f'https://auto.ria.com/uk/search/?&brand={filters.mark_car}&state[0]={filters.city}&year[0]={filters.min_year}&year[1]={filters.max_year}&price[1]={filters.min_price}&price[2]={filters.max_price}&limit=10'
        )
        print(base_url)

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers) as response:
                html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            cars = soup.find_all('a', class_='link product-card horizontal')

            if not cars:
                await message.answer("Нічого не знайдено за цим фільтром 😔")
                return

            for car in cars:
                link = car.get('href')
                link = f'https://auto.ria.com{link}' if link else None
                print(link)

                if not link:
                    continue

                model_tag = car.find('div', class_='common-text size-16-20 titleS fw-bold mb-4')
                model = model_tag.text.strip() if model_tag else 'N/A'

                price_tag = car.find('span', class_='common-text titleM c-green')
                price = price_tag.text.strip() if price_tag else 'N/A'

                info_tags = car.find_all('span', class_='common-text ellipsis-1 body')
                fuel = info_tags[0].text.strip() if len(info_tags) > 0 else 'N/A'
                gear_box = info_tags[1].text.strip() if len(info_tags) > 1 else 'N/A'
                mileage = info_tags[2].text.strip() if len(info_tags) > 2 else 'N/A'
                city_text = info_tags[3].text.strip() if len(info_tags) > 3 else 'N/A'

                time_post_tag = car.find('span', class_='common-text footnote c-contrastSecondary')
                time_post = time_post_tag.text.strip() if time_post_tag else 'Не вказано'

                text = (
                    f"🚗 Модель: {model}\n"
                    f"📅 Рік: {model.split()[-1] if model != 'N/A' else 'N/A'}\n"
                    f"💰 Ціна: {price}\n"
                    f"📍 Місто: {city_text}\n"
                    f"📏 Пробіг: {fuel}\n"
                    f"⛽ Паливо: {mileage}\n"
                    f"⚙️ Коробка: {gear_box}\n"
                    f"🕒 Опубліковано: {time_post}\n"
                    f"🔗 Посилання: {link}"
                )

                filters.last_checked = datetime.now()

                await message.answer(text)
            await db.commit()

            await message.answer("Ось перші 10 оголошень з Auto.Ria, якщо бажаєте продовжити натисніть кнопку нижче", reply_markup=pagination_kb)

    except Exception as e:
        await message.answer(f"❌ Сталася помилка: {e}")
    finally:
        await db.close()

@dp.message(lambda message: message.text == '▶️ Продовжити')
async def pagination(message: types.Message):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == message.from_user.id)
        )
        filters = result.scalar_one_or_none()

        if not filters:
            await message.answer("❌ Фільтр не знайдено, спершу налаштуй його")
            return

        page = filters.page_count + 1
        filters.page_count = page
        await db.commit()

        base_url = (
            f"https://auto.ria.com/uk/search/?"
            f"&brand={filters.mark_car}"
            f"&state[0]={filters.city}"
            f"&year[0]={filters.min_year}"
            f"&year[1]={filters.max_year}"
            f"&price[1]={filters.min_price}"
            f"&price[2]={filters.max_price}"
            f"&limit=10&page={page}"
        )

    # --- HTTP окремо ---
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, headers=headers) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "lxml")
    cars = soup.find_all('a', class_='link product-card horizontal')

    if not cars:
        await message.answer("😔 Нічого не знайдено за цим фільтром")
        return

    async with AsyncSessionLocal() as db:
        new_cars_texts = []
        for car in cars:
            link = car.get('href')
            if not link:
                continue
            link = f'https://auto.ria.com{link}'

            # Перевірка чи вже надсилали
            result = await db.execute(
                select(SentCar).where(
                    SentCar.user_id == message.from_user.id,
                    SentCar.car_link == link
                )
            )
            already_sent = result.scalar_one_or_none()
            if already_sent:
                continue

            # Формуємо текст
            model_tag = car.find('div', class_='common-text size-16-20 titleS fw-bold mb-4')
            model = model_tag.text.strip() if model_tag else 'N/A'

            price_tag = car.find('span', class_='common-text titleM c-green')
            price = price_tag.text.strip() if price_tag else 'N/A'

            info = car.find_all('span', class_='common-text ellipsis-1 body')
            fuel = info[0].text.strip() if len(info) > 0 else 'N/A'
            gear = info[1].text.strip() if len(info) > 1 else 'N/A'
            mileage = info[2].text.strip() if len(info) > 2 else 'N/A'
            city_text = info[3].text.strip() if len(info) > 3 else 'N/A'

            time_tag = car.find('span', class_='common-text footnote c-contrastSecondary')
            time_post = time_tag.text.strip() if time_tag else 'Не вказано'

            text = (
                f"🚗 Модель: {model}\n"
                f"💰 Ціна: {price}\n"
                f"📍 Місто: {city_text}\n"
                f"📏 Пробіг: {mileage}\n"
                f"⛽ Паливо: {fuel}\n"
                f"⚙️ Коробка: {gear}\n"
                f"🕒 Опубліковано: {time_post}\n"
                f"🔗 {link}"
            )

            # Зберігаємо лінк у БД
            db.add(SentCar(user_id=message.from_user.id, car_link=link))
            new_cars_texts.append(text)

        await db.commit()

    # Надсилаємо повідомлення користувачу
    for text in new_cars_texts:
        await message.answer(text)

    await message.answer("▶️ Показати ще оголошення", reply_markup=pagination_kb)


# =========================
# Команда зупинки моніторингу
# =========================
@dp.message(lambda message: message.text == '⛔ Зупинити')
async def stop_monitoring(message: types.Message):
    await message.answer("🛑 Моніторинг зупинено", reply_markup=menu)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Filter).where(Filter.user_id == message.from_user.id)
        )
        filters = result.scalar_one_or_none()

        if filters:
            filters.page_count = 0
            await db.commit()




# Обмеження одночасних запитів
semaphore = asyncio.Semaphore(25)  # максимум 25 одночасних HTTP-запитів

async def auto_monitoring(user_filter: Filter, session: aiohttp.ClientSession):
    """
    Оптимізований моніторинг нових авто для одного користувача.
    """
    try:
        async with semaphore:
            last_checked = user_filter.last_checked or datetime.min
            new_cars_text = []
            new_sent_cars = []

            base_url = (
                f"https://auto.ria.com/uk/search/?"
                f"brand={user_filter.mark_car}"
                f"&state[0]={user_filter.city}"
                f"&year[0]={user_filter.min_year}"
                f"&year[1]={user_filter.max_year}"
                f"&price[1]={user_filter.min_price}"
                f"&price[2]={user_filter.max_price}"
                f"&limit=20"
            )

            async with session.get(base_url, headers=headers) as response:
                html = await response.text()

            soup = BeautifulSoup(html, "lxml")
            cars = soup.find_all("a", class_="link product-card horizontal")
            if not cars:
                return

            async with AsyncSessionLocal() as db:
                # отримуємо вже надіслані лінки одним запитом
                result = await db.execute(
                    select(SentCar.car_link).where(SentCar.user_id == user_filter.user_id)
                )
                sent_links = {row[0] for row in result.all()}

                for car in cars:
                    link = car.get("href")
                    if not link:
                        continue
                    link = f"https://auto.ria.com{link}"
                    if link in sent_links:
                        continue

                    time_tag = car.find("span", class_="common-text footnote c-contrastSecondary")
                    time_post = parse_ua_relative_datetime(time_tag.text.strip()) if time_tag else None
                    if not time_post or time_post <= last_checked:
                        continue

                    model_tag = car.find("div", class_="common-text size-16-20 titleS fw-bold mb-4")
                    model = model_tag.text.strip() if model_tag else 'N/A'

                    price_tag = car.find('span', class_='common-text titleM c-green')
                    price = price_tag.text.strip() if price_tag else 'N/A'

                    info_tags = car.find_all('span', class_='common-text ellipsis-1 body')
                    fuel = info_tags[0].text.strip() if len(info_tags) > 0 else 'N/A'
                    gear_box = info_tags[1].text.strip() if len(info_tags) > 1 else 'N/A'
                    mileage = info_tags[2].text.strip() if len(info_tags) > 2 else 'N/A'
                    city_text = info_tags[3].text.strip() if len(info_tags) > 3 else 'N/A'

                    time_post_str = time_tag.text.strip() if time_tag else 'Не вказано'

                    text = (
                        f"🚗 Модель: {model}\n"
                        f"💰 Ціна: {price}\n"
                        f"📍 Місто: {city_text}\n"
                        f"📏 Пробіг: {mileage}\n"
                        f"⛽ Паливо: {fuel}\n"
                        f"⚙️ Коробка: {gear_box}\n"
                        f"🕒 Опубліковано: {time_post_str}\n"
                        f"🔗 {link}"
                    )

                    new_cars_text.append(text)
                    new_sent_cars.append(SentCar(user_id=user_filter.user_id, car_link=link))

                if new_sent_cars:
                    db.add_all(new_sent_cars)
                    user_filter.last_checked = datetime.now()
                    db.add(user_filter)
                    await db.commit()

            # надсилаємо пакетами
            if new_cars_text:
                batch_size = 5
                for i in range(0, len(new_cars_text), batch_size):
                    group_text = "\n\n".join(new_cars_text[i:i+batch_size])
                    try:
                        await bot.send_message(
                            user_filter.user_id,
                            group_text,
                            reply_markup=types.ReplyKeyboardMarkup(
                                keyboard=[[types.KeyboardButton(text="🚗 Переглянути авто")]],
                                resize_keyboard=True
                            )
                        )
                    except Exception as e:
                        print(f"Не вдалося надіслати користувачу {user_filter.user_id}: {e}")

    except Exception as e:
        print("Помилка авто-моніторингу:", e)
        traceback.print_exc()


async def periodic_monitoring():
    """
    Періодичний моніторинг для всіх користувачів.
    """
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with AsyncSessionLocal() as db:
                    filters = (await db.execute(select(Filter))).scalars().all()

                if filters:
                    await asyncio.gather(
                        *[auto_monitoring(f, session) for f in filters],
                        return_exceptions=True
                    )
            except Exception as e:
                print("Помилка в періодичному моніторингу:", e)

            await asyncio.sleep(1800)  # 30 хвилин




# =========================
# Перегляд авто користувачем
# =========================
@dp.message(lambda m: m.text == "🚗 Переглянути авто")
async def view_cars(message: types.Message):
    async with AsyncSessionLocal() as db:
        # Отримуємо всі авто для користувача
        result = await db.execute(
            select(SentCar).where(SentCar.user_id == message.from_user.id)
        )
        cars = result.scalars().all()

        if not cars:
            await message.answer("Немає нових авто")
            return

        # Надсилаємо кожне авто
        for car in cars:
            await message.answer(car.car_link, reply_markup=auto_monitoring_kb)

        # Очищаємо записи про відправлені авто
        await db.execute(delete(SentCar).where(SentCar.user_id == message.from_user.id))
        await db.execute(delete(CountCar).where(CountCar.user_id == message.from_user.id))

        # Оновлюємо фільтр користувача
        result = await db.execute(
            select(Filter).where(Filter.user_id == message.from_user.id)
        )
        user_filter = result.scalar_one_or_none()
        if user_filter:
            user_filter.last_checked = datetime.now()
            user_filter.page_count = 0

        await db.commit()



@dp.message(lambda message: message.text == "⛔ До головного меню")
async def sent_main_menu(message: types.Message):
    await message.answer('Головне меню', reply_markup=menu)


@dp.message(lambda message: message.text == '🤖 Авто моніторинг')
async def run_monitoring_auto(message: types.Message):
    await message.answer(
        'Автомоніторинг запущено, ми вас повідомимо, якщо знайдемо нову машину :)',
        reply_markup=menu
    )

    # Перевірка, чи вже запущено періодичний моніторинг
    if not hasattr(bot, "monitoring_task") or bot.monitoring_task.done():
        # Створюємо один таск для всіх користувачів
        bot.monitoring_task = asyncio.create_task(periodic_monitoring())


# --- Запуск бота і моніторингу одночасно ---
async def main_async():
    polling_task = asyncio.create_task(dp.start_polling(bot))
    await asyncio.gather(polling_task)


async def main():
    await create_db()
    await main_async()

if __name__ == "__main__":
    print('Bot started')
    asyncio.run(main())
