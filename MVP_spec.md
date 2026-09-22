# MVP SPEC — TIL SYSTEM

## 1. Problem
Three restaurants send images of their bills. Each bill may contain a
discrepancy of one of three types:
- **Void**
- **Discount**
- **Promotion**

An operator works in a separate custom app that has tickets (by ticket
number). To check out a void/discount/promo on a ticket, the operator needs
to find the matching bill image sent by the restaurant. Today that search is
manual. Some images arrive with no description, in which case the operator
must be prompted to supply one before it's usable.

## 2. What this system does (MVP scope)
1. **Accept bill images as input** (single upload or a batch of up to 30 images).
2. **Extract all text from each image** (OCR / text extraction).
3. **Build two dedicated structured datasets** from the extracted data.
   Tickets use `ticket_id` and a related `ticket_items` sub-table containing
   `item`, `category`, `price`, `qty`, `total`, and `is_void`; ticket scalar
   fields are date, terminal, table, department, user, payment_status,
   credit_card, ticket_total, grand_total, and charged. Dockets use
   `order_number`, marker-adjacent `item`, `discrepancy_type`, and handwriting-
   only `description`. Missing values are null and unknown labels go to
   `extra_fields`; OCR audit text is never a parsed display field. No shared
   ticket/docket display table is used.
4. **Export the table to CSV** via a button.

> Extraction detail (v4, see decisions.md): Tesseract `--oem 3 --psm 6`
> over a preprocessed image (grayscale, upscaling, autocontrast, OSD deskew
> only when the orientation confidence is >= 5.0). The OCR text is then split
> into blocks; `discrepancy_type` comes from line-item markers only, and a
> marker that cannot be confidently bound to a line item flags the row
> `needs_review` instead of guessing. Every parsed-value fix is recorded in
> the block's `corrections` list for auditability.

## 3. Explicitly out of scope for MVP
- Automated tests (see rules.md)
- Multi-user auth / roles
- Automated deployment pipeline
- Editing/annotating the image itself
- Any UI polish beyond "professional and usable" (frontend_spec.md governs the bar)
- Direct integration with the custom app's API (searching happens by the
  operator using ticket number as the lookup key — not a live sync, unless
  later decided otherwise in decisions.md)

## 4. Actors
- **Restaurant owner** — sends bill image (no system access assumed for MVP)
- **Operator** — uploads images, reviews extracted table, supplies missing
  descriptions, exports CSV
- **(Separate) UI developer** — builds frontend against `frontend_spec.md`

## 5. Core flow
1. Operator uploads ticket screenshots or docket images through their
  dedicated bulk control.
2. Backend extracts and persists structured rows in the matching dataset.
3. The upload result remains visible; parsed data stays collapsed until its
  dataset's **Show data** button is clicked.
4. Operator expands ticket items or reviews docket marker/handwriting fields.
5. Operator exports through the matching dedicated CSV endpoint.

## 6. Tech stack
- **Backend:** FastAPI (owns extraction — this is the core/hard part)
- **Frontend:** built separately by teammate, per `frontend_spec.md`
- **Extraction:** OCR method TBD — record the chosen library/service in
  `decisions.md` once picked (e.g. Tesseract, cloud OCR API, etc.)
- **Storage:** TBD for MVP — likely flat file/SQLite is enough; record choice
  in `decisions.md`

## 7. Ticket screenshot upload
`POST /api/upload/tickets` accepts up to 30 ticket screenshots in multipart
field `files`. Each image is OCR-parsed for the observed `#YYMMDD-N` Ticket ID,
known ticket metadata, item rows, and void markers. Missing fields are allowed;
unrecognized labeled fields are captured in `extra_fields`.

Screenshots are merged into one SQLite ticket record by normalized Ticket ID.
Items are appended only when item name, quantity, and unit price are new.
Populated scalar fields are preserved when later screenshots are blank, and
voided items are stored with `is_void: true`. Each screenshot remains recorded
as provenance. Failures are returned per image without stopping the batch.
Ticket screenshots detected in the generic image upload path are redirected to
this same ticket pipeline before bill parsing; they never create an `entries`
row. The complete ID string, including its hyphen (for example `260920-143`),
is retained as the ticket identifier.

## 8. Docket upload
`POST /api/upload/dockets` accepts up to 30 docket images in multipart field
`files`. Each stored docket has `docket_order_no`, `docket_date`,
`docket_time`, `item`, printed `discrepancy_type`, and a separate
`handwritten_reason`. Unknown labeled printed fields are stored in
`extra_fields`, while `printed_text` and `raw_text` remain available for audit.

`docket_order_no` is only a weak partial match key for the trailing integer in
a ticket ID; it is never converted into or stored as a full Ticket ID. The
docket date and time are captured for later tie-breaking. If one image appears
to contain multiple order numbers, or the parser cannot isolate an order and
discrepancy marker, the record is stored with `review_required: true` rather
than guessing the intended docket.

