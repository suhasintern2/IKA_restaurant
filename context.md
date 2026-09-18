# CONTEXT.md — START HERE

This is the only file a new session/agent needs to open first. Read this, then
follow the links below in order. Do not start writing code before doing this.

## Project
**TIL SYSTEM** — a discrepancy-checking tool for restaurant bills.
Three restaurants send bill images. An operator reconciles void / discount /
promotion discrepancies against tickets in a custom app, using the ticket
number to find the matching bill image. If a matched image has no
description, the system must prompt for one.

## Read in this order
1. `rules.md` — non-negotiable constraints. Everything else is subordinate to this.
2. `mvp_spec.md` — what we're building and why.
3. `architecture.md` — how the codebase is laid out.
4. `frontend_spec.md` — UI contract for the teammate building the frontend.
5. `decisions.md` — locked decisions. If a decision here conflicts with any
   other file, `decisions.md` wins and the other file is out of date — fix it.
6. `session_log.md` — history of what's been done, session by session.

## Current status
> Update this section at the end of every session. This is the fastest way
> for the next session to know where things stand.

- Phase: **All Divisions Complete - System ready for integration/testing**
- Last session: 2026-09-18 - Fixed field parsing logic (Division 2), enhanced schema flexibility with extra_fields, added granular statuses, fixed CSV export with image_filename
- Next up: All divisions complete - System ready for integration/testing

## Golden rule for every session
1. Before writing any code: write a "Planned changes" entry in `session_log.md`.
2. Do the work.
3. Write an "Achieved" entry in the same session_log.md entry.
4. If any decision changed, update `decisions.md` AND propagate that change
   into `mvp_spec.md` / `architecture.md` / `frontend_spec.md` — do not leave
   stale info in any of them.
5. Update the "Current status" block above.