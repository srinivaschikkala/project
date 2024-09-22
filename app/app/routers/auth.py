from fastapi import  Depends, HTTPException, status,APIRouter
from fastapi.security import  OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import  timedelta
from pydantic import BaseModel
from app.core.sql import get_item,get_db
router = APIRouter()

from app.core.auth import (ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS
                           ,create_access_token,create_refresh_token,REFRESH_SECRET_KEY,ALGORITHM)

class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Authentication route for login
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db=Depends(get_db)):
    user = get_item(f"select * from users where username = '{form_data.username}'",db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(data={"user": user['username']}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"user": user['username']}, expires_delta=refresh_token_expires)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer"
    }


# Route to refresh the access token
@router.post("/token/refresh")
async def refresh_access_token(refresh_token_request: RefreshTokenRequest,application:str):
    refresh_token = refresh_token_request.refresh_token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("user") is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = get_item(f"select * from users where username = '{payload.get('user')}'",get_db(application))
    
    if user is None:
        raise credentials_exception
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"user": user['username']}, expires_delta=access_token_expires)
    
    return {
        "access_token": access_token,   
        "token_type": "Bearer"
    }

