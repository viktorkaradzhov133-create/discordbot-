# Discord бот: модерация, посрещане и музика

## Подготовка
1. Инсталирай Python 3.11+ и FFmpeg (трябва да е в PATH).
2. Изпълни `pip install -r requirements.txt`.
3. Копирай `.env.example` като `.env` и попълни токена и ID на канала.
4. В [Discord Developer Portal](https://discord.com/developers/applications) създай приложение и бот. Активирай **Server Members Intent** и **Message Content Intent**.
5. Покани бота чрез OAuth2 с `bot` и `applications.commands`, с права View Channels, Send Messages, Manage Messages, Connect и Speak.
6. Стартирай с `python bot.py`.

## Команди
- `/play песен` – добавя песен или URL в опашката
- `/skip` – пропуска песента
- `/stop` – спира музиката и изчиства опашката
- `/leave` – напуска гласовия канал

## Филтър
Редактирай `BAD_WORDS` в `bot.py`. Използва съвпадения по цели думи. За по-сложна модерация (вариации, заобикаляне на филтъра) е необходим допълнителен код.

## Забележки
- Никога не качвай `.env` или токена в GitHub.
- GitHub не хоства постоянно работещия бот; използвай отделен хостинг.
- Някои музикални сайтове могат да ограничават извличането на аудио; `yt-dlp` не гарантира работа за всеки URL.
