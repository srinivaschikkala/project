from fastapi import  Depends, HTTPException,APIRouter
from pydantic import BaseModel, EmailStr
import random
import redis
import smtplib
from email.message import EmailMessage
from enum import Enum
from pydantic import BaseModel, EmailStr, constr
from twilio.rest import Client
from typing import Optional
from app.core.sql import create_item,get_db
from app.core.auth import get_password_hash
from os import environ
router = APIRouter()
from dotenv import load_dotenv 
load_dotenv()
# Configure Redis connection (change this if your Redis server isn't local)
redis_client = redis.StrictRedis(host=environ.get("REDIS_HOST"), port=environ.get("REDIS_PORT"), db = environ.get("REDIS_DB"), decode_responses=True)

# Define your email configuration (for SMTP-based email delivery)
EMAIL_HOST = environ.get("EMAIL_HOST") 
EMAIL_PORT = environ.get("EMAIL_PORT") 
EMAIL_HOST_USER = environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = environ.get("EMAIL_HOST_PASSWORD")


# Twilio configuration (replace with your own credentials)
TWILIO_ACCOUNT_SID = environ.get("TWILIO_ACCOUNT_SID") 
TWILIO_AUTH_TOKEN = environ.get("TWILIO_AUTH_TOKEN") 
TWILIO_PHONE_NUMBER = environ.get("TWILIO_PHONE_NUMBER") 


# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class OTPMethod(str, Enum):
    email = "email"
    sms = "sms"

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
    


def send_email_otp(email: str, otp: int):
    # Email setup
    msg = EmailMessage()
    msg.set_content(f"Your OTP is {otp}")
    msg['Subject'] = "Your OTP Code"
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = email
    
    # Send the email using SMTP
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
            print(f"Sent OTP {otp} to {email}")
            # Store the OTP in Redis with a TTL (e.g., 5 minutes = 300 seconds)
            redis_client.setex(email, 300, otp)
            return {"detail": "OTP sent to your email"}
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    
def send_mobile_otp(phone_number,otp):
    redis_client.setex(phone_number, 300, otp)
        
    try:
        message = twilio_client.messages.create(
            body=f"Your OTP code is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return {"detail": "OTP sent to your mobile number"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send OTP")



@router.post("/signup/request-otp/")
async def request_otp(otp_method:OTPMethod,data:OTPRequestPayload):
    # Generate OTP
    otp = random.randint(100000, 999999)
     # Logic to send the OTP based on the selected method
    if otp_method == OTPMethod.email:
        email_request = send_email_otp(data.email,otp)
        return email_request
    if otp_method == OTPMethod.sms:
        sms_request = send_mobile_otp(data.phone_number,otp)
        return sms_request



@router.post("/signup/verify-otp/")
async def verify_otp_method(otp_method:OTPMethod,verify_request: OTPVerifyPayload,db=Depends(get_db)):
    # Get the OTP from Redis
   
    if otp_method == OTPMethod.email:
        key = verify_request.user.email
        stored_otp = redis_client.get(key)
        
        if stored_otp is None:
            raise HTTPException(status_code=404, detail="OTP expired or not found")

        elif int(stored_otp) != verify_request.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # OTP is correct, proceed to registration logic here
        # Optionally delete the OTP after successful verification
        redis_client.delete(key)
        data = dict(verify_request.user)
        
        data['password'] = get_password_hash(data['password'])
        create_item(payload= data,table_name="users",db=db)
    
        return {"detail": "OTP verified, registration successful"}
    elif otp_method == OTPMethod.sms:
        stored_otp = redis_client.get(verify_request.user.phone_number)

        if stored_otp is None:
            raise HTTPException(status_code=404, detail="OTP expired or not found")

        if int(stored_otp) != verify_request.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Delete OTP after successful verification
        redis_client.delete(verify_request.user.phone_number)
        data = dict(verify_request.user)
        data['password'] = get_password_hash(data['password'])

        create_item(payload= data,table_name="users",db=db)

        return {"detail": "OTP verified successfully"}

