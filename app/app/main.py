"""Main server"""

from fastapi import FastAPI
from app.routers import curd, auth,s3,otp_signup,login

app = FastAPI()


# Include the CRUD router
# app.include_router(router=auth.router)
# app.include_router(router=curd.router)



# app.include_router(router=s3.router)
app.include_router(router=otp_signup.router)
app.include_router(router=login.router)