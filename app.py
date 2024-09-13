import asyncio
from asyncio import Semaphore

import logging
import os
from io import BytesIO  
import aiohttp
from aiohttp import ClientSession

import pandas as pd
import requests
import tornado
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask, jsonify, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from tenacity import retry, wait_fixed
from datetime import datetime, timedelta
from flask_caching import Cache
 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Otventa2593@localhost:5432/base'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,  
    'max_overflow': 5,  
    'pool_timeout': 30,  
    'pool_recycle': 1800  
}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

Base = declarative_base()

cache = Cache(app, config={'CACHE_TYPE': 'simple'})  

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), index=True)  
    temperature = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    wind_direction = db.Column(db.String(10))
    pressure = db.Column(db.Float)
    precipitation = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)  
    
    __table_args__ = (db.UniqueConstraint('city', 'timestamp', name='_city_timestamp_uc'),)  


def create_tables():
    with app.app_context():
        try:
            db.create_all()
            logger.info('Database tables created')
        except OperationalError as e:
            logger.error(f'Failed to create tables: {e}')


async def periodic_weather_fetch():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_save_weather_data, 'interval', minutes=3)
    scheduler.start()
    while True:
        await asyncio.sleep(3600)
        
        
sem = Semaphore(5)  

async def fetch_weather_for_city(session, city):
    async with sem:
        api_key = os.getenv('OPENWEATHERMAP_API_KEY', '572a2e17761b21d42f7698d383e91934')
        try:
            async with session.get('https://api.openweathermap.org/data/2.5/weather', params={
                'q': city,
                'appid': api_key,
                'units': 'metric'
            }) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch weather data for {city}: {response.status}")
        except Exception as e:
            logger.error(f"Exception for city {city}: {e}")
        return None

async def fetch_weather_data():
    cities = ['Boston', 'Toronto', 'Moscow']  
    async with ClientSession() as session:
        tasks = [fetch_weather_for_city(session, city) for city in cities]
        results = await asyncio.gather(*tasks)
        return results  

async def fetch_and_save_weather_data():
    cities = ['Boston', 'Toronto', 'Moscow']
    api_key = os.getenv('OPENWEATHERMAP_API_KEY', '572a2e17761b21d42f7698d383e91934')
    weather_data_list = []  

    async with aiohttp.ClientSession() as session:
        for city in cities:
            try:
                async with session.get('https://api.openweathermap.org/data/2.5/weather', params={
                    'q': city,
                    'appid': api_key,
                    'units': 'metric'
                }) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        
                        if 'main' in data and 'wind' in data:
                            weather_data = WeatherData(
                                city=city,  
                                temperature=data['main']['temp'],
                                wind_speed=data['wind']['speed'],
                                wind_direction=str(data['wind'].get('deg', 'N/A')),
                                pressure=data['main']['pressure'],
                                precipitation=data.get('rain', {}).get('1h', 0)
                            )
                            weather_data_list.append(weather_data)
                            logger.info(f"Weather data for {city}: {data}")
                    else:
                        logger.error(f"Failed to fetch weather data for {city}: {response.status}")
            except Exception as e:
                logger.error(f"Exception for city {city}: {e}")
    
    
    if weather_data_list:
        with app.app_context():
            db.session.bulk_save_objects(weather_data_list)
            db.session.commit()
            logger.info(f"Batch inserted weather data for {len(weather_data_list)} cities")


CACHE_DURATION = timedelta(minutes=10)  

def should_fetch_new_data(city):
    last_record = WeatherData.query.filter_by(city=city).order_by(WeatherData.timestamp.desc()).first()
    if last_record:
        time_since_last_update = datetime.utcnow() - last_record.timestamp
        return time_since_last_update > CACHE_DURATION
    return True  


@app.route('/favicon.ico')
def favicon():
    return send_file(os.path.join(app.root_path, 'templates', 'favicon.ico'), mimetype='image/vnd.microsoft.icon')


@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            api_key = os.getenv('OPENWEATHERMAP_API_KEY', '572a2e17761b21d42f7698d383e91934')
            try:
                response = requests.get('https://api.openweathermap.org/data/2.5/weather', params={
                    'q': city,
                    'appid': api_key,
                    'units': 'metric'
                }, timeout=10)  

                if response.status_code == 401:
                    logger.error("Invalid API key")
                    error = 'Invalid API key'
                elif response.status_code == 404:
                    logger.error(f"City {city} not found")
                    error = f"City {city} not found"
                elif response.status_code == 429:
                    logger.error("API request limit exceeded")
                    error = 'API request limit exceeded'
                else:
                    response.raise_for_status()  
                    weather_data = response.json()

                    
                    history = WeatherData(
                        temperature=weather_data['main']['temp'],
                        wind_speed=weather_data['wind']['speed'],
                        wind_direction=str(weather_data['wind'].get('deg', 'N/A')),  # Проверка наличия направления ветра
                        pressure=weather_data['main']['pressure'],
                        precipitation=weather_data.get('rain', {}).get('1h', 0)  
                    )
                    db.session.add(history)
                    db.session.commit()

                    logger.info(f"Weather data for {city}: {weather_data}")

            except requests.Timeout:
                logger.error(f"Request to OpenWeatherMap API timed out for {city}")
                error = 'Request timed out'
            except requests.ConnectionError:
                logger.error(f"Connection error occurred while fetching weather for {city}")
                error = 'Connection error'
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                error = 'Failed to fetch weather data from OpenWeatherMap API'
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                error = 'An unexpected error occurred'
        else:
            error = 'City is required'

    return render_template('index.html', weather_data=weather_data, error=error)


