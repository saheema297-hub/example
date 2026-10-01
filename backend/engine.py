from sqlalchemy.orm import Session
from models import Policy, Product, AuditLog
from schemas import PolicyEvaluateRequest, PolicyEvaluateResponse
import datetime

def evaluate_policy(db: Session, request: PolicyEvaluateRequest) -> PolicyEvaluateResponse:
    # Get active policy (assuming merchant_id='demo_merchant')
    policy = db.query(Policy).filter(Policy.merchant_id == "demo_merchant", Policy.active == True).first()
    
    if not policy:
        return PolicyEvaluateResponse(status="APPROVED")
        
    cart_total = request.proposed_cart.calculated_total
    
    # 1. Budget validation
    if cart_total > policy.max_transaction_value:
        log_audit(db, request, "BLOCKED", "MAX_TX_EXCEEDED", f"Transaction exceeds merchant maximum limit (₹{cart_total} > ₹{policy.max_transaction_value}).")
        return PolicyEvaluateResponse(
            status="BLOCKED",
            reason_code="MAX_TX_EXCEEDED",
            message=f"Transaction Intercepted. Reason: Exceeds merchant maximum transaction policy (₹{cart_total} > ₹{policy.max_transaction_value}). Price mismatch detected.",
            action_required="PROPOSE_CHEAPER_ALTERNATIVE"
        )
        
    # 2. Customer intent validation
    if cart_total > request.customer_intent_budget:
        log_audit(db, request, "BLOCKED", "BUDGET_EXCEEDED", f"Cart total (₹{cart_total}) exceeds the customer's stated intent limit (₹{request.customer_intent_budget}).")
        return PolicyEvaluateResponse(
            status="BLOCKED",
            reason_code="BUDGET_EXCEEDED",
            message=f"Cart total (₹{cart_total}) exceeds the customer's stated intent limit (₹{request.customer_intent_budget}).",
            action_required="PROPOSE_CHEAPER_ALTERNATIVE"
        )
        
    # 3. Item Category / Price Mismatch validation
    db_total = 0
    blocked_categories = policy.blocked_categories or []
    for item_id in request.proposed_cart.items:
        product = db.query(Product).filter(Product.id == item_id).first()
        if not product:
            log_audit(db, request, "BLOCKED", "INVALID_ITEM", f"Item {item_id} not found in catalog.")
            return PolicyEvaluateResponse(
                status="BLOCKED",
                reason_code="INVALID_ITEM",
                message=f"Item {item_id} not found in catalog.",
                action_required="REMOVE_INVALID_ITEM"
            )
            
        if product.category in blocked_categories:
            log_audit(db, request, "BLOCKED", "BLOCKED_CATEGORY", f"Item {item_id} belongs to blocked category: {product.category}.")
            return PolicyEvaluateResponse(
                status="BLOCKED",
                reason_code="BLOCKED_CATEGORY",
                message=f"Item belongs to blocked category.",
                action_required="REMOVE_BLOCKED_ITEM"
            )
            
        db_total += product.price
        
    if db_total != cart_total:
        log_audit(db, request, "BLOCKED", "PRICE_MISMATCH", "AI hallucinated discount or price mismatch.")
        return PolicyEvaluateResponse(
            status="BLOCKED",
            reason_code="PRICE_MISMATCH",
            message=f"Transaction Intercepted. Reason: Exceeds merchant maximum transaction policy. Price mismatch detected.",
            action_required="CORRECT_PRICE"
        )
        
    log_audit(db, request, "APPROVED", "CLEAN", "Transaction is policy-compliant.")
    return PolicyEvaluateResponse(status="APPROVED")
    
def log_audit(db: Session, request: PolicyEvaluateRequest, status: str, reason: str, message: str):
    log = AuditLog(
        session_id=request.session_id,
        action="AI_CHECKOUT_ATTEMPT",
        status=status,
        reason=message,
        amount=request.proposed_cart.calculated_total,
        cart_details=request.proposed_cart.model_dump()
    )
    db.add(log)
    db.commit()
