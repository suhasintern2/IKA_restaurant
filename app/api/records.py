import csv
import io
import json
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.storage.db import get_docket_records, get_ticket_items, get_ticket_records


router = APIRouter()


def _json(raw: str, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _ticket_record(row) -> Dict[str, Any]:
    items = [dict(item) for item in get_ticket_items(row["ticket_id"])]
    for item in items:
        item["is_void"] = bool(item["is_void"])
    return {
        "ticket_id": row["ticket_id"],
        "uploaded_at": row["updated_at"],
        "restaurant": row["restaurant"],
        "phone": row["phone"],
        "date": row["ticket_date"],
        "terminal": row["terminal"],
        "table": row["table_name"],
        "department": row["department"],
        "user": row["user_name"],
        "payment_status": row["payment_status"],
        "credit_card_amount": row["credit_card_amount"],
        "ticket_total": row["ticket_total"],
        "grand_total": row["grand_total"],
        "charged": row["charged"],
        "extra_fields": _json(row["extra_fields"], {}),
        "items": items,
        "screenshot_filenames": _json(row["screenshot_filenames"], []),
    }


def _docket_record(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "order_number": row["docket_order_no"],
        "date": row["docket_date"],
        "time": row["docket_time"],
        "item": row["item"],
        "discrepancy_type": row["discrepancy_type"],
        "description": row["handwritten_reason"],
        "extra_fields": _json(row["extra_fields"], {}),
        "image_filename": row["image_filename"],
        "review_required": bool(row["review_required"]),
        "review_reason": row["review_reason"],
    }


@router.get("/tickets")
async def get_ticket_records_endpoint() -> List[Dict[str, Any]]:
    """Return parsed ticket records with their complete item arrays."""
    return [_ticket_record(row) for row in get_ticket_records()]


@router.get("/dockets")
async def get_docket_records_endpoint() -> List[Dict[str, Any]]:
    """Return parsed docket records, including separate handwriting fields."""
    return [_docket_record(row) for row in get_docket_records()]


@router.get("/tickets/export")
async def export_ticket_records():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ticket_id", "uploaded_at", "restaurant", "terminal", "department", "user", "date",
        "item", "category", "price", "quantity", "total", "is_void",
        "payment_status", "credit_card_amount", "ticket_total", "grand_total",
        "charged", "extra_fields", "screenshots",
    ])
    for ticket in await get_ticket_records_endpoint():
        for item in ticket["items"] or [{}]:
            writer.writerow([
                ticket["ticket_id"], ticket["uploaded_at"], ticket["restaurant"], ticket["terminal"],
                ticket["department"], ticket["user"], ticket["date"],
                item.get("name"), item.get("category"), item.get("unit_price"),
                item.get("quantity"), item.get("total"), item.get("is_void", False),
                ticket["payment_status"], ticket["credit_card_amount"],
                ticket["ticket_total"], ticket["grand_total"], ticket["charged"],
                json.dumps(ticket["extra_fields"]), json.dumps(ticket["screenshot_filenames"]),
            ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tickets.csv"},
    )


@router.get("/dockets/export")
async def export_docket_records():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "order_number", "date", "time", "item",
        "discrepancy_type", "description", "review_required",
        "review_reason", "image_filename", "extra_fields",
    ])
    for docket in await get_docket_records_endpoint():
        writer.writerow([
            docket["order_number"], docket["date"], docket["time"],
            docket["item"], docket["discrepancy_type"], docket["description"],
            docket["review_required"], docket["review_reason"], docket["image_filename"],
            json.dumps(docket["extra_fields"]),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dockets.csv"},
    )