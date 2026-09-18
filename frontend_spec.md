# FRONTEND SPEC — TIL SYSTEM

> This is the contract between backend and UI. If the backend changes a
> field name, endpoint, or flow, this file must be updated in the same
> session — don't let it drift from what the API actually returns.

## 1. Screens

### Screen 1 — Upload
- Upload control for one or more bill images
- Shows upload progress / basic success-fail state per image
- On success, extracted rows appear in the table (Screen 2)

### Screen 2 — Table view
Columns (MVP):
- Restaurant (one of the 3 — should support filtering/tab by restaurant)
- Ticket number
- Discrepancy type (void / discount / promotion) — visually distinct (e.g. tag/badge)
- Thumbnail of the source image
- Description
- Status (Matched / Needs description / Unmatched)

Behavior:
- If a row has no description, it's visually flagged and clicking it opens
  a prompt (modal or inline field) to add one.
- Search/filter by ticket number and by restaurant (this is the core
  "operator searches for a ticket's matching image" use case).
- "Export CSV" button — exports the current table or the current filtered
  view (confirm which with backend/decisions.md).

### Screen 3 (optional, only if needed for MVP) — Description prompt
- Simple modal/form: shows the image, lets operator type a description,
  saves back to the row.

## 2. States to handle
- Empty state (no bills uploaded yet)
- Loading state (extraction in progress)
- Error state (extraction failed / bad image)
- "Needs description" state (distinct from normal rows)

## 3. Visual bar
- Professional, clean — not a bare unstyled table. Doesn't need to be
  elaborate, but should look like a real internal tool, not a prototype.

## 4. API contract (fill in once backend endpoints are finalized)
| Action | Method | Endpoint | Notes |
|---|---|---|---|
| Upload image | POST | `/upload` | Returns: {filename, original_filename, extracted_text, entry_id, parsed_data: {restaurant, ticket_number, discrepancy_type, description}} |
| Get table rows | GET | `/entries` | Returns: List of entries with fields: id, restaurant, ticket_number, discrepancy_type, extracted_text, description, status (matched/unmatched/needs_description) |
| Update description | PATCH | `/entries/{id}` | Accepts: {description?: string, status?: string}; Returns: updated entry object |
| Export CSV | GET | `/export` | Returns: CSV file with columns: restaurant, ticket_number, discrepancy_type, description, status, image_filename. Supports same filters as /entries (restaurant, ticket_number). Image filename exported instead of thumbnail. |

## 5. Changelog
| Date | Change | Reason |
|------|--------|--------|
| —    | Initial spec created | — |