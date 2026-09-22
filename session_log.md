# SESSION_LOG.md

> that's what lets a brand-new session (with zero memory) understand exactly
> where things left off, just by reading CONTEXT.md -> this file.
---

## Session 21 — 2026-09-22
**Planned changes:**
- Reset all ticket, ticket-item, docket, and generic entry data.
- Remove generated upload artifacts while preserving the ticket and docket
  fixture images for the next manual test.
- Verify all application record counts are zero.

**Achieved:**
- Cleared `entries`, `ticket_records`, `ticket_items`, and `docket_records`.
- Removed 3 generated upload files.
- Preserved `ticket.png` and `docket.jpeg` fixtures.
- Verified all application record counts are zero.


## Session 22 — 2026-09-22
**Planned changes:**
- Push existing frontend code to the frontend branch without making any code changes
- Follow the rules: push frontend code to the frentend branch

**Achieved:**
- Pushed frontend code to origin/frontend branch (commit 713777b)
- No code changes were made as requested
- Frontend/App.jsx, frontend/App.css, and requirements.txt were pushed


## Session 20 — 2026-09-22
**Planned changes:**
- Clear all stored ticket, ticket-item, docket, and generic entry records.
- Remove generated uploaded files while preserving the checked-in fixture
  samples needed for the user's bulk-upload test.
- Verify the database starts with zero application records. No automated tests.

**Achieved:**
- Cleared `entries`, `ticket_records`, `ticket_items`, and `docket_records`.
- Removed 19 generated ticket/docket upload files.
- Preserved `data/uploads/ticket_screenshots/ticket.png` and
  `data/uploads/dockets/docket.jpeg` as bulk-test fixtures.
- Verified all application record counts are zero. No automated tests were
  added or run.


## Session 19 — 2026-09-22
**Planned changes:**
- Fix the docket upload Show data control so it opens the docket dataset after
  a successful upload regardless of the previously active view.
- Verify the docket fields are rendered from the current API names and run a
  focused frontend validation. Do not add or run automated tests.

**Achieved:**
- Fixed docket upload completion to select the Dockets view after refreshing
  the saved records.
- Fixed the docket Show data button to select the Dockets view before toggling
  the table, so it no longer tries to reveal docket data inside the Tickets
  view.
- Frontend lint/build passed; only the existing two React effect warnings
  remain. No automated tests were added or run.


## Session 18 — 2026-09-22
**Planned changes:**
- Make the complete hyphenated ticket ID the most prominent ticket-table
  field, with no truncation or fallback display.
- Persist and expose the upload timestamp for ticket screenshots, and show it
  in the ticket records UI.
- Update the affected schema/API/UI documentation and manually verify the
  existing real ticket row. Do not add or run automated tests.

**Achieved:**
- Fixed the ticket table to use the complete hyphenated `ticket_id`, including
  `260920-143`, as its prominent primary field.
- Added `uploaded_at` to `/api/tickets` and a visible Uploaded column showing
  the latest screenshot upload/merge time.
- Verified the running API returned `ticket_id: 260920-143` and
  `uploaded_at: 2026-09-22 09:35:04` for the real ticket row.
- Frontend lint/build passed with only the existing two React effect warnings;
  no automated tests were added or run.


## Session 17 — 2026-09-22
**Planned changes:**
  image data before beginning the new validation run; do not migrate old rows.
  item sub-table, and align the docket schema to `order_number`, marker type,
  marker-adjacent item, handwriting-only description, and `extra_fields`.
  remain hidden until explicitly opened, with ticket items shown as nested
  sub-rows.
  update the project specifications, decisions, status, and this log.
  not add or run automated tests.


**Planned changes:**
  endpoints, and frontend tables against the required field contracts.
  hyphenated ticket number is preserved, printed docket text stays separate
  from handwritten reason, and unknown labels land in `extra_fields`.
  immediate GET retrieval from the matching dedicated endpoint; prevent any
  ticket/docket cross-contamination with the generic entries table.
- Update the frontend to render the exact dedicated ticket and docket column
  sets and refresh the correct table after upload.
  specs/decisions/status, and record the acceptance checks achieved. Do not
  add or run automated tests.

**Achieved:**
- Fixed the dedicated ticket upload rejection: it now checks the parser's
  `ticket_number` field and preserves `260920-143` as one hyphenated value.
