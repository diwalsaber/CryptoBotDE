import pytest
import json
import requests
from main import app
import random

def test_root():
    url = "http://localhost:8001/"
    response = requests.get(url)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Bienvenue sur l'API de prévision du cours du Bitcoin"}
    
def test_ohlcv_route():
    url = "http://localhost:8001/ohlcv"
    response = requests.get(url)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert "day" in item
        assert "open" in item
        assert "high" in item
        assert "low" in item
        assert "close" in item
        assert "volume" in item

def test_get_prices():
    url = "http://localhost:8000/prices"
    response = requests.get(url)
    assert response.status_code == 200, f"Expected status code 200, but received {response.status_code}"
    data = response.json()
    assert 'prices' in data, "Response does not contain 'prices' key"
    prices = data['prices']
    assert isinstance(prices, list), "Prices is not a list"
    assert len(prices) > 0, "No prices returned"
    assert all(isinstance(price, float) for price in prices), "Not all prices are floats"

        
def test_get_prices():
    url = "http://localhost:8001/prices?nb_day=1"
    response = requests.get(url)
    assert response.status_code == 200
    assert 'prices' in response.json()
    prices = response.json()['prices']
    assert isinstance(prices, list)
    assert len(prices) == 1
    assert isinstance(prices[0], float)
    
def test_predict_next_price():
    url = "http://localhost:8001/predict"
    headers = {"Content-Type": "application/json"}

    # Cas où le nombre d'éléments est égal à 3
    data = {"data": [random.random() for _ in range(3)]}
    response = requests.post(url, headers=headers, json=data)
    assert response.status_code == 200, f"Expected status code 200, but received {response.status_code}"
    assert "prediction" in response.json()
    prediction = response.json()["prediction"]
    assert isinstance(prediction, float)

    # Cas où le nombre d'éléments est différent de 3
    data = {"data": [random.random() for _ in range(2)]}
    response = requests.post(url, headers=headers, json=data)
    assert response.status_code == 400, f"Expected status code 400, but received {response.status_code}"
    assert "detail" in response.json()
    error_message = response.json()["detail"]
    assert error_message == "Input data should have three elements.", f"Unexpected error message: {error_message}"