@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'City is required'}), 400

    api_key = os.getenv('OPENWEATHERMAP_API_KEY', '572a2e17761b21d42f7698d383e91934')

    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params={
            'q': city,
            'appid': api_key,
            'units': 'metric'
        }, timeout=10)  

        if response.status_code == 401:
            logger.error("Invalid API key")
            return jsonify({'error': 'Invalid API key'}), 401
        elif response.status_code == 404:
            logger.error(f"City {city} not found")
            return jsonify({'error': f"City {city} not found"}), 404
        elif response.status_code == 429:
            logger.error("API request limit exceeded")
            return jsonify({'error': 'API request limit exceeded'}), 429
        else:
            response.raise_for_status()  
            weather_data = response.json()

            
            history = WeatherData(
                city=city,  
                temperature=weather_data['main']['temp'],
                wind_speed=weather_data['wind']['speed'],
                wind_direction=str(weather_data['wind'].get('deg', 'N/A')),
                pressure=weather_data['main']['pressure'],
                precipitation=weather_data.get('rain', {}).get('1h', 0)
            )
            db.session.add(history)
            db.session.commit()

            logger.info(f"Weather data for {city}: {weather_data}")
            return jsonify(weather_data)

    except requests.Timeout:
        logger.error(f"Request to OpenWeatherMap API timed out for {city}")
        return jsonify({'error': 'Request timed out'}), 500
    except requests.ConnectionError:
        logger.error(f"Connection error occurred while fetching weather for {city}")
        return jsonify({'error': 'Connection error'}), 500
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return jsonify({'error': 'Failed to fetch weather data'}), 500


@cache.memoize(timeout=900)
def get_weather_from_api(city):
    api_key = os.getenv('OPENWEATHERMAP_API_KEY', '572a2e17761b21d42f7698d383e91934')
    try:
        response = requests.get('https://api.openweathermap.org/data/2.5/weather', params={
            'q': city,
            'appid': api_key,
            'units': 'metric'
        }, timeout=10)  

        response.raise_for_status()  
        return response.json()
    
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

@app.route('/history', methods=['GET'])
def get_history():
    try:
        histories = WeatherData.query.all()
        return jsonify([{
            'city': h.city,  
            'temperature': h.temperature,
            'wind_speed': h.wind_speed,
            'wind_direction': h.wind_direction,
            'pressure': h.pressure,
            'precipitation': h.precipitation
            } for h in histories])

    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500


@app.cli.command('export_data')
def export_data():
    """Export the last 10 weather records to an Excel file."""
    try:
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI']) 
        
        with engine.connect() as conn:
            query = "SELECT * FROM weather_data ORDER BY id DESC LIMIT 10"
            df = pd.read_sql(query, conn)

            df.to_excel('last_10_weather_records.xlsx', index=False)
            logger.info("Exported data to last_10_weather_records.xlsx")

    except Exception as e:
        logger.error(f"Failed to export data: {e}")


@app.route('/export', methods=['GET'])
def export_to_excel():
    try:
        print("Export request received")
        weather_data = WeatherData.query.order_by(WeatherData.id.desc()).limit(10).all()
        
        if not weather_data:
            return jsonify({'error': 'No weather data available to export'}), 404

        data = {
            'City': [record.city for record in weather_data],  
            'Temperature (°C)': [record.temperature for record in weather_data],
            'Wind Speed (m/s)': [record.wind_speed for record in weather_data],
            'Wind Direction (°)': [record.wind_direction for record in weather_data],'Pressure (hPa)': [record.pressure for record in weather_data],
            'Precipitation (mm)': [record.precipitation for record in weather_data],'Timestamp': [record.timestamp.strftime('%Y-%m-%d %H:%M:%S') for record in weather_data]
            }


        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='WeatherData')

        output.seek(0)

        return send_file(output, 
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                         download_name='weather_data.xlsx', 
                         as_attachment=True)
    except Exception as e:
        logger.error(f"Failed to export data to Excel: {e}")
        return jsonify({'error': 'Failed to export data'}), 500


# Get the last 10 weather records
def get_last_10_weather_records():
    return WeatherData.query.with_entities(
        WeatherData.city,  
        WeatherData.temperature,
        WeatherData.wind_speed,
        WeatherData.wind_direction,
        WeatherData.pressure,
        WeatherData.precipitation,
        WeatherData.timestamp
    ).order_by(WeatherData.id.desc()).limit(10).all()

    
@retry(wait=wait_fixed(2))  
def save_weather_data(weather_data):
    try:
        db.session.add(weather_data)
        db.session.commit()
    except OperationalError as e:
        logger.error(f"Database error occurred: {e}")
        db.session.rollback()  



if __name__ == '__main__':
    create_tables()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(periodic_weather_fetch())
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
