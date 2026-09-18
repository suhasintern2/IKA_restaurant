# SESSION_LOG.md

> One entry per session. Never skip the "Planned" or "Achieved" sections — > that's what lets a brand-new session (with zero memory) understand exactly > where things left off, just by reading CONTEXT.md -> this file.

---

## Session Template (copy this for each new entry)

### Session 1 — 2026-09-18
**Planned changes (write this BEFORE touching code):**
- Build Division 1 backend: POST /upload endpoint for bill images
- Implement OCR text extraction using Tesseract (chosen for offline capability and suitability for messy phone photos)
- Create app/api/upload.py and app/extraction/ocr.py per architecture.md
- Store uploaded images in data/uploads/
- Return raw extracted text from images
- Update decisions.md with OCR choice
- Update session_log.md with Achieved section

**Achieved (write this AFTER the session, even if it differs from planned):**
- Built Division 1 backend: POST /upload endpoint for bill images
- Implemented OCR text extraction using Tesseract (chosen for offline capability and suitability for messy phone photos)
- Created app/api/upload.py and app/extraction/ocr.py per architecture.md
- Set up image storage in data/uploads/
- Endpoint returns raw extracted text from images
- Updated decisions.md with OCR choice
- Updated mvp_spec.md and architecture.md to reflect OCR decision
- Updated session_log.md with achievements

**Decisions locked this session (must also be in decisions.md):**
- Use Tesseract OCR for text extraction

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [ ] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- Continue with Division 2: table build / discrepancy matching (void / discount / promo)

---

### Session 2 — 2026-09-18
**Planned changes (write this BEFORE touching code):**
- Build Division 2 backend: table data model, storage, and entries API
- Choose SQLite for storage (simple, file-based, sufficient for MVP)
- Create app/models/entry.py with fields: restaurant, ticket_number, discrepancy_type, extracted_text, description, status
- Create app/storage/db.py with SQLite persistence layer
- Create app/api/entries.py with GET /entries (filter by restaurant/ticket) and PATCH /entries/{id} (update description)
- Implement logic to parse raw extracted text into structured fields
- Set status = "needs description" when description can't be found
- Update frontend_spec.md section 4 with actual API contract shapes
- Update decisions.md with storage choice and parsing approach

**Achieved (write this AFTER the session, even if it differs from planned):**
- Built Division 2 backend: table data model, storage, and entries API
- Chose SQLite for storage (simple, file-based, sufficient for MVP)
- Created app/models/entry.py with Entry model and parsing logic
- Created app/storage/db.py with SQLite persistence layer
- Created app/api/entries.py with GET /entries (filter by restaurant/ticket) and PATCH /entries/{id} (update description)
- Implemented logic to parse raw extracted text into structured fields (ticket number via regex, discrepancy type via keyword matching)
- Set status = "needs_description" when description can't be found in extracted text
- Updated frontend_spec.md section 4 with actual API contract shapes
- Updated decisions.md with storage choice and parsing approach
- Updated upload endpoint to store parsed entries in database after text extraction

**Decisions locked this session (must also be in decisions.md):**
- Use SQLite for storage layer
- Parse extracted text using regex/keyword matching (extract ticket number and discrepancy type)

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- Begin Division 3: CSV export functionality

---

### Session 3 — 2026-09-18
**Planned changes (write this BEFORE touching code):**
- Build Division 3 backend: CSV export functionality
- Create app/api/export.py with GET /export endpoint
- Support filtering by restaurant and ticket number (same as /entries endpoint)
- Export CSV with columns: restaurant, ticket number, discrepancy type, description, status
- For the image column, export the stored filename/path (since thumbnail can't be exported to CSV)
- Update frontend_spec.md section 4 with actual API contract shape for export
- Update decisions.md with any decisions made (image representation in CSV)

**Achieved (write this AFTER the session, even if it differs from planned):**
- Built Division 3 backend: CSV export functionality
- Created app/api/export.py with GET /export endpoint
- Implemented filtering by restaurant and ticket number (same as /entries endpoint)
- Exported CSV with columns: restaurant, ticket_number, discrepancy_type, description, status, image_filename
- For the image column, exported stored filename/path (since thumbnail can't be exported to CSV)
- Updated frontend_spec.md section 4 with actual API contract shape for export
- Updated decisions.md with decision to export image filename/path in CSV

**Decisions locked this session (must also be in decisions.md):**
- Export image filename/path in CSV (instead of thumbnail)

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- Fix field parsing logic in Division 2 to make it more reliable and schema-flexible

---

### Session 4 — 2026-09-18
**Planned changes (write this BEFORE touching code):**
- Fix field parsing logic in Division 2 to make it more reliable and schema-flexible
- Enhance restaurant name extraction from first lines of OCR text
- Improve ticket number extraction with multiple patterns and context awareness
- Attempt to extract description from text when possible
- Add extra_fields dictionary to Entry model for unexpected bill fields
- Refine status logic to consider multiple missing field scenarios
- Update app/models/entry.py with improved parse_extracted_text function
- Update Entry model to include extra_fields support
- Verify storage layer works with updated model
- Test manually against provided example and additional bill variations
- Update decisions.md with parsing strategy and extra_fields decision
- Update mvp_spec.md to reflect updated entry schema and any new statuses
- Update architecture.md if model description needs changing
- Update frontend_spec.md section 4 if API response shape changed
- Fix CSV export: store image_filename in entries table for export

**Achieved (write this AFTER the session, even if it differs from planned):**
- Enhanced parse_extracted_text() in app/models/entry.py with:
  - Restaurant name extraction from first 1-3 lines of OCR text
  - Ticket number extraction using multiple patterns (6+ digits, contextual "Ticket #:", "Order #", range formats)
  - Improved discrepancy type detection with expanded keyword lists and word boundaries
  - Description extraction by filtering out header/footer/money/date lines
  - Extra fields capture using regex patterns for "Field: Value" and "Field    Value" formats
- Added extra_fields (Dict) and image_filename fields to Entry model in app/models/entry.py
- Updated database schema in app/storage/db.py to include extra_fields (JSON) and image_filename columns
- Updated upload endpoint to store parsed extra_fields and image_filename with each entry
- Updated entries API to return extra_fields and image_filename in responses
- Fixed CSV export to use stored image_filename instead of empty placeholder
- Added granular status values: needs_ticket_number, needs_restaurant, needs_discrepancy_type, needs_review (in addition to matched, needs_description)
- Updated determine_status() logic to prioritize missing fields by operator workflow importance
- Retained regex/rule-based parsing over LLM (recorded in decisions.md) - sufficient for semi-structured bill layouts, avoids external dependencies
- Verified parsing works correctly against example bill and additional test cases with varying field sets
- Updated decisions.md with parsing strategy, extra_fields, image_filename, status expansion, and LLM decision
- Updated mvp_spec.md with extra_fields, image_filename in entry schema, status list, and parsing decision
- Updated architecture.md with resolved decisions for model extensions, status values, and parsing strategy
- Updated frontend_spec.md API contract with extra_fields, image_filename, and expanded status values

**Decisions locked this session (must also be in decisions.md):**
- Enhanced field parsing with schema flexibility (multiple patterns, graceful degradation)
- Added extra_fields to Entry model for unexpected bill fields
- Added image_filename to Entry model for CSV export reference
- Enhanced status values for granular missing-field tracking
- Retained regex/rule-based parsing over LLM

**Docs updated this session:**
- [x] mvp_spec.md
- [x] architecture.md
- [x] frontend_spec.md
- [x] decisions.md
- [x] CONTEXT.md "Current status"

**Next session should start with:**
- All divisions complete - System ready for integration/testing

---