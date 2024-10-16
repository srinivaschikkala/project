from fastapi import  Depends, HTTPException,APIRouter,Request
from pydantic import BaseModel, EmailStr
import random
import redis
import smtplib
from email.message import EmailMessage
from enum import Enum
from pydantic import BaseModel, EmailStr, constr
from twilio.rest import Client
from typing import Optional
from app.core.sql import create_item,get_db,get_item
from app.core.auth import get_password_hash,get_redis_client

router = APIRouter()

from fastapi import Request

from app.core.credentials import credentials


class OTPType(str, Enum):
    SIGNUP = "signup"
    LOGIN = "login"

class OTPMethod(str, Enum):
    EMAIL = "email"
    SMS = "sms"

class OTPRequestPayload(BaseModel):
    email: EmailStr
    phone_number: constr(max_length=15)


class OTPPayload(BaseModel):
    otp:int



class User(BaseModel):
    first_name:str 
    last_name:str
    username: constr(max_length=50)
    email: EmailStr
    phone_number: Optional[constr(max_length=15)] = None
    password: str

    

class OTPVerifyPayload(BaseModel):
    otp:int
    user:User


def send_email_otp(email, otp,application,redis_client):
    # Email setup
    msg = EmailMessage()
    msg.set_content(f"Your OTP is {otp}")
    msg['Subject'] = "Your OTP Code"
    msg['From'] = credentials[application]["EMAIL_OTP"].get("EMAIL_HOST_USER")
    msg['To'] = email
    
    # Send the email using SMTP
    try:
        with smtplib.SMTP(credentials[application]["EMAIL_OTP"].get("EMAIL_HOST") ,credentials[application]["EMAIL_OTP"].get("EMAIL_PORT") ) as server:
            server.starttls()  # Secure the connection
            server.login(credentials[application]["EMAIL_OTP"].get("EMAIL_HOST_USER") ,credentials[application]["EMAIL_OTP"].get("EMAIL_HOST_PASSWORD")  )
            server.send_message(msg)
            print(f"Sent OTP {otp} to {email}")
            redis_client.setex(email, 3000, otp)
            return {"detail": "OTP sent to your email"}
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    
def send_mobile_otp(phone_number,otp,application,redis_client):
    redis_client =  get_redis_client(application)
    redis_client.setex(phone_number, 300, otp)
    twilio_client = Client(credentials[application]["SMS_OTP"].get("TWILIO_ACCOUNT_SID") ,credentials[application]["SMS_OTP"].get("TWILIO_AUTH_TOKEN") )
    
    try:
        message = twilio_client.messages.create(
            body=f"Your OTP code is: {otp}",
            from_=credentials[application]["SMS_OTP"].get("TWILIO_PHONE_NUMBER") ,
            to=phone_number
        )
        return {"detail": "OTP sent to your mobile number"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP")



@router.post("/signup/request-otp/")
async def request_otp(request:Request,otp_method:OTPMethod,data:OTPRequestPayload):
    # Generate OTP

    application = request.headers.get("app_name")
    db = get_db(application)
    redis_client =  get_redis_client(application)
    email = get_item(query= f"select * from users where email = '{data.email}'",db=db)
    
    otp = random.randint(100000, 999999)

     # Logic to send the OTP based on the selected method
    if otp_method == OTPMethod.EMAIL:
        if email:
            return "Email already registered"
        email_request = send_email_otp(data.email,otp,application,redis_client)
        return email_request
    if otp_method == OTPMethod.SMS:
        sms_request = send_mobile_otp(data.phone_number,otp,application,redis_client)
        return sms_request



@router.post("/signup/verify-otp/")
async def verify_otp_method(request:Request,otp_method:OTPMethod,verify_request_payload: OTPVerifyPayload):
    # Get the OTP from Redis
    
    application = request.headers.get("app_name")
    db=get_db(application)
    redis_client =  get_redis_client(application)
    if otp_method == OTPMethod.EMAIL:
        key = verify_request_payload.user.email
        stored_otp = redis_client.get(key)
        
        if stored_otp is None:
            raise HTTPException(status_code=404, detail="OTP expired or not found")

        elif int(stored_otp) != verify_request_payload.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        # OTP is correct, proceed to registration logic here
        # Optionally delete the OTP after successful verification
        redis_client.delete(key) 
        
        data = dict(verify_request_payload.user)
        
        data['password'] = get_password_hash(data['password'])
        
        create_item(payload= data,table_name="users",db=db)
    
        return {"detail": "OTP verified, registration successful"}
    elif otp_method == OTPMethod.SMS:
        stored_otp = redis_client.get(verify_request_payload.user.phone_number)

        if stored_otp is None:
            raise HTTPException(status_code=404, detail="OTP expired or not found")

        if int(stored_otp) != verify_request_payload.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        
        data = dict(verify_request_payload.user)
        
        data['password'] = get_password_hash(data['password'])
        
        create_item(payload= data,table_name="users",db=db)

        # Delete OTP after successful verification
        redis_client.delete(verify_request_payload.user.phone_number)

        return {"detail": "OTP verified successfully"}

