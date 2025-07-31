from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory "database"
fake_users_db = {}

# Pydantic model for user data
class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI sample application!"}

@app.post("/users/")
def create_user(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    fake_users_db[user.username] = user
    return {"message": "User created successfully", "user": user}

@app.get("/users/{username}")
def read_user(username: str):
    user = fake_users_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
