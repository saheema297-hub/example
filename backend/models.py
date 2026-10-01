from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime
from database import Base
import datetime

class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(String, index=True)
    name = Column(String)
    max_transaction_value = Column(Float)
    blocked_categories = Column(JSON)  # List of strings
    active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    action = Column(String)
    status = Column(String)  # APPROVED, BLOCKED
    reason = Column(String)
    amount = Column(Float)
    cart_details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    category = Column(String)
