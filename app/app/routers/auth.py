from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta
from app.core.sql import get_item, get_db

router = APIRouter()
from dotenv import load_dotenv

load_dotenv()
from os import environ
from app.core.auth import create_access_token, create_refresh_token


# Authentication route for login
@router.post("/{application}/token")
async def login_for_access_token(
    application: str,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    user = get_item(f"select * from users where username = '{form_data.username}'", db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=int(environ.get(f"{application.upper()}_ACCESS_TOKEN_EXPIRE_MINUTES"))
    )
    refresh_token_expires = timedelta(
        days=int(environ.get(f"{application.upper()}_REFRESH_TOKEN_EXPIRE_DAYS"))
    )

    access_token = create_access_token(application,
        data={"user": user["username"]}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(application,
        data={"user": user["username"]}, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


# Route to refresh the access token
@router.get("/{application}/token/refresh")
async def refresh_access_token(refresh_token: str, application: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            refresh_token,
            environ.get(f"{application.upper()}_REFRESH_SECRET_KEY"),
            algorithms=[environ.get(f"{application.upper()}_ALGORITHM")],
        )

        if payload.get("user") is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_item(
        f"select * from users where username = '{payload.get('user')}'",
        get_db(application),
    )

    if user is None:
        raise credentials_exception

    access_token_expires = timedelta(
        minutes=int(environ.get(f"{application.upper()}_ACCESS_TOKEN_EXPIRE_MINUTES"))
    )
    access_token = create_access_token(application,
        data={"user": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "Bearer"}
