# DECISIONS.md — locked decisions

> Source of truth. If any other doc disagrees with this file, the other doc
> is wrong and needs fixing. Every row here must be reflected in every spec
> it affects (mvp_spec / architecture / frontend_spec) in the same session
> it's added.

| Date | Decision | Reason | Files updated |
|------|----------|--------|----------------|
| —    | —        | —      | —              |
| 2026-09-21 | Use placeholder restaurant options: Restaurant A, Restaurant B, Restaurant C | The backend has not supplied canonical restaurant names yet | frontend_spec.md |
| 2026-09-21 | Upload each selected image in its own POST `/upload` request | Allows the required per-image pending, success, and failure states | frontend_spec.md |
| 2026-09-21 | Export CSV downloads the backend dataset returned by `/export` | The endpoint has no documented filter parameters | frontend_spec.md |