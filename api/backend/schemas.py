from datetime import datetime
from enum import Enum

import pandas as pd
from pydantic import BaseModel
from fastapi import Query
from typing import Annotated, List


class FeatureColumn(str, Enum):
    open_price = 'open_price'
    high_price = 'high_price'
    low_price = 'low_price'
    close_price = 'close_price'
    base_volume = 'base_volume'
    quote_volume = 'quote_volume'
    number_trades = 'number_trades'
    taker_buybase = 'taker_buybase'
    taker_buyquote = 'taker_buyquote'

class Features(BaseModel):
    open_price: float=-1
    high_price: float=-1
    low_price: float=-1
    close_price: float=-1
    base_volume: float=-1
    quote_volume: float=-1
    number_trades: float=-1
    taker_buybase: float=-1
    taker_buyquote: float=-1


    def to_values_dict(self):
        #filter negative values
        dictfilt = lambda t: t[1] >= 0
        return [{t[0]: t[1]} for t in list(filter(dictfilt, [item for item in vars(self).items()]))]

    def to_values_list(self):
        #filter negative values
        dictfilt = lambda t: t[1] >= 0
        return [t[1] for t in list(filter(dictfilt, [item for item in vars(self).items()]))]

    def get_valid_columns(self):
        #filter negative values
        dictfilt = lambda t: t[1] >= 0
        return [t[0] for t in list(filter(dictfilt, [item for item in vars(self).items()]))]
class CreateModelInput(BaseModel):
    symbol:str
    interval:str
    features: List[FeatureColumn]
    dir:str='models'
    target:FeatureColumn= FeatureColumn.close_price
    epochs:int=10
    lookback:int=3
    units:int=50
class RefreshTokenInput(BaseModel):
    refresh_token:str
class PredictInput(BaseModel):
    features: List[Features]

    def to_DataFrame(self):
        return pd.DataFrame([f.to_values_list() for f in self.features], columns=self.features[0].get_valid_columns())

class Input(BaseModel):
    """
    Classe pour la validation de l'entrée.
    data : liste des derniers prix de clôture du BTC
    """
    data: list[float]

class TokenSchema(BaseModel):
    access_token:str
    refresh_token:str

class APIKey(BaseModel):
    key:str
    expiration_date:datetime
    name:str
class ApiKeyInput(BaseModel):
    validityInDays:int
    name:str
class RefreshInput(BaseModel):
    refresh_key: Annotated[str, Query(min_length=5, max_length=500)]
class UserAuth(BaseModel):
    email: Annotated[str, Query(min_length=5, max_length=100)]
                                #regex="([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+")]
    password: Annotated[str, Query(min_length=5, max_length=20)]


class AddModelInput(BaseModel):
    symbol: Annotated[str, Query(min_length=5, max_length=20,regex="[A-Z0-9]+")]
    interval: Annotated[str, Query(min_length=2, max_length=5)]
    lookback: int


class HistoryConfigInput(BaseModel):
    symbol: Annotated[str, Query(min_length=5, max_length=20,regex="[A-Z0-9]+")]
    interval: Annotated[str, Query(min_length=2, max_length=5)]
    startdate: datetime
    dir:str='data'
