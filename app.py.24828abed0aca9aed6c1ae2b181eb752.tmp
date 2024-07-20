from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
db = SQLAlchemy(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), nullable=False)
    count = db.Column(db.Integer, default=1)

def create_tables():
    with app.app_context():
        db.create_all()
        logger.info('Database tables created')

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            api_key = 'cdbc514bc130625a55698fe4db725a15'
            try:
                response = requests.get('https://api.openweathermap.org/data/2.5/weather', params={
                    'q': city,
                    'appid': api_key,
                    'units': 'metric'
                })
                response.raise_for_status()  # Raise an HTTPError for bad responses
                weather_data = response.json()

                # Save search history
                history = SearchHistory.query.filter_by(city=city).first()
                if history:
                    history.count += 1
                else:
                    history = SearchHistory(city=city)
                    db.session.add(history)
                db.session.commit()

                logger.info(f"Weather data for {city}: {weather_data}")
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                error = 'Failed to fetch weather data'
        else:
            error = 'City is required'

    return render_template('index.html', weather_data=weather_data, error=error)

@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    api_key = 'cdbc514bc130625a55698fe4db725a15'
    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params={
            'q': city,
            'appid': api_key,
            'units': 'metric'
        })
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()

        # Save search history
        history = SearchHistory.query.filter_by(city=city).first()
        if history:
            history.count += 1
        else:
            history = SearchHistory(city=city)
            db.session.add(history)
        db.session.commit()

        logger.info(f"Weather data for {city}: {data}")
        return jsonify(data)
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return jsonify({'error': 'Failed to fetch weather data'}), 500

@app.route('/history', methods=['GET'])
def get_history():
    try:
        histories = SearchHistory.query.all()
        return jsonify([{'city': h.city, 'count': h.count} for h in histories])
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500

@app.route('/populate', methods=['GET'])
def populate():
    # Список городов для тестирования
    cities = ['Moscow', 'London', 'New York', 'Beijing', 'Paris', 'Rome']

    # Ваш сервер Flask
    base_url = 'http://127.0.0.1:5000/weather'

    # Отправляем запросы для каждого города
    for city in cities:
        try:
            response = requests.get(base_url, params={'city': city})
            response.raise_for_status()  # Raise an HTTPError for bad responses
            logger.info(f'Weather data for {city}: {response.json()}')
        except requests.RequestException as e:
            logger.error(f'Failed to get weather data for {city}: {e}')

    return jsonify({'status': 'Population complete'})

if __name__ == '__main__':
    create_tables()  # Создать таблицы перед запуском приложения
    app.run(debug=True)
