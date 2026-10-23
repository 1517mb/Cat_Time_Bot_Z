# 🐾 Cat Time Bot Z

[![Лицензия](https://img.shields.io/github/license/1517mb/Cat_Time_Bot_Z)](https://github.com/1517mb/Cat_Time_Bot_Z)
[![Python Tests](https://github.com/1517mb/Cat_Time_Bot_Z/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/1517mb/Cat_Time_Bot_Z/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.10%E2%80%933.14-blue?style=flat&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat&logo=database&logoColor=white)](https://docs.sqlalchemy.org/)
<br>
[![Commit Activity](https://img.shields.io/github/commit-activity/w/1517mb/Cat_Time_Bot_Z)](https://github.com/1517mb/Cat_Time_Bot_Z/commits)
[![Last Commit](https://img.shields.io/github/last-commit/1517mb/Cat_Time_Bot_Z)](https://github.com/1517mb/Cat_Time_Bot_Z/commits)
[![Issues](https://img.shields.io/github/issues/1517mb/Cat_Time_Bot_Z)](https://github.com/1517mb/Cat_Time_Bot_Z/issues)
<br>
![Repo Size](https://img.shields.io/github/repo-size/1517mb/Cat_Time_Bot_Z)
![Code Size](https://img.shields.io/github/languages/code-size/1517mb/Cat_Time_Bot_Z)

Асинхронный Telegram-бот на базе **Aiogram 3** и **SQLAlchemy** для учета рабочего времени и выездов IT-специалистов. Бот начисляет опыт, выдает достижения и сезонные звания, отправляет ежедневные сводки с погодой, курсами валют и IT-новостями. Запускается через Telegram polling; веб-админка на FastAPI входит в планы развития.

## ✨ Возможности

- **Учет времени:** `/join` и `/leave` фиксируют прибытие и уход; `/edit_start` и `/edit_end` позволяют исправить время.
- **Геймификация:** опыт за выезды, сезонные ранги, 100 IT-званий и достижения.
- **Профиль:** `/profile` показывает статистику и прогресс до следующего уровня.
- **Новости и котики:** ежедневный IT-дайджест и кот-антистресс; `/mew` отправляет случайного кота.

Рассылки и напоминания настраиваются командами. Время указывается в формате `ЧЧ:ММ`, часовой пояс — `Europe/Moscow`.

| Команда | Рассылка |
| --- | --- |
| `/start_reminder ЧЧ:ММ` | Напоминание о транспортных расходах с учетом дней до конца месяца |
| `/start_leave_reminder ЧЧ:ММ` | Напоминание о незакрытых выездах |
| `/start_stats ЧЧ:ММ` | Ежедневный отчет по выездам |
| `/start_news ЧЧ:ММ` | IT-дайджест и котик |
| `/start_weather ЧЧ:ММ` | Погода, прогноз, фазы луны и магнитные бури |
| `/start_currency ЧЧ:ММ` | Курсы валют и их изменение |
| `/start_crypto ЧЧ:ММ` | Курсы основных криптовалют |

Для отключения одной рассылки замените `start_` на `stop_`, например `/stop_weather`. Команда `/stop_scheduler` отключает все активные рассылки и напоминания в текущем чате.

## 🛠 Стек технологий

- **Python 3.10–3.14**, Docker-образ на Python 3.14.
- **Aiogram 3** — обработка команд Telegram.
- **SQLite + SQLAlchemy 2.0 + aiosqlite** — асинхронная работа с базой данных.
- **APScheduler** — фоновые задачи и рассылки.
- **pytest и pytest-asyncio** — тестирование.
- **logging** — консоль и ротируемые журналы в `cat_bot/logs/`.

## ⚙️ Подготовка и настройка

Склонируйте репозиторий и перейдите в его корень:

```bash
git clone https://github.com/1517mb/Cat_Time_Bot_Z.git
cd Cat_Time_Bot_Z
```

Настройка `.env` нужна и для Docker, и для локального запуска. Создайте файл из [.env.example](.env.example).

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Заполните значения в `.env`:

| Переменная | Значение |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Токен бота от BotFather |
| `OPENWEATHER_API_KEY` | API-ключ OpenWeather для погодной сводки |
| `CHAT_ID` | Числовой ID чата для стандартных рассылок; у групп обычно отрицательный |

Добавьте бота в указанный чат и разрешите ему отправлять сообщения. Файл `.env` содержит секреты и исключен из Git.

При первом развертывании выберите один из двух путей: новая база с начальными уровнями или [перенос данных из Django-версии](#перенос-данных-из-django-версии).

## 🐳 Запуск через Docker

Команды выполняются из корня проекта. Требуются Docker и Docker Compose.

### Новая установка

Compose подключает два файла БД с хоста: `sqlite.db` и `old_bot_database.db`. Для новой установки создайте их пустыми до первого запуска контейнера, чтобы Docker не создал каталоги вместо файлов. Следующие команды сохраняют уже существующие файлы.

Windows PowerShell:

```powershell
foreach ($databasePath in 'cat_bot/sqlite.db', 'cat_bot/old_bot_database.db') {
    if (-not (Test-Path -LiteralPath $databasePath)) {
        New-Item -ItemType File -Path $databasePath | Out-Null
    }
}
```

Linux/macOS:

```bash
touch cat_bot/sqlite.db cat_bot/old_bot_database.db
```

Соберите образ, создайте таблицы и начальные уровни, затем запустите бота:

```bash
docker compose build
docker compose run --rm cat_bot python main.py --init_levels
docker compose up -d
```

Файлы БД и журналы сохраняются на хосте через volumes. Для обновления после изменения кода или зависимостей:

```bash
docker compose up -d --build
```

## 🚀 Локальный запуск

Из корня проекта создайте виртуальное окружение и активируйте его.

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Установите зависимости бота:

```bash
python -m pip install -r requirements.txt
```

Для новой установки перейдите в `cat_bot`, создайте таблицы и начальные уровни, затем запустите бота:

```bash
cd cat_bot
python main.py --init_levels
python main.py
```

При следующих запусках достаточно `python main.py` из `cat_bot/`. Для переноса существующих данных используйте инструкцию ниже вместо `--init_levels`.

## Перенос данных из Django-версии

Скрипт переносит данные из архивного проекта [cat_time_bot](https://github.com/1517mb/cat_time_bot) в новую SQLite-базу. Выполняйте перенос до первого запуска бота, в пустую целевую базу, без предварительного `--init_levels`: старые уровни переносятся вместе с остальными данными и сохраняют свои ID.

Поместите копию старой БД в `cat_bot/old_bot_database.db`. Сохраните исходную БД отдельно, чтобы можно было повторить перенос.

### Docker

Настройте `.env` и создайте пустой файл `cat_bot/sqlite.db`, как описано выше. На месте `cat_bot/old_bot_database.db` должна находиться копия старой БД. Из корня проекта выполните:

```bash
docker compose build
docker compose run --rm cat_bot python main.py --migrate_db
docker compose up -d
```

### Локально

Подготовьте окружение и установите зависимости по инструкции локального запуска. Из `cat_bot/` выполните:

```bash
python main.py --migrate_db
python main.py
```

Скрипт создает целевые таблицы и переносит данные из таблиц Django `bot_*`. Перед запуском бота проверьте журнал миграции на ошибки переноса и пропущенные таблицы.

## 📝 Логирование

Бот пишет сообщения в консоль и в файлы с путями, независимыми от текущей рабочей папки:

- `cat_bot/logs/cat_bot.log` — общий журнал, начиная с `INFO`.
- `cat_bot/logs/cat_bot_errors.log` — только `ERROR` и `CRITICAL`, включая traceback неожиданных исключений.

Каждый файл ротируется при достижении 5 МБ; сохраняются пять архивов. В Docker эта папка подключена через volume. Просмотр вывода контейнера:

```bash
docker compose logs --tail=100 cat_bot
```

Просмотр файла ошибок в Windows PowerShell:

```powershell
Get-Content cat_bot/logs/cat_bot_errors.log -Tail 100
```

Linux/macOS:

```bash
tail -n 100 cat_bot/logs/cat_bot_errors.log
```

Запись содержит модуль, функцию, строку кода и доступный контекст: `update_id`, `chat_id`, `user_id`, `job_id`, задачу, источник данных и операцию. Сетевые сбои и обработанные ошибки Telegram записываются как `WARNING` с типом ошибки; неожиданные исключения — с traceback. Необработанные ошибки команд и заданий планировщика записываются один раз.

При запуске через `main.py` настройки из `.env` загружаются до настройки логирования. Токен Telegram и ключ OpenWeather маскируются в сообщениях и traceback, в том числе в URL. Содержимое сообщений пользователей специально не добавляется в журналы; идентификаторы используются для поиска связанных записей.

## 🧪 Разработка и тестирование

Из корня проекта в активированном виртуальном окружении установите зависимости разработки и запустите тесты:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
python -m pip check
```

`requirements-dev.txt` включает зависимости бота и инструменты тестирования. Тесты БД используют изолированную `in-memory` SQLite-базу. GitHub Actions выполняет CI: установку зависимостей, проверку их согласованности и тесты на Python 3.10 и 3.14.

### Управление зависимостями

| Файл | Назначение |
| --- | --- |
| `requirements.in` | Прямые зависимости бота |
| `requirements-dev.in` | Дополнительные зависимости разработки |
| `requirements.txt` | Сгенерированное дерево зависимостей бота с закрепленными версиями |
| `requirements-dev.txt` | Сгенерированное дерево зависимостей разработки с закрепленными версиями |

Изменяйте прямые зависимости в `.in`, затем пересоздавайте соответствующие `.txt`. Сгенерированные файлы хранятся в репозитории и используются при установке, в CI и Docker.

Для генерации используется [uv](https://docs.astral.sh/uv/pip/compile/) версии `0.10.9`. Выполняйте команды из корня проекта в активированном окружении:

```bash
python -m pip install uv==0.10.9
uv pip compile requirements.in --universal --python-version 3.10 --no-python-downloads --output-file requirements.txt
uv pip compile requirements-dev.in --universal --python-version 3.10 --no-python-downloads --constraint requirements.txt --output-file requirements-dev.txt
```

`--universal` сохраняет условные зависимости для разных версий Python и платформ. Файл разработки компилируется с ограничениями из `requirements.txt`, чтобы версии общих пакетов совпадали. После изменения зависимостей выполните установку и проверки из раздела выше; обновленные `.in` и `.txt` сохраняйте вместе.

## 📂 Структура проекта

```text
Cat_Time_Bot_Z/
├── cat_bot/
│   ├── core/                 # БД, модели, запросы, логирование
│   ├── handlers/             # Обработчики команд
│   ├── middlewares/          # Сессии БД и контекст логирования
│   ├── services/             # Статистика, сезоны, рассылки
│   ├── scripts/              # Инициализация уровней и перенос данных
│   ├── tests/                # Автотесты
│   ├── logs/                 # Журналы, создаются при запуске
│   ├── sqlite.db             # Рабочая БД, создается при инициализации
│   ├── old_bot_database.db   # Копия старой БД для переноса
│   └── main.py               # Точка входа бота и CLI
├── .github/workflows/        # CI на GitHub Actions
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.in
├── requirements.txt
├── requirements-dev.in
├── requirements-dev.txt
├── .env.example              # Шаблон настроек без секретов
└── .env                      # Локальные настройки, исключены из Git
```

## 📝 Планы развития

- [ ] Перенос базы данных на PostgreSQL.
- [ ] Веб-админка на базе FastAPI.
- [x] Упаковка проекта в Docker и развертывание на сервере.
- [x] Интеграция API с котиками.
- [x] Автотесты ключевого функционала и CI.

## Предложения и ошибки

Предложить идею или сообщить об ошибке можно в [Issues](https://github.com/1517mb/Cat_Time_Bot_Z/issues). Технические статьи и инструкции автора — на [riopass.ru](https://riopass.ru).
