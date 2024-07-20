# Приложение Погоды

Добро пожаловать в **Приложение Погоды**! Это веб-приложение позволяет пользователям получать текущие прогнозы погоды для любого города. Оно предоставляет простой и удобный интерфейс, где пользователи могут ввести название города и получить информацию о погоде, такую как температура, погодные условия, влажность и скорость ветра.

## Особенности

- **Текущие данные о погоде:** Получайте актуальные обновления погоды для любого города по всему миру.
- **Удобный интерфейс:** Легкий в использовании веб-интерфейс с четкой и лаконичной информацией о погоде.
- **История поиска:** Просматривайте историю городов, которые были запрашивались.
- **Сохранение данных:** Информация о погоде хранится и управляется эффективно.
- **Тестирование:** Заполните базу данных образцами городов для целей тестирования.

## Используемые технологии

- **Flask:** Легковесный WSGI веб-фреймворк на Python для создания веб-приложения.
- **SQLAlchemy:** Инструмент ORM (Object-Relational Mapping) для управления базой данных.
- **OpenWeatherMap API:** Обеспечивает данные о погоде для приложения.
- **Docker:** Технология контейнеризации для обеспечения согласованности сред разработки и продакшена.

## Как начать

Чтобы начать работу с Приложением Погоды, выполните следующие шаги:

1. **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/Tommy-97/my-weather.git
    ```
2. **Перейдите в каталог проекта:**
    ```bash
    cd my-weather
    ```
3. **Настройте окружение:**
    - Убедитесь, что у вас установлен Python.
    - Установите необходимые зависимости:
        ```bash
        pip install -r backend/requirements.txt
        ```

4. **Запустите приложение:**
    ```bash
    python app.py
    ```
    Приложение будет доступно по адресу `http://127.0.0.1:5000`.

5. **Откройте приложение:**
    Откройте ваш веб-браузер и перейдите по адресу `http://127.0.0.1:5000`, чтобы использовать Приложение Погоды.

## Структура каталогов

- **`backend/`**: Содержит Dockerfile и requirements.txt для настройки среды бэкенда.
- **`frontend/`**: Содержит Dockerfile для настройки среды фронтенда.
- **`instance/`**: Хранит файл базы данных SQLite.
- **`templates/`**: Содержит HTML-шаблоны для веб-приложения.
- **`docker-compose.yml`**: Файл конфигурации Docker Compose для настройки многоконтейнерного приложения.

## Сотрудничество

Внесение вкладов в Приложение Погоды приветствуется! Если у вас есть предложения или улучшения, пожалуйста, создайте проблему или отправьте запрос на слияние.

## Лицензия

Этот проект лицензирован на условиях лицензии MIT. См. файл [LICENSE](LICENSE) для подробностей.

## Контакт

Если у вас есть вопросы или отзывы, пожалуйста, свяжитесь с [Том](mailto: tommyk9797@gmail.com, telegram: @tommyrun97)