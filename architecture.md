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
- OCR engine/service choice
- Storage choice (SQLite vs flat JSON vs other)
- How ticket number / restaurant are identified from extracted text
  (regex? fixed template per restaurant? manual entry fallback?)