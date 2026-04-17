# 🐾 Cat Time Bot Z (FastAPI Edition)

![Лицензия](https://img.shields.io/github/license/1517mb/Cat_Time_Bot_Z)
<a href="https://www.python.org/" style="text-decoration: none;"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python&logoColor=ffdd54" height="20" alt="python"></a>
<a href="https://docs.aiogram.dev/" style="text-decoration: none;"><img src="https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white" height="20" alt="aiogram"></a>
<a href="https://docs.sqlalchemy.org/" style="text-decoration: none;"><img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=database&logoColor=white" height="20" alt="sqlalchemy"></a>
<br>
<a href="https://github.com/1517mb/Cat_Time_Bot_Z/commits" style="text-decoration: none;"><img src="https://img.shields.io/github/commit-activity/w/1517mb/Cat_Time_Bot_Z" height="20" alt="commit-activity"></a>
<a href="https://github.com/1517mb/Cat_Time_Bot_Z/commits" style="text-decoration: none;"><img src="https://img.shields.io/github/last-commit/1517mb/Cat_Time_Bot_Z" height="20" alt="last-commit"></a>
<a href="https://github.com/1517mb/Cat_Time_Bot_Z/issues" style="text-decoration: none;"><img src="https://img.shields.io/github/issues/1517mb/Cat_Time_Bot_Z" height="20" alt="issues"></a>
<br>
<img src="https://img.shields.io/github/repo-size/1517mb/Cat_Time_Bot_Z" height="20" alt="repo-size">
<img src="https://img.shields.io/github/languages/code-size/1517mb/Cat_Time_Bot_Z" height="20" alt="code-size">

Асинхронный Telegram-бот на базе **Aiogram 3** и **SQLAlchemy** для геймифицированного учета рабочего времени и выездов IT-специалистов. Бот не только считает отработанные часы, но и награждает пользователей достижениями, повышает уровни (от "Укротителя USB" до "Архитектора Систем") и рассылает ежедневные сводки (погода, валюты ЦБ РФ, крипта).

## ✨ Ключевые возможности
* ⏱ **Трекинг времени:** Команды `/join` и `/leave` для фиксации прибытия и ухода с точек.
* 🎮 **Геймификация:** Умная система начисления опыта, сезонные ранги, 100 уникальных IT-званий и система достижений ("Первая кровь" и др.).
* 📊 **Профиль:** Личный кабинет (`/profile`) с графическим прогресс-баром и статистикой.
* ⏰ **Фоновые задачи (APScheduler):** Автоматическая смена сезонов и рассылка отчетов прямо в чат.
* 🌤 **Ежедневные сводки:**
  * `/start_weather` — детальная погода, прогноз, фазы луны и магнитные бури.
  * `/start_currency` — курсы фиатных валют с динамикой роста/падения.
  * `/start_crypto` — курсы основных криптовалют.

## 🛠 Стек технологий
* **Python 3.10+**
* **Фреймворк:** [Aiogram 3.x](https://docs.aiogram.dev/en/latest/)
* **База данных:** SQLite + [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) (Асинхронная)
* **Планировщик:** [APScheduler](https://apscheduler.readthedocs.io/)
* **Тестирование:** `pytest`, `pytest-asyncio` (In-memory БД)
* **Логирование:** Встроенный RotatingFileHandler (сохранение в `logs/`)

---

## 🚀 Инструкция по локальному запуску

### 1. Подготовка окружения
Склонируйте репозиторий, перейдите в папку с ботом и создайте виртуальное окружение:

```bash
# Для Windows
python -m venv venv
venv\Scripts\activate

# Для Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей
Установите необходимые библиотеки:

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
В корневой папке проекта создайте файл `.env` и добавьте туда ваши токены:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
OPENWEATHER_TOKEN=ваш_ключ_от_OpenWeatherMap
```

### 4. Инициализация базы данных и уровней
Перед первым запуском необходимо загрузить в базу данных иерархию уровней (титулов) и пороги опыта. 
Для этого в проекте предусмотрена встроенная консольная команда. Выполните:

```bash
python main.py --init_levels
```
*Ожидаемый результат: сообщение в консоли об успешном добавлении 100 уровней в БД. Бот автоматически закроется после инициализации.*

### 5. Запуск бота
```bash
python main.py
```
В консоли должно появиться сообщение `🤖 Бот запущен и готов к работе!`, после чего можно переходить в Telegram.

---

## 🧪 Тестирование

Проект покрыт автоматизированными тестами для проверки основной бизнес-логики (работа с БД, выезды, геймификация, ротация сезонов). Тесты выполняются в изолированной `in-memory` базе данных, поэтому не затрагивают и не портят основную рабочую БД.

Для запуска тестов выполните команду в корне проекта:

```bash
pytest -v
```

---

## 📂 Структура проекта

```plaintext
Cat_Time_Bot_Z/
├── venv/                   # Виртуальное окружение
└── cat_bot/                # Основная директория бота
    ├── core/               # Настройки БД, модели (models.py), запросы (crud.py), логгер
    ├── handlers/           # Обработчики команд (/profile, /join, /leave)
    ├── services/           # Бизнес-логика (статистика, сезоны, геймификация)
    ├── scripts/            # Утилиты и скрипты (init_level.py)
    ├── tests/              # Автотесты (test_db.py, test_activities.py и др.)
    ├── logs/               # Директория с ротируемыми логами
    ├── pytest.ini          # Конфигурация для Pytest
    ├── main.py             # Точка входа, инициализация бота и диспетчера
    └── .env                # Секретные ключи (не коммитить!)
```

## 📝 Планы дальнейшего развития

- [ ] Перенос базы данных на PostgreSQL для production.
- [ ] Развертывание Web-админки на базе FastAPI.
- [ ] Упаковка проекта в Docker и деплой на сервер.
- [ ] Интеграция антистресс-API с котиками.

## 🎉 Предложения и баги
Вы можете предложить свою идею, сообщить о баге или просто написать автору. Больше технических статей и гайдов можно найти на сайте [riopass.ru](https://riopass.ru).

## 🌟 Спасибо за внимание!