- Tightened docket parsing for the real sample: order/date/time, printed void
  marker, item candidate, handwriting-only candidate, and unknown labeled
  fields are stored separately. Added read-back checks after both inserts.
- Generic non-ticket uploads now fail closed rather than creating docket rows;
  generic ticket detection still merges into `ticket_records`.
- Removed the generic entries upload/table from the frontend. Tickets now use
  the exact requested 13 columns with one row per ticket and a flattened Items
  cell; Dockets use the exact requested six columns.
- Manually uploaded real `ticket.png` through `/api/upload/tickets` and
  `/api/upload`, and real `docket.jpeg` through `/api/upload/dockets`.
  Verified success responses, immediate `/api/tickets` and `/api/dockets`
  retrieval, exact `#260920-143`, separate docket fields, and `/api/entries`
  remained empty. SQLite counts were `entries=0`, `ticket_records=2`, and
  `docket_records=3` before removing no user data. The two older docket rows
  predated this parser pass and remain visible for review.
- Updated `mvp_spec.md`, `architecture.md`, `frontend_spec.md`,
  `decisions.md`, and `CONTEXT.md`. No automated tests were added or run;
  backend compile and frontend lint/build validation passed.



### Session N — YYYY-MM-DD
-
**Achieved (write this AFTER the session, even if it differs from planned):**
- Added per-image upload feedback with uploading, success, and error states.

## Session 11 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Add `GET /api/reconcile/voids` returning aligned reconciliation rows for
  every voided ticket item and its docket candidates.
- Match only by docket order number against trailing Ticket ID digits; use
  ticket/docket dates as a tie-breaker and surface all unresolved candidates
  as `needs_review`.
- Sort matched rows first, preserve unmatched voids as visible `unmatched`
  rows, and expose the same order through a reconciliation CSV endpoint.
- Add a frontend Voids view with aligned ticket/docket columns and distinct
  matched, unmatched, and needs-review states.
- Update all affected specifications and leave real-data/collision validation
  for manual testing; do not run tests.

**Achieved:**
- Added `GET /api/reconcile/voids` to build aligned rows from voided ticket
  items and docket records, using trailing order numbers only.
- Added date tie-breaking, all-candidate collision output with `needs_review`,
  explicit `unmatched` rows, matched-first sorting, and stable row positions.
- Added `/api/reconcile/voids/export` using the same builder and ordering.
- Added the frontend Voids view and ordered export action; updated all affected
  docs. No tests or real-data validation were run.

**Decisions locked this session:**
- Backend owns matching, ordering, and CSV alignment.
- Docket date resolves a collision only when exactly one candidate matches.
- Unresolved collisions and missing dockets remain visible, never auto-resolved.

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md
- [x] session_log.md

**Next session:**
- Manually validate aligned rows with a real void ticket/docket set and a
  deliberate trailing-number collision.

## Session 12 — 2026-09-21
**Planned changes:**
- Replace the obsolete ticket PDF upload UI/API path with ticket screenshot
  upload using `POST /api/upload/tickets`.
- Remove legacy PDF-only backend routes and clear existing application data,
  uploaded files, and CSV files.

**Achieved:**
- Ticket upload UI now accepts image screenshots and calls
  `/api/upload/tickets`; PDF wording and the legacy PDF route were removed.
- Cleared `entries`, `ticket_records`, and `docket_records`, removed all
  uploaded files, and removed all CSV files. Database schema was preserved.

**Next session:**
- Manually upload fresh ticket screenshots and dockets for validation.

## Session 13 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Add read-only ticket and docket list endpoints because the current API only
  exposes uploads and the void reconciliation result, leaving parsed fields
  invisible to the frontend.
- Add CSV exports for the parsed ticket and docket tables with stable backend
  ordering.
- Replace the single workspace toggle with visible Tickets, Dockets, and Voids
  views; render the full ticket and docket column sets from their real fields.
- Keep Voids powered by `GET /api/reconcile/voids`, preserving backend row
  order and the existing reconciled export.
- Update frontend_spec.md, decisions.md, CONTEXT.md, and this log. Do not run
  automated tests; manual validation remains the user's responsibility.

