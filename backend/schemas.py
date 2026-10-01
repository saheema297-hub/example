from pydantic import BaseModel
from typing import List, Optional

class Cart(BaseModel):
    items: List[str]
    calculated_total: float
    currency: str = "INR"

class PolicyEvaluateRequest(BaseModel):
    session_id: str
    customer_intent_budget: float
    proposed_cart: Cart

class PolicyEvaluateResponse(BaseModel):
    status: str
    reason_code: Optional[str] = None
    message: Optional[str] = None
    action_required: Optional[str] = None

class CreateOrderRequest(BaseModel):
    session_id: str
    amount: float
    currency: str = "INR"

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    requires_payment: bool = False
    payment_link: Optional[str] = None
