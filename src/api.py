import os, sys
import jwt
import uvicorn
import logging
import pandas as pd

from pydantic import BaseModel
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Depends, status
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from utils import return_models
from data_preprocess import transform_preprocessing



logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

if (logger.hasHandlers()):
    logger.handlers.clear()
logger.addHandler(ch)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

users_db = {
    "user1": {
        "username": "user1",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str
    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Functions related to the security and authentication of the API
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/")
def root():
    return {"Hello": "world"}

class Item(BaseModel):
    type_of_residence: str
    sector: str
    net_usable_area: float
    net_area: float
    n_rooms: int
    n_bathroom: int
    latitude: float
    longitude: float
    price: float

@app.get("/prediction")
def generate_prediction(
    current_user: Annotated[User, Depends(get_current_active_user)],
    type_of_residence: Annotated[str, Query(alias="Type")],
    sector: Annotated[str, Query(alias="Sector")],
    net_usable_area: Annotated[float, Query(alias="Net Usable Area")],
    net_area: Annotated[float, Query(alias="Net Area")],
    n_rooms: Annotated[int, Query(alias="Number of rooms")],
    n_bathroom: Annotated[int, Query(alias="Number of bathrooms")],
    latitude: Annotated[float, Query(alias="Latitude")],
    longitude: Annotated[float, Query(alias="Longitude")],
    price: Annotated[float, Query(alias="Price")]
):
    try:
        logger.info("Receiving data.")
        data = {
            "type": type_of_residence,
            "sector": sector,
            "net_usable_area": net_usable_area,
            "net_area": net_area,
            "n_rooms": n_rooms,
            "n_bathroom": n_bathroom,
            "latitude": latitude,
            "longitude": longitude,
            "price": price
        }

        parameters = pd.DataFrame([data])
        logger.info("Returning models.")
        model, preprocessor = return_models()

        logger.info("Preprocessing data")
        parameters = transform_preprocessing(parameters, preprocessor)   
        
        logger.info("Generating prediction")     
        predicted_valuation = model.predict(parameters)
        
        logger.info("Successfully made prediction.")
        return {"predicted_valuation": predicted_valuation[0]}
    
    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        raise HTTPException(status_code=400, detail="Invalid input data")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    uvicorn.run('api:app', host="0.0.0.0", port=8000, reload=True, debug=True)