**Achieved:**
- Added `/api/tickets` and `/api/dockets` read endpoints returning stored
  parsed fields, plus `/api/tickets/export` and `/api/dockets/export` CSVs.
- Added visible Tickets and Dockets tables with their distinct column sets;
  ticket rows flatten merged item arrays and void items are visually marked.
- Added separate Voids tally navigation using `/api/reconcile/voids`, while
  keeping backend row ordering and reconciled CSV export authoritative.
- Refreshes parsed tables after upload so extracted data appears immediately.
- Updated frontend_spec.md, decisions.md, CONTEXT.md, and this log. No tests
  or manual data validation were run.

**Decisions locked this session:**
- Tickets and Dockets are separate views and schemas.
- Parsed item data is exported from dedicated backend CSV endpoints.
- Voids matching and ordering remain backend-owned.

**Docs updated this session:**
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md
- [x] session_log.md

**Next session:**
- Upload real ticket screenshots and dockets, then inspect parsed fields in the
  Tickets and Dockets views and verify all three CSV downloads.

## Hotfix — 2026-09-21
**Planned changes:**
- Fix the ticket screenshot parser failure caused by the undefined `LABEL_RE`
  symbol and make per-image parse failures visible in the backend log.

**Achieved:**
- Defined `LABEL_RE` in `app/models/ticket.py`.
- Added traceback logging for ticket screenshot failures in `app/api/upload.py`.
- The bulk response continues to return the original filename and failure
  reason so the frontend can display the error per image.
- No tests were run.
- Removed non-MVP summary metrics from the dashboard.
- Documented the unresolved API response assumptions and export behavior in frontend_spec.md.
- Updated CONTEXT.md to show the actual frontend MVP status.
- Validated with npm run build and npm run lint; build passed and lint reports only the existing setState-in-effect warning.
- Export CSV currently downloads the backend dataset because filtered export parameters are undocumented.

- [ ] mvp_spec.md
- [ ] architecture.md
- [x] frontend_spec.md
- [x] decisions.md

- Confirm the real backend upload payload/response shape, canonical restaurant names, and whether `/export` supports filtered results.
## Session 3 — 2026-09-21
- Complete the frontend MVP process requirements and document the work.
- Add per-image upload progress and success/failure feedback.
- Update the project current status and finish the session achievement entry.
**Achieved (write this AFTER the session, even if it differs from planned):**
-

**Decisions locked this session (must also be in decisions.md):**

**Docs updated this session:**
- [ ] architecture.md
- [ ] frontend_spec.md
---

**Planned changes (write this BEFORE touching code):**
- Build a dedicated `frontend/src/api/` client layer: `client.js` (base fetch
  wrapper), `entries.js` (`getEntries`, `updateEntry`), `upload.js`
  (`uploadImages`), `export.js` (`exportCsv`). Strip the leftover TypeScript
  syntax from these `.js` files (it breaks the build).
- Point all endpoints at the real backend paths. Verified from source:
  routes live under the `/api` prefix; `/upload` takes a single multipart
  field named `file` (not `files`); responses have no `thumbnail` field.
- Fix the BASE_URL to `/api` and add the matching Vite dev-server proxy so
  the browser can reach the backend without CORS changes.
- Wire App.jsx to the API client: server-filtered `getEntries` (restaurant +
  ticket_number query params), per-image upload via `uploadImages`, PATCH
  description via `updateEntry`, filtered CSV export via `exportCsv`.
- Replace the placeholder/mock behavior:
  - Restaurant filter options derived from data returned by `/entries`
    (placeholders only as empty-state fallback).
  - Thumbnail column renders the stored `image_filename` (backend does not
    serve image bytes), since backend has no `thumbnail` field.
  - Surface `extra_fields` minimally under the Description cell.
  - Render real backend statuses verbatim (`matched`, `needs_description`,
    `needs_ticket_number`, `needs_restaurant`, `needs_discrepancy_type`,
    `needs_review`) with proper visual treatment.
- Manual test against the running backend: upload, table render, description
  PATCH, restaurant filter, ticket search, CSV export.
- Update docs: decisions.md (thumbnail/image_filename surface decision,
  upload field name correction, filter-sourced restaurant options, export
  filtering now confirmed), frontend_spec.md section 4 (finalize API
  contract), and CONTEXT.md status.

