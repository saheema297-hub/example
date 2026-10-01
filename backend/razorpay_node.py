import razorpay
import os
from dotenv import load_dotenv

load_dotenv()

# We use test keys for hackathon
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_demo")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "demo_secret")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount_inr: float, session_id: str):
    # Amount is in paise
    amount_paise = int(amount_inr * 100)
    
    # Try creating order (mock if it fails due to fake keys)
    try:
        if RAZORPAY_KEY_ID == "rzp_test_demo":
            return {"id": "plink_mock123", "short_url": f"https://rzp.io/i/mock_{session_id}"}
            
        data = {
            "amount": amount_paise,
            "currency": "INR",
            "reference_id": session_id,
            "description": "AgentGuard AI Checkout",
            "customer": {
                "name": "Demo User",
                "email": "demo@example.com"
            }
        }
        payment_link = client.payment_link.create(data)
        return payment_link
    except Exception as e:
        return {"id": f"plink_mock_{session_id}", "short_url": f"https://rzp.io/i/mock_{session_id}", "mock": True}
