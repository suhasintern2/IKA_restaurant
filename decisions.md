# DECISIONS.md — locked decisions
 
> Source of truth. If any other doc disagrees with the file, the other doc
> is wrong and needs fixing. Every row here must be reflected in every spec
> it affects (mvp_spec / architecture / frontend_spec) in the same session
> it's added.
 
| Date | Decision | Reason | Files updated |
|------|----------|--------|----------------|
| —    | —        | —      | — |
| 2026-09-18 | Use Tesseract OCR for text extraction | Open-source, offline-capable, suitable for messy phone photos, no API costs | mvp_spec.md, architecture.md |
| 2026-09-18 | Use SQLite for storage layer | Simple, file-based, zero-configuration, sufficient for MVP | architecture.md, decisions.md |
| 2026-09-18 | Parse extracted text using regex/keyword matching | Extract ticket number (6+ digits) and discrepancy type (void/discount/promotion keywords); restaurant and description left for user input | architecture.md, decisions.md |
| 2026-09-18 | Export image filename/path in CSV (instead of thumbnail) | Thumbnail cannot be exported to CSV; filename/path allows referencing original image | architecture.md, decisions.md |
| 2026-09-18 | Enhanced field parsing with schema flexibility | Improved restaurant name extraction (first lines), ticket number (multiple patterns), description extraction, and extra_fields capture for unexpected bill fields | app/models/entry.py, app/api/upload.py, app/storage/db.py, app/api/entries.py |
| 2026-09-18 | Added extra_fields to Entry model | Capture unexpected bill fields (Table, Staff, Terminal, etc.) in a generic key/value bucket rather than discarding them | app/models/entry.py, app/storage/db.py, app/api/entries.py |
| 2026-09-18 | Added image_filename to Entry model | Store uploaded image filename with each entry for CSV export reference | app/models/entry.py, app/storage/db.py, app/api/upload.py, app/api/entries.py, app/api/export.py |
| 2026-09-18 | Enhanced status values for granular missing-field tracking | Added statuses: needs_ticket_number, needs_restaurant, needs_discrepancy_type, needs_review (in addition to matched, needs_description) for precise operator guidance | app/models/entry.py, app/api/upload.py, mvp_spec.md, frontend_spec.md |
| 2026-09-18 | Regex/rule-based parsing retained over LLM | Bills have semi-structured layouts; rule-based with multiple patterns and graceful degradation is sufficient for MVP and avoids external dependencies | decisions.md |