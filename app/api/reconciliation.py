import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter

from app.models.reconciliation import ReconcileRequest, ReconcileResponse, ReconciliationResult

router = APIRouter()


def _normalize_ticket_number(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9]", "", str(value))
    return cleaned or None


def _normalize_amount(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip().lower().replace("£", "").replace(",", "")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    return cleaned or None


def _looks_like_sales_report(ticket_number: Optional[str]) -> bool:
    if not ticket_number:
        return False
    digits = re.sub(r"[^0-9]", "", str(ticket_number))
    return len(digits) >= 6 and ("-" in str(ticket_number) or len(digits) >= 10)


def _match_ticket_records(ticket: Dict[str, Any], entry: Dict[str, Any]) -> Tuple[bool, str, str]:
    ticket_number = _normalize_ticket_number(ticket.get("ticket_number") or ticket.get("order_number") or ticket.get("order_no"))
    entry_ticket_number = _normalize_ticket_number(entry.get("ticket_number") or entry.get("order_number") or entry.get("order_no"))

    if ticket_number and entry_ticket_number and ticket_number == entry_ticket_number:
        return True, "high", "Exact ticket-number match"

    if ticket_number and entry_ticket_number and ticket_number in entry_ticket_number or entry_ticket_number in ticket_number:
        return True, "medium", "Partial ticket-number match"

    ticket_amount = _normalize_amount(ticket.get("amount") or ticket.get("total") or ticket.get("grand_total"))
    entry_amount = _normalize_amount(entry.get("amount") or entry.get("total") or entry.get("grand_total"))
    ticket_restaurant = (ticket.get("restaurant") or "").strip().lower()
    entry_restaurant = (entry.get("restaurant") or "").strip().lower()
    ticket_date = (ticket.get("date") or "").strip()
    entry_date = (entry.get("date") or "").strip()
    ticket_time = (ticket.get("time") or "").strip()
    entry_time = (entry.get("time") or "").strip()

    amount_matches = bool(ticket_amount and entry_amount and abs(float(ticket_amount) - float(entry_amount)) < 0.05)
    restaurant_matches = bool(ticket_restaurant and entry_restaurant and ticket_restaurant == entry_restaurant)
    date_matches = bool(ticket_date and entry_date and ticket_date == entry_date)
    time_matches = bool(ticket_time and entry_time and ticket_time == entry_time)

    if restaurant_matches and date_matches and amount_matches:
        return True, "low", "Fallback restaurant + date + amount match"

    if restaurant_matches and date_matches and ticket_time and entry_time:
        return True, "low", "Fallback restaurant + date match (time not exact)"

    return False, "none", "No reliable match"


def _handwritten_note_for_entry(entry: Dict[str, Any]) -> Optional[str]:
    for key in ("handwritten_note", "handwriting", "manual_note", "reason_note", "notes"):
        value = entry.get(key)
        if value:
            return str(value)
    return None


def _reason_provided(note: Optional[str]) -> bool:
    if note is None:
        return False
    note_clean = note.strip()
    return bool(note_clean and len(note_clean) > 2)


def _issue_addressed(ticket: Dict[str, Any], entry: Dict[str, Any], note: Optional[str]) -> Optional[str]:
    if not note:
        return "no"

    text = note.lower()
    amount_present = bool(re.search(r"(amount|price|charged|refund|promo|discount|void|promot|wrong|not|hard|bad|customer)", text))
    if not amount_present:
        return "unclear"

    if ticket.get("discrepancy_type") == "promotion" and ("promo" in text or "promotion" in text or "refund" in text or "discount" in text):
        return "yes"
    if ticket.get("discrepancy_type") == "void" and ("void" in text or "not" in text or "cancel" in text or "removed" in text or "wrong" in text):
        return "yes"
    if ticket.get("discrepancy_type") == "discount" and ("discount" in text or "offer" in text or "promo" in text or "price" in text):
        return "yes"

    if re.search(r"(customer complained|hard|bad|refund|wrong|not|cancel|replaced|rebook|adjusted)", text):
        return "yes"
    return "unclear"


@router.post("/reconcile", response_model=ReconcileResponse)
async def reconcile_ticket_entries(payload: ReconcileRequest):
    results: List[ReconciliationResult] = []
    ticket_entries = payload.tickets or []
    image_entries = payload.entries or []

    for ticket in ticket_entries:
        ticket_number = ticket.ticket_number or ticket.order_number
        normalized_ticket = _normalize_ticket_number(ticket_number)
        matched = None
        match_confidence = "none"
        matched_entry_id = None
        matched_entry_ticket = None
        matched_note = None
        matched_evidence = []

        for entry in image_entries:
            match_bool, confidence, reason = _match_ticket_records(ticket.model_dump() if hasattr(ticket, "model_dump") else ticket, entry)
            if match_bool:
                if matched is None or confidence == "high" or (confidence == "medium" and match_confidence == "low"):
                    matched = entry
                    match_confidence = confidence
                    matched_entry_id = entry.get("id")
                    matched_entry_ticket = entry.get("ticket_number") or entry.get("order_number")
                    matched_note = _handwritten_note_for_entry(entry)
                    matched_evidence = [reason]
                    break

        if matched is None:
            status = "Missing"
            if normalized_ticket and _looks_like_sales_report(normalized_ticket):
                status = "Needs Review"
            results.append(ReconciliationResult(
                ticket_number=ticket_number,
                restaurant=ticket.restaurant,
                status=status,
                match_confidence="none",
                matched_entry_id=None,
                matched_entry_ticket_number=None,
                reason_provided=False,
                issue_addressed=None,
                reason_evidence=[],
                handwritten_note=None,
                evidence=["No matching entry found for this ticket."],
            ))
            continue

        note = _handwritten_note_for_entry(matched)
        issue_state = _issue_addressed(ticket.model_dump() if hasattr(ticket, "model_dump") else ticket, matched, note)
        reason_flag = _reason_provided(note)
        status = "Matched"
        if match_confidence in {"low", "medium"}:
            status = "Needs Review"

        results.append(ReconciliationResult(
            ticket_number=ticket_number,
            restaurant=ticket.restaurant,
            status=status,
            match_confidence=match_confidence,
            matched_entry_id=matched_entry_id,
            matched_entry_ticket_number=matched_entry_ticket,
            reason_provided=reason_flag,
            issue_addressed=issue_state,
            reason_evidence=[note] if note else [],
            handwritten_note=note,
            evidence=matched_evidence + (["Handwritten note present"] if note else []),
        ))

    summary = {
        "Matched": sum(1 for r in results if r.status == "Matched"),
        "Missing": sum(1 for r in results if r.status == "Missing"),
        "Needs Review": sum(1 for r in results if r.status == "Needs Review"),
    }
    return ReconcileResponse(results=results, summary=summary)
