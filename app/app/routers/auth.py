from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import timedelta
from app.core.sql import get_item, get_db
from fastapi import Request
router = APIRouter()


from app.core.auth import create_access_token, create_refresh_token
from app.core.credentials import credentials

# Authentication route for login
@router.post("/token")
async def login_for_access_token(
    request:Request,
    form_data: OAuth2PasswordRequestForm = Depends()

):  
    application = request.headers.get("app_name")
    db=get_db(application)
    user = get_item(f"select * from users where username = '{form_data.username}'", db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",    
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(
        minutes=int(credentials[application]["JWT"].get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
    )
    refresh_token_expires = timedelta(
        days=int(credentials[application]["JWT"].get("JWT_REFRESH_TOKEN_EXPIRE_DAYS"))
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
@router.get("/token/refresh")
async def refresh_access_token(request:Request,refresh_token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"}
    )
    application = request.headers.get("app_name")
    
    try:
        payload = jwt.decode(
            refresh_token,
            credentials[application]["JWT"].get("JWT_REFRESH_SECRET_KEY"),
            algorithms=credentials[application]["JWT"].get("JWT_ALGORITHM"),
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
        credentials[application]["JWT"].get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"),
        minutes=int(credentials[application]["JWT"].get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))
        
    )
    access_token = create_access_token(application,
        data={"user": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "Bearer"}
