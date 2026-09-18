# RULES.md — strict, non-negotiable

1. **MVP only.** No speculative features, no "nice to have" abstractions.
   If it's not needed to prove the core flow works, it doesn't get built.

2. **No automated tests.** Do not write unit/integration/e2e tests.
   All testing is manual by the user.

3. **No autonomous downloads/installs.** If a package, tool, or dependency
   needs to be installed, TELL the user the exact command — do not run it
   for them silently as part of "just making it work."

4. **UI must be professional**, even in MVP form. Not placeholder-looking.
   (Detailed UI requirements live in `frontend_spec.md` — that's the other
   person's job, but any UI produced here must still follow it.)

5. **Three divisions stay separated**, in code and in docs:
   - Division 1: Image input + text extraction (FastAPI)
   - Division 2: Table build / discrepancy matching (void / discount / promo)
   - Division 3: CSV export

6. **Single source of truth for decisions is `decisions.md`.**
   If a decision changes, it must be updated in `decisions.md` AND reflected
   in every other spec file it touches, in the same session. A decision is
   not "done" until every file agrees.

7. **Session discipline:**
   - Before writing code: log the planned change in `session_log.md`.
   - After finishing: log what was actually achieved (may differ from planned).
   - Never skip logging because the change felt small.

8. **One entry point.** New sessions are only ever pointed at `CONTEXT.md`.
   Do not assume a new session has any memory beyond what's written in these
   files.

9. **Alignment with the UI dev.** Anything that changes what data the
   frontend receives, what fields exist, or what actions are available must
   be reflected in `frontend_spec.md` immediately — that person is working
   off this file, not off conversations with you.