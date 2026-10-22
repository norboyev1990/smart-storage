# Деплой на хостинг с cPanel (ahost.uz)

Схема на одном аккаунте cPanel:

- `your-domain.uz`: фронтенд (собранные статические файлы в `public_html`)
- `api.your-domain.uz`: backend (FastAPI через «Setup Python App», Phusion Passenger)
- PostgreSQL: база в cPanel
- Бот работает через вебхук внутри backend, отдельный процесс не нужен

Ниже `your-domain.uz` замените на свой домен.

## 1. Домен и SSL

1. В cPanel → **Domains** создайте поддомен `api.your-domain.uz` (корневая папка, например, `api.your-domain.uz`, не внутри `public_html`).
2. В cPanel → **SSL/TLS Status** нажмите **Run AutoSSL**, чтобы сертификаты выпустились для `your-domain.uz` и `api.your-domain.uz`. Telegram Mini App и вебхук работают только по HTTPS.

## 2. База PostgreSQL

1. cPanel → **PostgreSQL Databases**: создайте базу (например, `smart`) и пользователя с длинным паролем, добавьте пользователя в базу со всеми правами.
2. cPanel добавляет к именам префикс аккаунта, например `cpuser_smart`. Запишите полные имена.
3. Строка подключения. На cPanel PostgreSQL обычно не принимает подключения по TCP (`localhost`/`127.0.0.1`), только через unix-сокет, поэтому хост указывается параметром `host=` с путём к папке сокета:

   ```
   postgresql+psycopg://cpuser_smartuser:ПАРОЛЬ@/cpuser_smart?host=/var/run/postgresql
   ```

   Где лежит сокет, можно проверить по SSH: `ls /var/run/postgresql/.s.PGSQL.5432 /tmp/.s.PGSQL.5432`. Если файл есть только в `/tmp`, укажите `host=/tmp`. Проверить логин и пароль: `psql -h /var/run/postgresql -U cpuser_smartuser cpuser_smart`.

   Если в пароле есть символы `@ : / # % ?`, замените их URL-кодом (`@` → `%40`) или выберите пароль из букв и цифр.

## 3. Загрузка backend (FastAPI)

1. Загрузите содержимое папки `backend/` в `~/smart-storage-api/` (архивом через **File Manager** или `rsync`/`scp` по SSH). Папки `tests/`, `.venv/` и файл `.env` с вашего компьютера не нужны. Дальше обновления будет загружать GitHub Actions.
2. cPanel → **Setup Python App** → **Create Application**:
   - Python version: **3.13** (или 3.12)
   - Application root: `smart-storage-api`
   - Application URL: `api.your-domain.uz` (корень, без пути)
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
3. Нажмите **Create**. Вверху страницы приложения cPanel покажет команду активации окружения вида
   `source /home/cpuser/virtualenv/smart-storage-api/3.13/bin/activate && cd /home/cpuser/smart-storage-api`. Запишите путь до `activate`, он понадобится для GitHub Actions.
4. Создайте в `~/smart-storage-api/` файл `.env` (через File Manager или по SSH) и сделайте его доступным только вам (`chmod 600 .env`):

   ```
   DATABASE_URL=строка из шага 2
   BOT_TOKEN=токен от @BotFather
   JWT_SECRET=случайная строка из 64 символов
   WEBHOOK_SECRET=ещё одна случайная строка (только латиница и цифры)
   WEBAPP_URL=https://your-domain.uz
   API_URL=https://api.your-domain.uz
   CORS_ORIGINS=["https://your-domain.uz"]
   ```

   Случайную строку можно получить командой `openssl rand -hex 32`. Файл `.env` читают и сайт, и команды по SSH, поэтому переменные лучше хранить в нём, а не в «Environment variables» cPanel (их не видно из SSH). Не отправляйте эти значения никому, в том числе в чат. Деплой из GitHub этот файл не трогает.

## 4. Запуск backend (FastAPI): зависимости, миграции и вебхук бота

Uvicorn на хостинге не нужен: FastAPI запускает Passenger через `passenger_wsgi.py` (адаптер `a2wsgi`), сам при первом запросе и после `touch tmp/restart.txt`. Команды ниже ставят зависимости FastAPI, создают таблицы в PostgreSQL и подключают бота.

Зайдите по SSH (или в **Terminal** cPanel) и выполните, подставив свою команду активации:

```bash
source /home/cpuser/virtualenv/smart-storage-api/3.13/bin/activate && cd ~/smart-storage-api
pip install -r requirements.txt
python manage.py migrate
python manage.py set-webhook
mkdir -p tmp && touch tmp/restart.txt   # перезапуск приложения
```

Должно появиться `Migrations applied` и `Webhook set: https://api.your-domain.uz/telegram/webhook`. Откройте `https://api.your-domain.uz/health`: ответ `{"status":"ok"}` значит, что backend работает. Документация API: `https://api.your-domain.uz/docs`.

## 5. Фронтенд

На своём компьютере:

```bash
cd frontend
npm ci
VITE_API_URL=https://api.your-domain.uz npm run build
```

В Windows (PowerShell): `$env:VITE_API_URL="https://api.your-domain.uz"; npm run build`.

Загрузите **содержимое** папки `frontend/dist/` в `public_html/` (сам `index.html` должен лежать прямо в `public_html`). Приложение использует HashRouter, поэтому настраивать `.htaccess` для маршрутов не нужно.

