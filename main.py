from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import stripe
from os import environ

from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Set your Stripe API key (replace this with your actual secret key or use environment variables)
stripe.api_key = environ.get("API_KEY")


# Customer creation request body model
class CustomerRequest(BaseModel):
    email: str
    name: str
    description: str = "Customer created via API"


# Payment intent creation request body model
class PaymentIntentRequest(BaseModel):
    amount: int  
    currency: str = 'usd'
    customer_id: str  


class CancelPaymentRequest(BaseModel):
    payment_intent_id: str  # The ID of the payment intent to cancel


class RefundRequest(BaseModel):
    payment_intent_id: str  # The ID of the payment intent to refund
    amount: int = None  # Optional: Amount to refund in cents

class InvoiceItemRequest(BaseModel):
    customer_id: str
    amount: int  # Amount in cents
    currency: str = 'usd'
    description: str = "Invoice Item Description"


@app.get("/stripe-auth")
async def stripe_auth():
    """Stripe authentication endpoint (optional, usually used for client-side)."""
    return {"publicKey":environ.get("STRIPE_PUBLIC_KEY")}

# Endpoint to create a new customer
@app.post('/create-customer')
def create_customer(request: CustomerRequest):
    try:
        customer = stripe.Customer.create(
            email=request.email,
            name=request.name,
            description=request.description
        )
        return {
            "customer_id": customer.id,
            "email": customer.email,
            "name": customer.name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post('/create-invoice-item')
def create_invoice_item(request: InvoiceItemRequest):
    try:
        invoice_item = stripe.InvoiceItem.create(
            customer=request.customer_id,
            amount=request.amount,  
            currency=request.currency,
            description=request.description
        )
        return {
            "invoice_item_id": invoice_item.id,
            "amount": invoice_item.amount,
            "currency": invoice_item.currency,
            "description": invoice_item.description
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to create a payment intent
@app.post('/create-payment-intent')
def create_payment_intent(request: PaymentIntentRequest):
    try:
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            customer=request.customer_id,  # Link to existing customer
            payment_method_types=["card"],
        )
        return {'client_secret': intent.client_secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cancel-payment")
async def cancel_payment(cancel_request: CancelPaymentRequest):
    """Endpoint to cancel a payment intent."""
    try:
        cancellation = stripe.PaymentIntent.cancel(cancel_request.payment_intent_id)
        return {"status": cancellation.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/payment-history")
async def payment_history(limit: int = 10):
    """Endpoint to retrieve payment history."""
    try:
        payments = stripe.PaymentIntent.list(limit=limit)
        return {"payments": payments.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refund-payment")
async def refund_payment(refund_request: RefundRequest):
    """Endpoint to refund a payment."""
    try:
        refund = stripe.Refund.create(
            payment_intent=refund_request.payment_intent_id,
            amount=refund_request.amount,  # If None, the full amount will be refunded
        )
        return {"status": refund.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

