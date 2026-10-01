from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db, SessionLocal
from models import Policy, Product, AuditLog
from schemas import ChatRequest, ChatResponse, PolicyEvaluateRequest, PolicyEvaluateResponse
from orchestrator import process_chat
from engine import evaluate_policy
import os
import uvicorn

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Razorpay AgentGuard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    db = SessionLocal()
    # Check if data exists
    if not db.query(Product).first():
        products = [
            Product(id="P_101", name="Flagship Gaming Laptop", price=150000, category="Electronics"),
            Product(id="P_902", name="Mechanical Keyboard", price=3500, category="Accessories"),
            Product(id="P_304", name="Wireless Mouse", price=1500, category="Accessories")
        ]
        db.add_all(products)
        
    if not db.query(Policy).first():
        policy = Policy(
            merchant_id="demo_merchant",
            name="Default Security Policy",
            max_transaction_value=5000,
            blocked_categories=["Weapons", "Drugs"],
            active=True
        )
        db.add(policy)
        
    db.commit()
    db.close()

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        res = process_chat(request.session_id, request.message)
        return ChatResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/policy/evaluate", response_model=PolicyEvaluateResponse)
def policy_evaluate_endpoint(request: PolicyEvaluateRequest, db: Session = Depends(get_db)):
    return evaluate_policy(db, request)

@app.get("/api/audit-logs")
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
    return logs

@app.get("/api/policy")
def get_policy(db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.merchant_id == "demo_merchant").first()
    return policy

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
