from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Optional
from pydantic import BaseModel
from fastapi import Request
from app.core.credentials import credentials
import redis

# User schemas
class TokenData(BaseModel):
    username: Optional[str] = None
    app: Optional[str] = None


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_redis_client(application):
    redis_client = redis.StrictRedis(host= credentials[application]["REDIS"].get("REDIS_HOST") , port=  credentials[application]["REDIS"].get("REDIS_PORT"),
                                      db = credentials[application]["REDIS"].get("REDIS_DB"), decode_responses=True)

    return redis_client


def get_current_user(request: Request):
    authorization = request.headers.get("Authorization")
    application = request.headers.get("app_name")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    
    try:
        # Extract the token from the Authorization header
        token = authorization.split(" ")[1]

        payload = jwt.decode(token,credentials[application]["JWT"].get("JWT_SECRET_KEY") , algorithms=credentials[application]["JWT"].get("JWT_ALGORITHM"))
       
        username = payload.get("user")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except (JWTError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(application:str,data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = (
        datetime.utcnow() + expires_delta
        if expires_delta
        else datetime.utcnow() + timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, credentials[application]["JWT"].get("JWT_SECRET_KEY") , algorithm=credentials[application]["JWT"].get("JWT_ALGORITHM") )


def create_refresh_token(application:str,data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = (
        datetime.utcnow() + expires_delta
        if expires_delta
        else datetime.utcnow() + timedelta(days=7)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, credentials[application]["JWT"].get("JWT_REFRESH_SECRET_KEY") , algorithm=credentials[application]["JWT"].get("JWT_ALGORITHM") )