## 6. Telegram

1. @BotFather → ваш бот → **Bot Settings → Menu Button**: укажите `https://your-domain.uz`.
2. Отправьте боту `/start`. Должна появиться кнопка «Открыть Smart Storage».

## Автоматический деплой через GitHub Actions

После первой ручной настройки (шаги 1–6) обновления выкладываются сами: файл `.github/workflows/deploy.yml` на каждый пуш в `main` запускает тесты, собирает фронтенд, загружает файлы по SSH, ставит зависимости, применяет миграции и перезапускает приложение. На pull request запускаются только тесты.

### Ключ для GitHub

На своём компьютере создайте отдельный ключ только для деплоя (без пароля):

```bash
ssh-keygen -t ed25519 -f ahost_deploy -N "" -C github-actions
```

1. cPanel → **SSH Access → Manage SSH Keys → Import Key**: вставьте содержимое `ahost_deploy.pub`, затем нажмите **Manage → Authorize**.
2. Узнайте отпечаток сервера: `ssh-keyscan -p ПОРТ ваш-сервер.ahost.uz` (порт и адрес SSH указаны в cPanel или в письме от ahost).

### Настройки репозитория

GitHub → репозиторий → **Settings → Environments → New environment** с именем `production`. В нём добавьте:

**Secrets** (секретные):

| Имя | Значение |
|---|---|
| `SSH_HOST` | адрес SSH сервера |
| `SSH_PORT` | порт SSH (если не 22) |
| `SSH_USER` | логин cPanel |
| `SSH_PRIVATE_KEY` | всё содержимое файла `ahost_deploy` (приватный ключ) |
| `SSH_KNOWN_HOSTS` | вывод `ssh-keyscan` |

**Variables** (обычные):

| Имя | Значение |
|---|---|
| `API_URL` | `https://api.your-domain.uz` |
| `VENV_ACTIVATE` | путь до `activate`, например `/home/cpuser/virtualenv/smart-storage-api/3.13/bin/activate` |
| `APP_DIR` | папка backend, если не `smart-storage-api` |
| `WEB_DIR` | папка фронтенда, если не `public_html` |

После этого любой пуш в `main` (или кнопка **Actions → Test and deploy → Run workflow**) выкладывает новую версию. Если тесты не прошли, деплой не запускается. Ход и ошибки видны во вкладке **Actions**. После деплоя workflow сам проверяет `API_URL/health`.

Приватный ключ после добавления в GitHub с компьютера можно удалить. Если он утёк, удалите ключ в cPanel → SSH Access и создайте новый.

## Ручное обновление (без GitHub Actions)

- Backend: загрузите изменённые файлы и повторите команды из шага 4 (кроме `set-webhook`).
- Frontend: снова соберите и замените файлы в `public_html/`.

## Резервные копии

cPanel → **Backup** позволяет скачать дамп PostgreSQL. Делайте это регулярно, или настройте **Cron Jobs**:

```
0 3 * * * pg_dump "postgresql://cpuser_smartuser:ПАРОЛЬ@/cpuser_smart?host=/var/run/postgresql" | gzip > ~/backups/smart-$(date +\%F).sql.gz
```

(папку `~/backups` создайте заранее, она не должна быть внутри `public_html`).

## Если что-то не работает

- **`no pg_hba.conf entry for host ...` при миграции**: на cPanel вход разрешён, только если пользователь привязан к базе (правило `samerole`). В **PostgreSQL Databases** в блоке «Add User To Database» выберите пользователя и базу и нажмите **Submit**, затем внизу **Synchronize Grants**. Строку подключения используйте через сокет из шага 2.
- **«We're sorry, but something went wrong» от Passenger**: проверьте, что cPanel не заменил `passenger_wsgi.py` своим шаблоном (он использует `imp`, которого нет в Python 3.12). Правильный файл содержит `from a2wsgi import ASGIMiddleware`. Быстрая проверка: `python -c "import passenger_wsgi"` в окружении приложения.
- **Ошибка 500 или «Web application could not be started»**: откройте `~/smart-storage-api/stderr.log` (или лог Passenger), там будет причина. Частые причины: не выполнен `pip install`, нет файла `.env` или в нём неверный `DATABASE_URL`, `CORS_ORIGINS` не в формате JSON.
- **Бот не отвечает на /start**: проверьте `https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo` в браузере. В поле `last_error_message` будет причина. После смены `WEBHOOK_SECRET` или домена выполните `python manage.py set-webhook` ещё раз.
- **Mini App открывается, но вход не работает**: проверьте, что `CORS_ORIGINS` совпадает с адресом фронтенда, а фронтенд собран с правильным `VITE_API_URL`.
- **Деплой в Actions падает на SSH**: проверьте `SSH_HOST`, `SSH_PORT`, что ключ авторизован в cPanel и что `SSH_KNOWN_HOSTS` получен для того же порта.
- **Хостинг не даёт исходящие запросы к api.telegram.org**: напишите в поддержку ahost, чтобы открыли доступ, иначе бот не сможет отвечать.

## Локальная разработка

Ничего не меняется: `python -m app.bot` по-прежнему запускает бота в режиме polling (он сам снимает вебхук). После локального запуска на рабочем токене снова выполните `python manage.py set-webhook` на сервере. Удобнее завести для разработки отдельного тестового бота.
