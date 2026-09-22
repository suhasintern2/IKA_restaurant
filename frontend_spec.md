# FRONTEND SPEC — TIL SYSTEM

> This is the contract between backend and UI. If the backend changes a
> field name, endpoint, or flow, this file must be updated in the same
> session — don't let it drift from what the API actually returns.

## 1. Screens

### Screen 1 — Upload
- “Upload screenshots in bulk” control for ticket screenshots using `files`,
  with per-screenshot success/failure state and merged Ticket ID/item counts
  in the response
- Separate bulk docket image control using `files`, with per-image
  success/failure state and visible manual-review flags
- Shows upload progress / basic success-fail state per image
- On success, extracted rows appear in the table (Screen 2)

### Screen 2 — Parsed records
The header exposes separate `Tickets`, `Dockets`, and `Voids tally` views.
Parsed ticket and docket tables are collapsed by default after upload. Each
upload panel exposes a `Show data` button after a successful result; clicking
it reveals that dataset and toggles it closed again.

Tickets renders one row per parsed ticket from `/api/tickets`, with columns:
Ticket ID, Uploaded, Restaurant, Date, Terminal, Table, Department, User, Payment
Status, Credit Card Amount, Items, Ticket Total, Grand Total, and Charged.
The Items cell contains an expandable nested item table with item, category,
price, qty, total, and void marker. Ticket CSV export uses
`/api/tickets/export`.
Ticket screenshots uploaded through either ticket control or a structure-
detected generic image upload appear here immediately; they do not appear in
the legacy bill-image entries table. The Ticket Number column displays the
complete hyphenated value, such as `260920-143`.

Dockets renders `/api/dockets` separately, with columns: Order No, Date, Time,
Item, Discrepancy Type, and Handwritten Reason. The
order number is explicitly labelled as partial and never displayed as Ticket
ID. Review-flagged rows are visibly distinct. Docket CSV export uses
`/api/dockets/export`.

The legacy generic entries table is not rendered for ticket or docket data.

### Screen 3 (optional, only if needed for MVP) — Description prompt
- Simple modal/form: shows the image, lets operator type a description,
  saves back to the row.

### Screen 4 — Voids reconciliation
- A Voids view calls `GET /api/reconcile/voids` and renders two aligned
  columns: the voided ticket item on the left and docket evidence on the right.
- Each row shows `row_position`, Ticket ID, item name/quantity/price/total,
  docket order/date/time/item, and `handwritten_reason` when available.
- Rows with `status: matched` appear first. `needs_review` rows show every
  `docket_candidates` candidate and an explicit collision message. `unmatched`
  rows show an explicit no-docket state; the right cell must not look blank.
- Summary counts show total void items, matched, needs review, and unmatched.

## 2. States to handle
- Empty state (no bills uploaded yet)
- Loading state (extraction in progress)
- Error state (extraction failed / bad image)
- "Needs description" state (distinct from normal rows)
- Backend `status` values feed the row/table styling: `matched`,
  `needs_description`, `needs_ticket_number`, `needs_restaurant`,
  `needs_discrepancy_type`, `needs_review`.

## 3. Visual bar
- Professional, clean — not a bare unstyled table. Doesn't need to be
  elaborate, but should look like a real internal tool, not a prototype.

## 4. API contract (confirmed against the running backend)
| Action | Method | Endpoint | Notes |
|---|---|---|---|
| Upload image | POST | `/api/upload` | Multipart field **`file`** (singular). A full hyphenated Ticket ID is routed to `ticket_records`; unrecognized non-ticket images are rejected instead of being written to the docket table. |
| Upload image batch | POST | `/api/upload/bulk` | Multipart field **`files`** (plural, up to 30). Ticket-detected images use the ticket pipeline; non-ticket images are reported as failures and never enter a dedicated record table. |
| Upload ticket screenshots | POST | `/api/upload/tickets` | Multipart field **`files`** (plural, up to 30 screenshots). Each success returns the full `ticket_id`, item count, and screenshot count. |
| Upload docket images | POST | `/api/upload/dockets` | Multipart field **`files`** (plural, up to 30 images). Each success returns `order_number`, `date`, `time`, `item`, `discrepancy_type`, `description`, and review fields. |
| Get parsed tickets | GET | `/api/tickets` | Returns `ticket_id`, `uploaded_at` (latest screenshot upload/merge time), scalar metadata, `items[]` from the ticket item sub-table, `extra_fields`, and screenshot filenames. |
| Get parsed dockets | GET | `/api/dockets` | Returns `order_number`, `date`, `time`, `item`, `discrepancy_type`, `description`, `extra_fields`, and review fields. |
| Export parsed tickets | GET | `/api/tickets/export` | CSV with one row per parsed ticket and an Items column containing the flattened item list. |
| Export parsed dockets | GET | `/api/dockets/export` | CSV with docket order/date/time/item/discrepancy/handwriting/review fields. |
| Get void reconciliation | GET | `/api/reconcile/voids` | Returns `{rows, summary}`. Rows are already aligned and sorted by `row_position`; each contains `status`, `match_confidence`, `ticket`, `docket`, and `docket_candidates`. |
| Export void reconciliation | GET | `/api/reconcile/voids/export` | Downloads the same aligned rows and order as the JSON endpoint. The Voids view must use this endpoint instead of `/export`. |
| Get table rows | GET | `/api/entries?restaurant=&ticket_number=` | Query params optional; backend matches by exact value. Returns an array of `{id, restaurant, ticket_number, discrepancy_type, extracted_text, description, status, extra_fields, image_filename, blocks?}`. `blocks` is additive structured segmentation (header / line_items / discrepancies / totals / payment) that the frontend may ignore. |
| Reconcile tickets to image entries | POST | `/api/reconcile` | Body `{tickets: [{ticket_number, restaurant, date, time, amount, discrepancy_type, ...}], entries: [{id, ticket_number, restaurant, image_filename, extracted_text, description, ...}]}`. Returns `{results: [{ticket_number, restaurant, status, match_confidence, matched_entry_id, reason_provided, issue_addressed, handwritten_note, evidence}], summary: {Matched, Missing, Needs Review}}`. Ticket status is separate from entry status and must be displayed with its own column/filter. |
| Update description | PATCH | `/api/entries/{id}` | Body `{description?, status?}`. Returns the updated row (same shape as `/entries` rows). |
| Export CSV | GET | `/api/export?restaurant=&ticket_number=` | Same filters as `/entries`. Returns a CSV file with columns `restaurant, ticket_number, discrepancy_type, description, status, image_filename`. Browser downloads the file. |