## 9. Void reconciliation
`GET /api/reconcile/voids` returns `{rows, summary}`. Each row contains one
voided ticket item, its trailing order number, a selected docket when uniquely
matched, all `docket_candidates` when a collision remains ambiguous, a
`status` of `matched`, `needs_review`, or `unmatched`, and a stable
`row_position`. Rows sort matched pairs first, then review rows, then
unmatched voids. Date matching may resolve a collision only when exactly one
docket date matches the ticket date; otherwise all candidates remain visible.

`GET /api/reconcile/voids/export` emits the same rows in the same
`row_position` order, including ticket item, docket reason, and candidate IDs.

## 10. Changelog
> Every change to scope, flow, or fields gets a dated entry here. Keep it in
> sync with `decisions.md`.

| Date | Change | Reason |
|------|--------|--------|
| —    | Initial spec created | — |
| 2026-09-18 | Selected Tesseract OCR for text extraction | Open-source, offline-capable, suitable for messy phone photos, no API costs |
| 2026-09-18 | Selected SQLite for storage layer | Simple, file-based, zero-configuration, sufficient for MVP |
| 2026-09-18 | Selected regex/keyword matching for text parsing | Extract ticket number (6+ digits) and discrepancy type (void/discount/promotion keywords); restaurant and description left for user input |
| 2026-09-18 | Added CSV export functionality with filtering support | Exports filtered/same view as /entries endpoint; exports image filename/path instead of thumbnail |
| 2026-09-18 | Export image filename/path in CSV (instead of thumbnail) | Thumbnail cannot be exported to CSV; filename/path allows referencing original image |
| 2026-09-18 | Enhanced field parsing with schema flexibility | Improved restaurant name extraction, ticket number detection, description extraction, and extra_fields capture for unexpected bill fields |
| 2026-09-18 | Added extra_fields to Entry model | Capture unexpected bill fields (Table, Staff, Terminal, Staff, Terminal, etc.) in a generic key/value bucket rather than discarding them |
| 2026-09-18 | Enhanced status handling | Added statuses for specific missing field scenarios: needs_ticket_number, needs_restaurant, needs_discrepancy_type, needs_review |
| 2026-09-18 | Added image_filename to Entry model | Store uploaded image filename with each entry for CSV export reference |
| 2026-09-18 | Retained regex/rule-based parsing over LLM | Bills have semi-structured layouts; rule-based with multiple patterns and graceful degradation is sufficient for MVP and avoids external dependencies |
| 2026-09-21 | OCR preprocessing + block segmentation | Per-entry structured `blocks` (header / line_items / discrepancies / totals / payment) persisted as JSON; auditable value corrections; `discrepancy_type` from line-item markers only; low-confidence markers -> `needs_review` |
| 2026-09-21 | OSD deskew gated on confidence >= 5.0 | Dense numeric tables spuriously report 180° rotation at low confidence and get garbled |
| 2026-09-21 | Status precedence: restaurant > ticket > discrepancy_type > review > description > matched | Review of unbound markers beats "matched"; never guess |
| 2026-09-21 | Added synchronous bulk image upload via `POST /upload/bulk`, capped at 30 images with per-image failure reporting | Supports 20-30 WhatsApp bill images while preserving the existing `/upload` contract |
| 2026-09-21 | Added Division 4c ticket-to-image reconciliation with ticket-level `Matched` / `Missing` / `Needs Review`, match confidence, handwritten note capture, and operator-facing reason validity | This task consumes ticket records and image entries together; it must surface uncertainty explicitly instead of silently auto-approving |
| 2026-09-21 | Added bulk ticket screenshot upload and merge-by-Ticket-ID storage | Ticket PDFs omit voided item details; multiple app screenshots must build one complete ticket without duplicate records |
| 2026-09-21 | Added bulk docket upload with separate printed fields and handwritten reason | Dockets provide only a weak trailing order number and must retain ambiguity for Division 5c review |
| 2026-09-21 | Added void reconciliation with aligned matched/unmatched rows and ordered CSV export | Operators need to review voided ticket items beside docket explanations without hiding missing or colliding weak-key matches |
| 2026-09-21 | Added parsed ticket/docket read tables and dedicated CSV exports | Uploaded OCR data must be visible as structured ticket and docket records rather than remaining only in upload responses or SQLite |
| 2026-09-21 | Enforced ticket/bill pipeline separation and exact hyphenated Ticket ID storage | Ticket screenshots were being misclassified as bill images and losing the second Ticket ID segment |
| 2026-09-22 | Finalized strict ticket/docket fields, dedicated upload boundaries, read-back verification, and separate table rendering | Uploads must produce immediately queryable structured rows without cross-contamination or raw-text display blobs |