**Achieved (write this AFTER the session, even if it differs from planned):**
- Built `frontend/src/api/`: `client.js` (`/api` BASE_URL, JSON + error
  handling, FormData support), `entries.js` (`getEntries`, `updateEntry`),
  `upload.js` (`uploadImages`, sending one POST per image in the singular
  `file` field), `export.js` (`exportCsv`, blob download). Removed the
  TypeScript syntax that was breaking the build in the `.js` files.
- Added the Vite dev-server proxy `/api` → `http://localhost:8000`.
- Wired App.jsx end-to-end: server-filtered entries (debounced, race
  guarded), per-image upload states then a table refresh, description PATCH,
  and CSV export of the currently filtered view.
- Corrected mocked behavior to the real backend: restaurant options derived
  from `/entries` data (placeholders only while empty), Image column shows
  `image_filename`, `extra_fields` surfaced under Description, backend
  statuses rendered verbatim with per-status styling.
- Verified every endpoint against the live backend on :8000: `/api/entries`
  (incl. restaurant + ticket_number exact-match filters), `/api/upload`
  (confirmed field must be `file` — `files` returns 422; confirmed response
  shape incl. `entry_id` + `parsed_data` without status), `PATCH
  /api/entries/{id}` (description update + 404 on missing id), `/api/export`
  (CSV download, filtered variant returns only matching rows).
- `npm run lint` clean; `npm run build` passes.

**Decisions locked this session (must also be in decisions.md):**
- All backend routes live under `/api`; Vite dev proxy bridges to
  `http://localhost:8000` (no CORS on backend).
- `/upload` multipart field is singular `file`, one image per request.
- Restaurant filter options derive from `/entries` data; placeholders show
  only while the table is empty.
- `/export` supports the same `restaurant`/`ticket_number` filters as
  `/entries`; the UI exports the current filtered view.
- Backend has no `thumbnail` and serves no image bytes; Image column shows
  `image_filename`; `extra_fields` rendered under Description.
- Frontend renders the six backend statuses verbatim.

**Docs updated this session:**
- [ ] mvp_spec.md
- [ ] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- Backend extraction accuracy + block segmentation (plane — this is the
  current task session).

---

## Session 5 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Baseline current extraction accuracy against every sample image in
  `data/uploads/` (each restaurant + the VOID-bearing Ay Be Spice receipts),
  recording which rows segment correctly today.
- `app/extraction/ocr.py`: add pre-processing (grayscale, autocontrast,
  upscaling of small/dim phone photos, OSD-based deskew) and evaluate
  Tesseract PSM tuning vs the current `--psm 6`; log the OCR-engine/PSM
  decision in decisions.md.
- `app/models/entry.py`: add an auditable post-processing step for common OCR
  misreads (n↔decimal point, O↔0, l↔1, comma↔dot decimals) applied only in
  controlled numeric contexts, with each correction recorded so no guess is
  invisible.
- Block segmentation: separate the extracted text into header / metadata /
  line items / discrepancy markers / totals / payment blocks. Each line item
  becomes a record (name, quantity, unit price, line total).
- Item-level discrepancy association: bind each void/discount/promotion
  marker to the line item it applies to (position/proximity within the block);
  if association cannot be made confidently, leave it unbound and let status
  become `needs_review` instead of guessing.
- Persist the structured blocks on the entry (new `blocks` column, JSON),
  keep the raw `extracted_text` for auditability, keep `extra_fields` as the
  bucket for unrecognized fields. `Entry` model gains `blocks`; `entries.py`
  deserializes it (additive contract change — frontend ignores new fields).
  `/upload`, `/entries`, `/export` route paths, params, and response field
  semantics stay unchanged.
- Manual validation against multiple sample bills (several restaurants /
  layouts, at least one marker mid-bill on a non-final line item); ask the
  user for more sample images if coverage is too thin.
- Docs: decisions.md (OCR tuning decision, correction-logging approach,
  segmentation strategy, `blocks` schema), mvp_spec.md section 2,
  architecture.md extraction module description, frontend_spec.md if the
  `/entries` response shape changed, CONTEXT.md status.

**Achieved (write this AFTER the session, even if it differs from planned):**
- Baseline OCR recorded for every sample in `data/uploads/` (Spice Haven
  receipt, two Ay Be Spice VOID receipts, the sales/income report, and the
  synthetic VOID test bill).
