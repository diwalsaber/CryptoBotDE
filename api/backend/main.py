from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
from keras.models import load_model
from keras.preprocessing.sequence import TimeseriesGenerator
import joblib

# charge le modèle de prédiction
model = load_model('lstm.h5')
scaler = joblib.load('scaler.job')

# Initialiser FastAPI
app = FastAPI()

# Définition du modèle de données


class Input(BaseModel):
    data: list[float]


# Route pour la prédiction
@app.post("/predict")
def predict(input: Input):
    # Convertir les données en DataFrame
    data = pd.DataFrame(input.data).values.reshape(-1, 1).astype('float32')
    #print(data)

    # Normaliser les données
    data_scaled = scaler.transform(data) #.reshape(-1, 1)).flatten()

    # Create TimeseriesGenerator for the training data
    #generator = TimeseriesGenerator(
    #data_scaled, data_scaled, length=3, batch_size=1, stride=1)

    #data_scaled_reshaped = data_scaled.reshape(1, 3, 1)

    # Prédiction
    prediction = model.predict(data_scaled)
    prediction = scaler.inverse_transform(prediction)

    return {'prediction': prediction.tolist()}