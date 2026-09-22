from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TicketRecord(BaseModel):
    ticket_number: Optional[str] = None
    restaurant: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    table: Optional[str] = None
    amount: Optional[str] = None
    discrepancy_type: Optional[str] = None
    has_discrepancy: bool = True
    notes: Optional[str] = None
    order_number: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class ReconciliationResult(BaseModel):
    ticket_number: Optional[str] = None
    restaurant: Optional[str] = None
    status: str = Field(..., description="Matched | Missing | Needs Review")
    match_confidence: Optional[str] = None
    matched_entry_id: Optional[int] = None
    matched_entry_ticket_number: Optional[str] = None
    reason_provided: bool = False
    issue_addressed: Optional[str] = None
    reason_evidence: List[str] = Field(default_factory=list)
    handwritten_note: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)


class ReconcileRequest(BaseModel):
    tickets: List[TicketRecord] = Field(default_factory=list)
    entries: List[Dict[str, Any]] = Field(default_factory=list)


class ReconcileResponse(BaseModel):
    results: List[ReconciliationResult] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)