### Frontend integration notes
- All routes live under the `/api` prefix (confirmed in `app/main.py`). The
  Vite dev server proxies `/api` to `http://localhost:8000` because the
  backend has no CORS middleware.
- `/upload` accepts one file per request in the singular `file` field. For
  true bulk upload, `/upload/bulk` accepts up to 30 files in the plural
  `files` field and reports success/failure independently for each filename.
  Both routes use the same synchronous extraction pipeline. The existing UI
  may continue sending one request per selected image; a bulk UI should
  refresh `/entries` after the bulk response rather than poll.
- Division 4c adds ticket-level reconciliation. The UI needs a separate
  reconciliation table or section showing `status` values `Matched`, `Missing`,
  and `Needs Review`, plus `match_confidence`, `reason_provided`, and
  `issue_addressed` columns or filters. These are different from the image
  entry `status` values (`matched`, `needs_description`, etc.) and must not be
  collapsed into one field.
- `/entries` returns no `thumbnail` field and the backend serves no image
  bytes; the "Image" column shows `image_filename` instead.
- Restaurant filter options come from the restaurant values in the
  `/entries` data (static placeholder names are shown only while the table
  is empty).
- The ticket-number search maps to the `ticket_number` query param (exact
  match), so a partial number returns no rows until it is fully entered.
- `/entries` responses may include an additive `blocks` field (structured
  line items / discrepancies / totals / payment). Render only what the table
  needs today; ignore unknown fields so backend growth stays non-breaking.
- Ticket upload results are authoritative for the merged ticket count. The UI
  should show the returned `ticket_id`, item count, screenshot count, and each
  failed screenshot; it should not create one UI ticket row per screenshot.
- Docket upload must display `docket_order_no` as a weak/partial match key,
  never as a full Ticket ID. It must keep `handwritten_reason` separate from
  printed fields and visibly mark `review_required` records.
- The Voids view must never independently sort or match rows in the browser;
  it renders the backend `row_position` order and sends void exports to the
  reconciliation export endpoint. The Tickets and Dockets views refresh their
  parsed endpoint after their corresponding bulk upload completes.

## 5. Changelog
| Date | Change | Reason |
|------|--------|--------|
| —    | Initial spec created | — |
| 2026-09-21 | Added frontend integration notes for upload and export behavior | Keep the UI contract honest while backend response shapes remain TBD |
| 2026-09-21 | Confirmed and finalized the API contract (section 4) against the running backend; updated column list (Image/Image column, verbatim statuses, extra_fields surfacing) and Frontend integration notes | Frontend is now wired end-to-end to the real backend; earlier "TBD" assumptions (upload field `files`, thumbnail field, unfiltered export) were corrected to match actual API behavior |
| 2026-09-21 | Documented the additive `blocks` field on `/entries` rows | Backend now persists per-entry structured segmentation (block JSON); frontend ignores it until it needs it |
| 2026-09-21 | Documented synchronous `/upload/bulk` with per-image success/failure results | Backend now accepts up to 30 images without changing the existing single-upload contract |
| 2026-09-21 | Replaced the stale single-entry-table contract with separate parsed Tickets, Dockets, and Voids tally views | Operators need to inspect extracted ticket/docket fields directly and export each record type without losing void alignment |
| 2026-09-22 | Finalized dedicated table columns: one row per ticket with a flattened Items cell and six docket columns; generic entries are not rendered | The UI must match the strict ticket/docket schemas and avoid generic raw-text presentation |