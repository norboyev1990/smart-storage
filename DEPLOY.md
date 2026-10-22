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
3. Строка подключения:

   ```
   postgresql+psycopg://cpuser_smartuser:ПАРОЛЬ@localhost:5432/cpuser_smart
   ```

   Если в пароле есть символы `@ : / # %`, замените их URL-кодом (`@` → `%40`) или выберите пароль из букв и цифр.

## 3. Загрузка backend

1. Загрузите содержимое папки `backend/` в `~/smart-storage-api/` (через **File Manager** архивом `.zip` и «Extract», или через Git™ Version Control в cPanel). Папки `tests/`, `.venv/` и файл `.env` с вашего компьютера не нужны.
2. cPanel → **Setup Python App** → **Create Application**:
   - Python version: **3.13** (или 3.12)
   - Application root: `smart-storage-api`
   - Application URL: `api.your-domain.uz` (корень, без пути)
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
3. В том же окне в **Environment variables** добавьте:

   | Переменная | Значение |
   |---|---|
   | `DATABASE_URL` | строка из шага 2 |
   | `BOT_TOKEN` | токен от @BotFather |
   | `JWT_SECRET` | случайная строка из 64 символов |
   | `WEBHOOK_SECRET` | ещё одна случайная строка (только латиница и цифры) |
   | `WEBAPP_URL` | `https://your-domain.uz` |
   | `API_URL` | `https://api.your-domain.uz` |
   | `CORS_ORIGINS` | `["https://your-domain.uz"]` (именно с кавычками и скобками) |

   Случайную строку можно получить командой `openssl rand -hex 32` или любым генератором паролей. Не отправляйте эти значения никому, в том числе в чат.
4. Нажмите **Create**, затем внизу в поле «Configuration files» укажите `requirements.txt` и нажмите **Run Pip Install**.

## 4. Миграции и вебхук бота

В **Setup Python App** у приложения есть поле **Execute python script**. Выполните по очереди:

```
manage.py migrate
manage.py set-webhook
```

Должно появиться `Migrations applied` и `Webhook set: https://api.your-domain.uz/telegram/webhook`.

Если в тарифе есть **Terminal** (или SSH), то же самое можно сделать там. Команду активации окружения cPanel показывает вверху страницы приложения:

```bash
source /home/cpuser/virtualenv/smart-storage-api/3.13/bin/activate && cd ~/smart-storage-api
python manage.py migrate
python manage.py set-webhook
```

Нажмите **Restart** у приложения и откройте `https://api.your-domain.uz/health`. Ответ `{"status":"ok"}` значит, что backend работает. Документация API: `https://api.your-domain.uz/docs`.

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

## Обновление

- Backend: загрузите изменённые файлы, при изменении `requirements.txt` снова **Run Pip Install**, при новых миграциях `manage.py migrate`, затем **Restart**.
- Frontend: снова соберите и замените файлы в `public_html/`.

## Резервные копии

cPanel → **Backup** позволяет скачать дамп PostgreSQL. Делайте это регулярно, или настройте **Cron Jobs**:

```
0 3 * * * pg_dump "postgresql://cpuser_smartuser:ПАРОЛЬ@localhost/cpuser_smart" | gzip > ~/backups/smart-$(date +\%F).sql.gz
```

(папку `~/backups` создайте заранее, она не должна быть внутри `public_html`).

## Если что-то не работает

- **Ошибка 500 или «Web application could not be started»**: откройте `~/smart-storage-api/stderr.log` (или лог Passenger), там будет причина. Частые причины: не выполнен Pip Install, неверный `DATABASE_URL`, `CORS_ORIGINS` не в формате JSON.
- **Бот не отвечает на /start**: проверьте `https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo` в браузере. В поле `last_error_message` будет причина. После смены `WEBHOOK_SECRET` или домена выполните `manage.py set-webhook` ещё раз.
- **Mini App открывается, но вход не работает**: проверьте, что `CORS_ORIGINS` совпадает с адресом фронтенда, а фронтенд собран с правильным `VITE_API_URL`.
- **Хостинг не даёт исходящие запросы к api.telegram.org**: напишите в поддержку ahost, чтобы открыли доступ, иначе бот не сможет отвечать.

## Локальная разработка

Ничего не меняется: `python -m app.bot` по-прежнему запускает бота в режиме polling (он сам снимает вебхук). После локального запуска на рабочем токене снова выполните `manage.py set-webhook` на сервере.