- `app/extraction/ocr.py`: rewrote preprocessing as grayscale → 2x LANCZOS
  upscale when max(w,h) < 1400 → autocontrast(cutoff=1) → OSD deskew; kept
  Tesseract `--oem 3 --psm 6`. OSD rotation is now applied ONLY when
  Orientation confidence >= 5.0 — the sales report (a dense numeric table)
  spuriously reported `Rotate: 180` at confidence 3.03 and rotating it
  produced reversed garbage (verified by reproducing it).
- `app/models/segmentation.py` (new): BillSegmenter splits the OCR blob into
  blocks — header / metadata / line_items / discrepancies / totals / payment /
  footer / extra_lines / corrections. Items get name, quantity, unit_price,
  line_total; prices are parsed only from the text AFTER the qty marker so OCR
  junk digits before "1 x" can't leak in; all value fixes are auditable via
  `parse_amount` + `corrections`.
- Fixed during validation: PHONE_RE is now 3+ leading digits (a decimal like
  "14.00" is no longer a "phone" that swallows item lines); metadata
  separator class gained `;` (Date;) ; terminal extraction no longer mangles
  "POS-01" into "P0S-01"; totals parse amounts AFTER their keyword (junk
  prefix digits ignored) and VAT lines skip the parenthesized percentage;
  summary totals (Voids/Discounts/Promotions Total) are classified before the
  generic total so they never fill the bill-total slot; `_clean_name` strips
  underscores and truncates glued-on prices.
- Item-level discrepancy association: each marker binds to the nearest
  preceding item end line; `high` confidence when gap <= 2 lines and the
  marker amount (when present) matches the item line_total, otherwise `low`.
- Pipeline wiring: `parse_extracted_text` now adds `blocks` / `line_items` /
  `discrepancies` and derives `discrepancy_type` from line-item markers ONLY
  (never from summary lines); `Entry` model gains `blocks`; `db.py` stores a
  `blocks` JSON column (idempotent ALTER) and saves/loads it; `entries.py`
  deserializes it via a shared `_row_to_entry`; `upload.py` persists blocks,
  derives status from the new precedence
  (restaurant > ticket > discrepancy_type > discrepancy-review >
  description > matched) so a low-confidence marker yields `needs_review`,
  and keeps the `/upload` `parsed_data` response whitelisted to the original
  5 fields.
