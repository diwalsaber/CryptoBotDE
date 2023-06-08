import os

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import timedelta
import jwt

from typing import Union, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status

from pydantic import ValidationError

from cryptobot.common import DBUtils
from schemas import APIKey

ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
API_KEY_EXPIRE_MINUTES = 60 * 24 * 365 * 5 # 5 years
ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']  # should be kept secret
JWT_REFRESH_SECRET_KEY = os.environ['JWT_REFRESH_SECRET_KEY']  # should be kept secret

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

reuseable_oauth = OAuth2PasswordBearer(
    tokenUrl="/signin",
    scheme_name="JWT"
)

def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), 'is_api_key': False}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_api_key(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + timedelta(days=expires_delta)
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=API_KEY_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), 'is_api_key': True}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt, expires_delta
def get_api_keys(email:str) -> list[APIKey]:
    return [APIKey(key=key['key'], expiration_date=key['expiration_date'], name=key['name']) for key in DBUtils.get_api_keys(email)]

def revoke_api_key(email: str, key:str):
    DBUtils.delete_api_key(email, key)


def revoke_api_keys(email: str):
    DBUtils.delete_api_keys(email)

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expires_delta, "sub": str(subject), 'api_key': False}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt



def get_refresh_current_user(token: str) :
    try:
        payload = jwt.decode(
            token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM]
        )
        if datetime.fromtimestamp(payload['exp']) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"Authorization": "Bearer"},
            )

    except(jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"Authorization": "Bearer"},
        )
    user = DBUtils.get_user(payload['sub'])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )
    return user

async def get_current_user(token: str = Depends(reuseable_oauth)) :
    try:
        payload = jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[ALGORITHM]
        )
        if datetime.fromtimestamp(payload['exp']) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"Authorization": "Bearer"},
            )
    except(jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"Authorization": "Bearer"},
        )

    user: Union[dict[str, Any], None] = DBUtils.get_user(payload['sub'])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )
    if payload['is_api_key']:
        #check api key is still exists in the db
        if DBUtils.exists_api_key(payload['sub'], token):
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
                headers={"Authorization": "Bearer"},
            )
    else:
        return user


async def is_admin(user: str = Depends(get_current_user)) :

    if user and user['email'] == 'admin':
        return user
    raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not athorized user",
            headers={"WWW-Authenticate": "Bearer"},
    )