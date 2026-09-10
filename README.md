# 🚗 AutoRia Telegram Bot

Telegram-бот для пошуку та автоматичного моніторингу автомобільних оголошень на AutoRia.

Бот дозволяє задавати критерії пошуку, знаходити відповідні автомобілі та автоматично отримувати повідомлення про нові оголошення.

## ✨ Features

* 🔎 Пошук автомобілів за фільтрами
* 💰 Фільтрація за ціною
* 📅 Фільтрація за роком випуску
* 🚘 Фільтрація за маркою автомобіля
* 📍 Фільтрація за містом
* 🔄 Автоматичний моніторинг нових оголошень
* 📩 Надсилання нових оголошень у Telegram
* ⚙️ Налаштування критеріїв пошуку через бота
* 🆘 Розділ допомоги
* 🗄️ PostgreSQL для збереження історії оголошень
* 🚫 Захист від повторного надсилання одного оголошення

## 🛠️ Tech Stack

* Python
* aiogram 3
* BeautifulSoup
* PostgreSQL
* asyncio
* requests

## 🏗️ Architecture

```text
AutoRia
   │
   ▼
Parser
   │
   ▼
Data processing
   │
   ├── New advertisement
   │
   ▼
PostgreSQL
   │
   ▼
Telegram Bot
   │
   ▼
User
```

## ⚙️ Installation

### 1. Clone repository

```bash
git clone https://github.com/YOUR_USERNAME/auto-ria-telegram-bot.git
cd auto-ria-telegram-bot
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token

DB_HOST=localhost
DB_PORT=5432
DB_NAME=auto_ria_bot
DB_USER=postgres
DB_PASSWORD=your_password
```

### 5. Run the bot

```bash
python main.py
```

## 📋 Bot functionality

The user can:

1. Configure search filters
2. Run a manual search
3. Enable automatic monitoring
4. Receive notifications about new advertisements
5. Change search parameters at any time

## 🗄️ Database

PostgreSQL is used to store previously processed advertisements.

This prevents the bot from sending the same advertisement multiple times.

## 🔐 Environment Variables

Sensitive data is stored in environment variables and is not included in the repository.

See `.env.example` for the required configuration.

## ⚠️ Disclaimer

This project is created for educational and portfolio purposes.

Users should respect AutoRia's terms of service and applicable laws when using automated data collection tools.

## 👨‍💻 Author

**Maksym Lesiv**

Python Developer / Business Analyst

GitHub: [maksym21l](https://github.com/maksym21l)
