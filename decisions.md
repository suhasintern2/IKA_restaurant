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