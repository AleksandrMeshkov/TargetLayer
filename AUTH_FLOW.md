# Схема авторизации и работа с JWT (описание на русском)

Цель: кратко описать логику регистрации, аутентификации и обновления токенов (access/refresh) в проекте.

1) Компоненты и таблицы
- `auth_identities` — хранит email и хеш пароля.
- `users` — профиль пользователя (имя, фамилия, `created_at`, `updated_at`, avatar и т.д.).
- `chat_messages` — служебная запись создаётся при регистрации (как требование доменной модели).
- `user_activity` — связывает записи из трёх таблиц: `auth_identities`, `users`, `chat_messages`. Создаётся сразу при регистрации и содержит FK на все три таблицы.

При регистрации сервис создаёт по одной записи в каждой из трёх таблиц и затем создаёт запись в `user_activity`, которая агрегирует эти связи.

2) Токены
- Access token: короткоживущий токен (в минутах), тип payload: `{sub: <user_activity_id>, exp: <...>, type: "access"}`. Используется для авторизации API-запросов (Bearer header).
- Refresh token: долгоживущий токен (в часах), тип payload: `{sub: <user_activity_id>, exp: <...>, type: "refresh"}`. Хранится в HttpOnly cookie и используется для получения нового access token без повторной авторизации пользователя.

3) Endpoints (реализованы в `app/api/v1/auth/auth.py`)
- `POST /auth/register` — принимает JSON `UserRegister`, создаёт `AuthIdentity`, `User`, `ChatMessage` и `UserActivity`; возвращает `access_token` в теле; `refresh_token` устанавливается в HttpOnly cookie.
- `POST /auth/login` — принимает `email` и `password`; при успешной аутентификации возвращает `access_token` в теле и устанавливает `refresh_token` в HttpOnly cookie.
- `POST /auth/refresh` — читает `refresh_token` из cookie, проверяет его и при успешной проверке обновляет (ротация) refresh в cookie и возвращает новый access в теле.

4) Cookie и безопасность
- `refresh_token` устанавливается с опциями: `HttpOnly`, `SameSite=Lax`, `max_age` = `REFRESH_TOKEN_EXPIRE_HOURS * 3600`.
- Access токен не хранится в cookie сервером — он возвращается в теле и клиент кладёт его в `Authorization: Bearer <access>` при запросах.
- Рекомендуется хранить access на клиенте в памяти или в безопасном месте (не в localStorage без продуманной политики).

5) Пример использования (curl)

Регистрация:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ivan","email":"ivan@example.com","password":"secret","name":"Иван","surname":"Иванов"}' \
  -i
```
Ответ: тело содержит `access_token`, а в заголовках будет `Set-Cookie: refresh_token=...; HttpOnly; Max-Age=...`.

Логин:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=ivan@example.com&password=secret" \
  -i
```

Обновление токена (refresh) — пример клиентской логики: браузер автоматически пришлёт cookie при запросе к тому же origin.
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -c cookies.txt -b cookies.txt -i
```

Выход (logout) — серверная реализация может просто стереть cookie:
```python
# Пример: в обработчике
response.delete_cookie("refresh_token")
```

6) Защита роутов с помощью access token
- Все приватные endpoint'ы должны требовать `Authorization: Bearer <access_token>` и проверять `type == 'access'` в payload.
- Если access истёк — клиент вызывает `/auth/refresh` (cookie отправляется автоматически) и получает новый access.

7) Поведение `created_at` / `updated_at`
- Поля `created_at` и `updated_at` в `users` определены с дефолтными значениями в модели. При регистрации обе записи должны иметь `created_at` и `updated_at` (по умолчанию — текущее время).
- При обновлении профиля (включая будущий endpoint с фотографией) обязательно обновлять поле `updated_at` (ORM поле `onupdate=datetime.utcnow` уже настроено в модели `User`).

8) Дополнительные рекомендации
- Храните секрет ключа (`SECRET_KEY`) надёжно и не в репозитории.
- Рассмотрите стратегию ротации refresh токенов и возможность отката (revocation list) при компрометации.
- Для production: включите `Secure` флаг у cookie (только HTTPS) и настройте `SameSite` более строго при необходимости.

9) Короткая проверка работоспособности
- Запустите приложение и выполните последовательность: регистрация → проверка cookie → доступ к защищённому ресурсу с access → дождитесь истечения access → вызов `/auth/refresh` → проверьте, что access обновился.

Файлы реализации: [app/services/auth_service.py](app/services/auth_service.py), [app/api/v1/auth/auth.py](app/api/v1/auth/auth.py), [app/core/security/jwt.py](app/core/security/jwt.py), [app/core/security/password.py](app/core/security/password.py)
