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
1. **Accept bill images as input** (upload).
2. **Extract all text from each image** (OCR / text extraction).
3. **Build a table** from the extracted data, with a row per bill, containing
   at minimum:
   - Restaurant (1 of 3)
   - Ticket number (extracted or entered)
   - Discrepancy type (void / discount / promotion)
   - Extracted raw text
   - Description (prompted from user if missing)
   - Status (matched / unmatched / needs description)
4. **Export the table to CSV** via a button.

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
1. Operator uploads a bill image (or batch).
2. Backend (FastAPI) extracts text from the image.
3. A row is added to the table with extracted fields.
4. If no description exists in the extracted text, the row is flagged
   "needs description" and the operator is prompted.
5. Operator can filter/search the table (e.g. by restaurant, by ticket
   number) to find the bill matching a ticket they're checking out in the
   custom app.
6. Operator exports the table (or a filtered view) as CSV.

## 6. Tech stack
- **Backend:** FastAPI (owns extraction — this is the core/hard part)
- **Frontend:** built separately by teammate, per `frontend_spec.md`
- **Extraction:** OCR method TBD — record the chosen library/service in
  `decisions.md` once picked (e.g. Tesseract, cloud OCR API, etc.)
- **Storage:** TBD for MVP — likely flat file/SQLite is enough; record choice
  in `decisions.md`

## 7. Changelog
> Every change to scope, flow, or fields gets a dated entry here. Keep it in
> sync with `decisions.md`.

| Date | Change | Reason |
|------|--------|--------|
| —    | Initial spec created | — |