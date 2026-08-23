from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class EventSchema(BaseModel):
    event_id: str
    source: str  # razorpay | checkout | subscription | invoice_system
    customer_id: str
    amount: float
    currency: str = "INR"
    raw_payload: Dict[str, Any] = {}
    received_at: datetime = Field(default_factory=datetime.utcnow)

class CustomerSchema(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: str
    payment_methods: List[str] = []
    opt_out: bool = False
    history: Dict[str, Any] = {
        "past_recoveries": 0,
        "past_failures": 0,
        "lifetime_value": 0.0
    }

class TransactionSchema(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    status: str  # failed | pending | succeeded
    failure_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RecoveryCaseSchema(BaseModel):
    case_id: str
    transaction_id: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    event_type: str  # payment_failure | checkout_abandonment | subscription_dunning | overdue_invoice
    amount: float
    risk_score: float = 0.5
    recovery_probability: float = 0.5
    root_cause: Optional[str] = None
    reasoning_summary: Optional[str] = None
    selected_action: Optional[str] = None
    action_rationale: Optional[str] = None
    attempts: int = 0
    last_action_at: Optional[datetime] = None
    last_contact_at: Optional[datetime] = None
    recovered_amount: float = 0.0
    status: str = "detected"  # detected | diagnosing | deciding | guarded | executing | recovered | escalated | closed | blocked
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PromiseToPaySchema(BaseModel):
    promise_id: str
    case_id: str
    promised_amount: float
    due_date: datetime
    status: str = "promised"  # promised | paid | broken
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLogSchema(BaseModel):
    log_id: str
    case_id: str
    agent: str  # Detector | Diagnosis | Strategy | ComplianceGuard | Execution | Audit
    decision: str
    reason: str
    tool_called: Optional[str] = None
    result: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ComplianceDecisionSchema(BaseModel):
    decision_id: str
    case_id: str
    customer_id: str
    action_attempted: str
    decision: str  # ALLOW | BLOCK | ESCALATE
    rule_fired: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