- Live API validation on the restarted backend (:8000):
  - Spice Haven receipt → `matched`, 3 items (Chicken Tikka Masala 12.50,
    Garlic Naan 4.50, Mango Lassi 3.95), VOID bound HIGH-confidence to Garlic
    Naan, subtotal 13.05 / VAT 2.61 / total 15.66, Card/Visa/**1897,
    metadata incl. table 5, staff Ravi, terminal POS-01.
  - Ay Be Spice VOID receipt → `needs_review` (VOID marker amount 1.50 doesn't
    match the preceding item, so association is unbound / low).
  - Sales report → `needs_ticket_number`, 0 items, discrepancy `unknown`
    (only summary totals extracted).
  - Synthetic VOID bill → `needs_review` (marker with no preceding item).
- `/api/export` and `/api/entries` re-verified after the schema change;
  existing rows (id 1-5) keep their stored values (old rows not re-parsed).
  Backend recompiled cleanly; frontend untouched (oxlint clean, build passed).
- Validation rows 6-9 created during testing were deleted to keep the DB tidy.

**Decisions locked this session (must also be in decisions.md):**
- OCR stays `--oem 3 --psm 6` (line-oriented) with preprocessing
  (grayscale/upscale/autocontrast); OSD rotation trusted only at confidence >= 5.0.
- Every OCR/correction to a parsed value is recorded in `corrections`; no
  "fixed" number is silent.
- `discrepancy_type` for an entry comes from line-item markers only; summary
  totals ("Voids Total" etc.) go to the totals block, not markers/type.
- Discrepancy→item association: nearest preceding item, gap<=2 + amount match
  = high; otherwise low → status `needs_review` (never guess).
- Status precedence: needs_restaurant > needs_ticket_number >
  needs_discrepancy_type > needs_review > needs_description > matched.
- Structured blocks persist in a new additive `blocks` JSON column; `/upload`
  response `parsed_data` stays the original 5 fields.

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- Broader validation: real bills from all three restaurants (incl. mid-bill
  markers, discounts, promotions, multi-item bills) to harden item parsing
  and association; consider feeding the segmenter OCR from `--psm 4`
  layouts if line-oriented receipts still garble.

## Session 6 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Preserve the existing synchronous `POST /api/upload` contract.
- Add synchronous `POST /api/upload/bulk` accepting up to 30 image files and
  process each file through the existing save -> OCR -> parse -> persist
  pipeline.
- Return per-image successes and failures so a corrupt image does not prevent
  other images from being stored; include each failed filename and reason.
- Update architecture, frontend API documentation, decisions, and current
  status to describe the additive bulk endpoint and synchronous behavior.
- Manually validate the endpoint with a real 20-30 image batch including one
  corrupt image, without adding or running automated tests.

**Achieved (write this AFTER the session, even if it differs from planned):**
- Refactored the existing single-image processing sequence into a shared
  per-file helper without changing the `POST /api/upload` response contract.
- Added synchronous `POST /api/upload/bulk` with up to 30 `files`, independent
  per-image success/failure handling, and filename/reason failure details.
- Updated `mvp_spec.md`, `architecture.md`, `frontend_spec.md`,
  `decisions.md`, and `CONTEXT.md` for the new endpoint and sync behavior.
- Ran a Python syntax check only; automated tests and the real 20-30 image
  manual batch were not run per instruction and remain for user validation.

**Decisions locked this session (must also be in decisions.md):**
- Preserve `/api/upload` and add `/api/upload/bulk` for batch requests.
- Process bulk uploads synchronously through the existing per-image pipeline.

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- Manually send 20-30 images, including one corrupt image, to
  `POST /api/upload/bulk` and verify partial failure behavior.

## Session 7 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Inspect the real Division 4a ticket records and Division 4b image entries
  supplied for this task before choosing matching keys or fallback thresholds.
- Build ticket-to-entry reconciliation with explicit `Matched`, `Missing`,
  and `Needs Review` ticket-level statuses and surfaced confidence/evidence.
- Add handwritten-note extraction as a distinct field after matching is
  defined, using an approach selected from the supplied real samples.
- Add an operator-reviewable reason assessment with `reason_provided`,
  `issue_addressed`, and evidence; do not auto-approve discrepancies.
- Manually validate end-to-end against the supplied real samples, including
  at least one handwritten note and one image without a note. Do not add or
  run automated tests.
- Update mvp_spec.md, architecture.md, frontend_spec.md, decisions.md,
  CONTEXT.md, and this session entry with the final contracts and decisions.

**Achieved (write this AFTER the session, even if it differs from planned):**
- Waiting for real Division 4a ticket records and Division 4b discrepancy
  images before implementing matching or reason assessment.

**Decisions locked this session (must also be in decisions.md):**
- None yet; matching and handwriting choices remain intentionally open until
  the real sample data is supplied.

**Docs updated this session:**
- [ ] mvp_spec.md
- [ ] architecture.md
- [ ] frontend_spec.md
- [ ] decisions.md
- [ ] CONTEXT.md "Current status"

**Next session should start with:**
- Use the user-supplied ticket batch and discrepancy-image batch to define the
  ticket schema, image fields, matching evidence, and handwriting approach.

## Session 8 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Add two distinct bulk upload flows in the UI: one for ticket PDFs and one
  for discrepancy docket images, with separate status cards and no shared
  upload logic.
- Extend the backend with bulk PDF upload and bulk image upload routes that
  accept a list of files, save them into their own folders, and return per-file
  success/failure results.
- Keep the existing single-image and bulk image pipeline intact; the new bulk
  ticket flow is intentionally separate and stores uploaded files for later
  parsing/export.
- Update the UI so each upload panel supports the max batch size the module
  can handle and keeps the result list visible for the operator.
- Validate the new routes via syntax check only; no automated tests.

**Achieved (write this AFTER the session, even if it differs from planned):**
-

**Decisions locked this session (must also be in decisions.md):**
-

**Docs updated this session:**
- [ ] frontend_spec.md
- [ ] architecture.md
- [ ] decisions.md
- [ ] session_log.md

**Next session should start with:**
- Manual upload of real ticket PDF batches and docket batches through the new
  two-panel UI, then verify saved filenames and partial failures.

---

## Session 1 — 2026-09-18
**Planned changes (write this BEFORE touching code):**
- Build the three screens (Upload, Table view, Description prompt) as per frontend_spec.md.
- Implement image upload, display extracted rows in a table with filtering and search.
- Handle states: empty, loading, error, needs description.
- Implement CSV export.

**Achieved (write this AFTER the session, even if it differs from planned):**
- Created the frontend React application with three screens: Upload, Table view, and Description prompt (modal).
- Implemented image upload via POST /upload endpoint.
- Fetched and displayed entries from GET /entries.
- Implemented filtering by restaurant and search by ticket number.
- Implemented visual flagging for entries needing description and opening a description prompt modal.
- Implemented saving description via PATCH /entries/{id}.
- Implemented CSV export via GET /export.
- Handled loading, error, and empty states.
- Beautified the UI with a refined color scheme, improved spacing, shadows, rounded corners, hover effects, and polished components (buttons, inputs, table, modal, upload area).
- Fixed JSX syntax error in the restaurant filter select, ensuring the frontend compiles without errors.

**Decisions locked this session (must also be in decisions.md):**
- None (used placeholder restaurant names; actual names should be obtained from backend or decisions.md)

**Docs updated this session:**
- [ ] mvp_spec.md
- [ ] architecture.md
- [ ] frontend_spec.md
- [ ] decisions.md
- [ ] CONTEXT.md "Current status"

**Next session should start with:**
- Test the frontend with the backend backend (once dependencies are installed and backend is running).
- Adjust API call shapes if necessary based on actual backend responses.

## Session 9 — 2026-09-21
**Planned changes:**
- Add `POST /api/upload/tickets` for bulk ticket screenshots with partial
  failure reporting.
- Parse flexible ticket fields, item rows, and void markers using existing OCR.
- Merge screenshots by normalized Ticket ID, dedupe items by item + quantity +
  price, preserve populated fields, and retain screenshot provenance.
- Update all affected specifications and leave real-sample validation manual.

**Achieved:**
- Added the bulk ticket screenshot endpoint and per-image success/failure
  responses.
- Added flexible ticket OCR parsing, SQLite `ticket_records` storage, merge by
  Ticket ID, item deduplication, field preservation, `is_void`, and provenance.
- Updated mvp_spec.md, architecture.md, frontend_spec.md, decisions.md, and
  CONTEXT.md. No automated tests or real-sample validation were run.

**Decisions locked:**
- Normalize `#YYMMDD-N` to `YYMMDD-N` for merging.
- Deduplicate by normalized item name + quantity + unit price.
- Never overwrite a populated scalar field with a later blank value.

**Next session:**
- Manually validate single screenshots, out-of-order multi-screenshot tickets,
  duplicate regions, void flags, and a batch containing one bad image.

## Session 10 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Add `POST /api/upload/dockets` for bulk discrepancy docket images with
  per-image partial-failure reporting.
- Parse printed docket fields separately from a best-effort handwritten reason;
  store `docket_order_no` as a weak trailing-order match key, never as a
  full Ticket ID.
- Capture docket date/time, item, and printed discrepancy marker, and flag
  images containing multiple order numbers for manual review rather than
  guessing the intended docket.
- Add dedicated SQLite docket storage and update the MVP, architecture,
  decisions, frontend contract, context, and session log.
- Do not run automated tests or real-sample validation; leave those checks for
  manual validation with real docket photographs.

**Achieved:**
- Added `POST /api/upload/dockets` with up to 30 images and per-image
  success/failure reporting.
- Added separate printed docket parsing and best-effort handwritten-reason
  extraction, with `docket_order_no` stored as a weak partial key.
- Added SQLite `docket_records` storage, date/time capture, discrepancy marker
  parsing, raw/printed OCR fields, and manual-review flags for ambiguous frames.
- Updated mvp_spec.md, architecture.md, frontend_spec.md, decisions.md,
  CONTEXT.md, and this session log. No tests or real-sample validation were run.

**Decisions locked this session:**
- A docket order number is never treated as a full Ticket ID.
- Multiple detected order numbers require manual review rather than guessing.
- Printed OCR and `handwritten_reason` remain separate fields.

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md
- [x] session_log.md

**Next session:**
- Manually upload a clear docket, a docket with difficult handwriting, and a
  photo containing multiple dockets; verify printed fields, handwritten_reason,
  weak order key, and manual-review flags.

---

## Session 2 — 2026-09-18
- Redesign the frontend with a professional, non-"AI-generated" look.
  success/failure reporting.
  extraction, with `docket_order_no` stored as a weak partial key.
- Added SQLite `docket_records` storage, date/time capture, discrepancy marker
- Updated mvp_spec.md, architecture.md, frontend_spec.md, decisions.md,
- Improve typography with a modern font stack and clear visual hierarchy.
- Add subtle animations and micro-interactions (hover states, transitions, focus states).
## Session 14 — 2026-09-21
**Planned changes:**
- Fix the parsed Tickets view showing no rows when uploads succeed but OCR
  produces an empty `items` array.
- Preserve item-name-only lines inside the ticket Items section when price
  columns are unreadable, while leaving numeric fields blank rather than
  inventing values.
- Render a metadata row for every stored ticket even when no item row can be
  recovered, so parsed ticket information is always visible.
- Do not run tests; manual re-upload and inspection remains required.

**Achieved:**
- Added structure detection before bill parsing so ticket screenshots uploaded
  through `/upload` or `/upload/bulk` route into `ticket_records` instead of
  `entries`.
- Preserved full hyphenated Ticket IDs and improved adjacent-label parsing for
  ticket metadata, totals, payment values, and item-name fallback rows.
- Refreshed the Tickets table after generic uploads and removed the confirmed
  leaked `Ticket #260920-143` bill entry and its image.
- Reparsing existing dedicated ticket OCR produced separate ticket records;
  updated the project specifications and decisions. No tests were run.

## Session 15 — 2026-09-21
**Planned changes (write this BEFORE touching code):**
- Ensure ticket screenshots never enter the bill/discrepancy `entries` table,
  even when submitted through the generic image upload route.
- Preserve the complete Ticket ID string including the hyphen and parse the
  screenshot's labeled metadata into the dedicated `ticket_records` table.
- Improve parsing for labels and values that OCR places on adjacent lines,
  without concatenating unrelated labels into Description.
- Refresh the Tickets table after both the dedicated ticket upload and any
  structure-detected ticket upload through the generic image box.
- Remove any existing leaked ticket rows from `entries`, update all affected
  docs, and do not run automated tests.

**Achieved:**
-

**Decisions locked this session:**
- Ticket structure detection routes to ticket storage before bill parsing.
- The full normalized Ticket ID remains one string in `ticket_records`.

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md
- [x] session_log.md

**Next session:**
- Manually upload the exact `260920-143` screenshot through both upload paths
  and confirm one ticket record, zero bill-entry leakage, and visible columns.

**Decisions locked this session (must also be in decisions.md):**
-

**Docs updated this session:**
- [ ] mvp_spec.md
- [ ] architecture.md
- [ ] frontend_spec.md
- [ ] decisions.md
- [ ] CONTEXT.md "Current status"

**Next session should start with:**
-
## Session 16 — 2026-09-21

**Planned changes (write this BEFORE touching code):
- Replace the current rule-based parsing in parse_ticket_screenshot, parse_docket_text, and parse_extracted_text with the master parsing prompt logic (ticket vs. docket detection and strict per-field JSON output).
- For ticket uploads, ensure extracted data populates the ticket-specific fields (ticket_number, restaurant, date, terminal, table, department, user, payment_status, credit_card_amount, items, ticket_total, grand_total, charged) and is saved to the ticket_records table.
- For docket uploads, ensure extracted data populates the docket-specific fields (docket_order_no, date, time, item, discrepancy_type, handwritten_reason) and is saved to the docket_records table.
- Ensure that the structured data is saved and visible immediately after upload (i.e., the row is queryable in the respective table).
- Update the upload.py and the respective model files to use the new parsing logic.
- Do not merge ticket and docket storage/tables.

**Achieved (write this AFTER the session, even if it differs from planned):
- 

**Decisions locked this session (must also be in decisions.md):
- 

**Docs updated this session:
- [ ] mvp_spec.md
- [ ] architecture.md
- [ ] frontend_spec.md
- [ ] decisions.md
- [ ] CON.md

