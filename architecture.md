# ARCHITECTURE.md — TIL SYSTEM

## 1. High-level split
Backend (this repo) and frontend (teammate's repo) are separate. Backend
exposes a REST API; frontend consumes it per `frontend_spec.md`.

## 2. Backend responsibilities (FastAPI)
- Receive image uploads
- Run text extraction on images
- Parse extracted text into structured fields (restaurant, ticket number,
  discrepancy type, description)
- Persist rows
- Serve the table data to the frontend
- Generate CSV export

## 3. Proposed directory structure

    til-system-backend/
    ├── CONTEXT.md
    ├── mvp_spec.md
    ├── architecture.md
    ├── frontend_spec.md
    ├── rules.md
    ├── decisions.md
    ├── session_log.md
    ├── app/
    │   ├── main.py                # FastAPI app entrypoint
    │   ├── api/
    │   │   ├── upload.py          # POST endpoint: receive image(s)
    │   │   ├── entries.py         # GET/PATCH endpoints: table rows
    │   │   └── export.py          # GET endpoint: CSV export
    │   ├── extraction/
    │   │   └── ocr.py             # text extraction from image
    │   ├── models/
    │   │   └── entry.py           # data model for a bill/discrepancy row
    │   ├── storage/
    │   │   └── db.py              # persistence layer (SQLite for MVP)
    │   └── core/
    │       └── config.py
    ├── data/
    │   └── uploads/                # stored images
    └── requirements.txt

## 4. Data flow

    [image upload] -> [FastAPI /upload] -> [OCR extraction]
        -> [structured row created] -> [stored in DB]
        -> [/entries returns table data] -> [frontend renders table]
        -> [/export returns CSV of current table/filtered view]

## 5. Division-to-code mapping
| Division | Code location |
|---|---|
| 1. Image input + extraction | `app/api/upload.py`, `app/extraction/ocr.py` |
| 2. Table / discrepancy data | `app/models/entry.py`, `app/api/entries.py`, `app/storage/db.py` |
| 3. CSV export | `app/api/export.py` |

## 6. Open decisions (resolve and move into decisions.md)
- How ticket number / restaurant are identified from extracted text
  (regex? fixed template per restaurant? manual entry fallback?)

## 7. Resolved decisions
- OCR engine/service choice: Selected Tesseract OCR (recorded in decisions.md)
- Storage layer: Selected SQLite for MVP (simple, file-based, sufficient)
- Text parsing approach: Selected regex/keyword matching (extract ticket # and discrepancy type)
- CSV export functionality: Selected GET /export endpoint with filtering support (restaurant, ticket_number)
- CSV image representation: Selected to export stored image filename/path instead of thumbnail
- Entry model: Added extra_fields (dict) for capturing unexpected bill fields, image_filename for CSV export reference
- Status values: Expanded to matched, needs_description, needs_ticket_number, needs_restaurant, needs_discrepancy_type, needs_review
- Parsing strategy: Retained regex/rule-based over LLM; multiple patterns with graceful degradation for schema flexibility