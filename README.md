# 🐾 Cat Time Bot Z (FastAPI Edition)

![Лицензия](https://img.shields.io/github/license/1517mb/Cat_Time_Bot_Z)
[![Python Tests](https://github.com/1517mb/Cat_Time_Bot_Z/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/1517mb/Cat_Time_Bot_Z/actions/workflows/tests.yml)
<a href="[https://www.python.org/](https://www.python.org/)" style="text-decoration: none;"><img src="[https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python&logoColor=ffdd54](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python&logoColor=ffdd54)" height="20" alt="python"></a>
<a href="[https://docs.aiogram.dev/](https://docs.aiogram.dev/)" style="text-decoration: none;"><img src="[https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white)" height="20" alt="aiogram"></a>
<a href="[https://docs.sqlalchemy.org/](https://docs.sqlalchemy.org/)" style="text-decoration: none;"><img src="[https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=database&logoColor=white](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=database&logoColor=white)" height="20" alt="sqlalchemy"></a>
<br>
<a href="[https://github.com/1517mb/Cat_Time_Bot_Z/commits](https://github.com/1517mb/Cat_Time_Bot_Z/commits)" style="text-decoration: none;"><img src="[https://img.shields.io/github/commit-activity/w/1517mb/Cat_Time_Bot_Z](https://img.shields.io/github/commit-activity/w/1517mb/Cat_Time_Bot_Z)" height="20" alt="commit-activity"></a>
<a href="[https://github.com/1517mb/Cat_Time_Bot_Z/commits](https://github.com/1517mb/Cat_Time_Bot_Z/commits)" style="text-decoration: none;"><img src="[https://img.shields.io/github/last-commit/1517mb/Cat_Time_Bot_Z](https://img.shields.io/github/last-commit/1517mb/Cat_Time_Bot_Z)" height="20" alt="last-commit"></a>
<a href="[https://github.com/1517mb/Cat_Time_Bot_Z/issues](https://github.com/1517mb/Cat_Time_Bot_Z/issues)" style="text-decoration: none;"><img src="[https://img.shields.io/github/issues/1517mb/Cat_Time_Bot_Z](https://img.shields.io/github/issues/1517mb/Cat_Time_Bot_Z)" height="20" alt="issues"></a>
<br>
<img src="[https://img.shields.io/github/repo-size/1517mb/Cat_Time_Bot_Z](https://img.shields.io/github/repo-size/1517mb/Cat_Time_Bot_Z)" height="20" alt="repo-size">
<img src="[https://img.shields.io/github/languages/code-size/1517mb/Cat_Time_Bot_Z](https://img.shields.io/github/languages/code-size/1517mb/Cat_Time_Bot_Z)" height="20" alt="code-size">

Асинхронный Telegram-бот на базе **Aiogram 3** и **SQLAlchemy** для геймифицированного учета рабочего времени и выездов IT-специалистов. Бот не только считает отработанные часы, но и награждает пользователей достижениями, повышает уровни (от "Укротителя USB" до "Архитектора Систем") и рассылает ежедневные сводки (погода, валюты ЦБ РФ, крипта).

## ✨ Ключевые возможности
* ⏱ **Трекинг времени:** Команды `/join` и `/leave` для фиксации прибытия и ухода с точек. Редактирование времени через `/edit_start` и `/edit_end`.
* 🎮 **Геймификация:** Умная система начисления опыта, сезонные ранги, 100 уникальных IT-званий и система достижений ("Первая кровь" и др.).
* 📊 **Профиль:** Личный кабинет (`/profile`) с графическим прогресс-баром и статистикой.
* ⏰ **Фоновые задачи и рассылки (APScheduler):**
  * `/start_reminder ЧЧ:ММ` — умное напоминание о транспортных расходах (динамически считает дни до конца месяца).
  * `/start_leave_reminder ЧЧ:ММ` — напоминание сотрудникам о незакрытых выездах (чтобы никто не забыл нажать `/leave`).
  * `/start_stats ЧЧ:ММ` — автоматическая отправка ежедневного отчета по выездам.
  * `/start_news ЧЧ:ММ` — ежедневный IT-дайджест и кот-антистресс.
  * **Отключение:** используйте приставку `stop_` вместо `start_` для точечной отмены (например, `/stop_weather`).
  * `/stop_scheduler` — полная отмена **всех** активных рассылок и напоминаний в текущем чате.
* 🌤 **Ежедневные сводки:**
  * `/start_weather ЧЧ:ММ` — детальная погода, прогноз, фазы луны и магнитные бури.
  * `/start_currency ЧЧ:ММ` — курсы фиатных валют с динамикой роста/падения.
  * `/start_crypto ЧЧ:ММ` — курсы основных криптовалют.

## 🛠 Стек технологий
* **Python 3.10+**
* **Фреймворк:** [Aiogram 3.x](https://docs.aiogram.dev/en/latest/)
* **База данных:** SQLite + [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) (Асинхронная)
* **Планировщик:** [APScheduler](https://apscheduler.readthedocs.io/)
* **Тестирование:** `pytest`, `pytest-asyncio` (In-memory БД)
* **Логирование:** Встроенный RotatingFileHandler (сохранение в `logs/`)

---

## 🐳 Запуск через Docker (Рекомендуется)

Это самый быстрый способ развернуть бота со всеми зависимостями и правильным часовым поясом.

### 1. Подготовка
Создайте в папке бота пустой файл базы данных (чтобы Docker не создал вместо него директорию):
```bash
touch cat_bot/sqlite.db
```

### 2. Запуск
*(Если вы используете Linux/WSL и получаете ошибку прав доступа к сокету Docker, используйте команду с `sudo`)*:
```bash
sudo docker compose up -d --build
```

### 3. Первоначальная настройка (для новых пользователей)
Если вы запускаете бота впервые, наполните базу уровнями:
```bash
sudo docker compose exec cat_bot python main.py --init_levels
```

### 4. Миграция данных из архивного проекта
Если вы переходите с архивной версии [cat_time_bot (Django)](https://github.com/1517mb/cat_time_bot):
1. Положите файл вашей старой базы в папку `cat_bot/` под именем `old_bot_database.db`.
2. Выполните команду миграции внутри работающего контейнера:
```bash
sudo docker compose exec cat_bot python main.py --migrate_db
```
*(Если возникает ошибка доступа к `sqlite.db`, выполните на хосте: `sudo chmod 666 cat_bot/sqlite.db`)*

---

## 🚀 Локальный запуск (без Docker)

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
CHAT_ID=id_вашего_чата_для_рассылок
```

### 4. Инициализация базы данных и уровней
Перед первым запуском необходимо загрузить в базу данных иерархию уровней (титулов). Перейдите в папку `cat_bot` и выполните:
```bash
cd cat_bot
python main.py --init_levels
```

### 5. Миграция данных (из архивного проекта)
Если вы переходите с архивной версии бота [cat_time_bot](https://github.com/1517mb/cat_time_bot) (Django), которая больше не поддерживается, вы можете перенести свои данные локально:
1. Поместите файл вашей старой базы данных в папку `cat_bot/` под именем `old_bot_database.db`.
2. Запустите команду миграции:
```bash
python main.py --migrate_db
```
*Скрипт автоматически создаст таблицы в новой базе и адаптирует данные из таблиц Django (bot_*) под новую структуру SQLAlchemy.*

### 6. Запуск бота
```bash
python main.py
```

---

## 🧪 Тестирование

Проект покрыт автоматизированными тестами с использованием параметризации. Тесты выполняются в изолированной `in-memory` базе данных, имеется настроенный CI/CD пайплайн (GitHub Actions). 
Для запуска тестов локально выполните команду в корне проекта:

```bash
pytest -v
```

---

## 📂 Структура проекта

```plaintext
Cat_Time_Bot_Z/
├── cat_bot/                # Основная директория бота и данные
│   ├── core/               # Настройки БД, модели (models.py), запросы (crud.py), логгер
│   ├── handlers/           # Обработчики команд (/profile, /join, /leave, рассылки)
│   ├── services/           # Бизнес-логика (статистика, сезоны, геймификация)
│   ├── scripts/            # Утилиты (init_level.py, migrate_db.py)
│   ├── tests/              # Автотесты (test_db.py, test_tasks.py, test_scheduling.py и др.)
│   ├── logs/               # Директория с ротируемыми логами
│   ├── sqlite.db           # Основная база данных
│   ├── old_bot_database.db # Архивный дамп для миграции (опционально)
│   └── main.py             # Точка входа, инициализация CLI и бота
├── venv/                   # Виртуальное окружение
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile              # Инструкция для сборки Docker-образа
├── .dockerignore           # Исключения для Docker
├── pytest.ini              # Конфигурация для Pytest
├── requirements.txt        # Зависимости Python
└── .env                    # Секретные ключи (не коммитить!)
```

## 📝 Планы дальнейшего развития

- [ ] Перенос базы данных на PostgreSQL для production.
- [ ] Развертывание Web-админки на базе FastAPI.
- [x] Упаковка проекта в Docker и деплой на сервер.
- [x] Интеграция антистресс-API с котиками.
- [x] Покрытие ключевого функционала автотестами и настройка CI.

## 🎉 Предложения и баги
Вы можете предложить свою идею, сообщить о баге или просто написать автору. Больше технических статей и гайдов можно найти на сайте [riopass.ru](https://riopass.ru).

## 🌟 Спасибо за внимание!