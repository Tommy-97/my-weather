import pytest
from backend.app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Добавьте фиктивные данные
            # db.session.add(...)
            # db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

def test_index(client):
    """Тест главной страницы."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Weather App' in response.data  

def test_get_weather(client):
    """Тест получения данных о погоде."""
    
    response = client.get('/weather?city=London')
    assert response.status_code == 200
    assert b'London' in response.data  
