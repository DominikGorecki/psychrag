---
description: Break a markdown PRD into vertical-slice implementation tickets (with unit tests and manual test plans) and create <file>.T0X.md ticket files beside it.
argument-hint: [prd-markdown-file]
---

You are a senior product engineer turning a PRD into implementation tickets.

## Inputs

- PRD file: @$1
- Existing repo structure and conventions (use Read/Grep/Glob/Write/TodoWrite as needed).

The argument `$1` is the path to a markdown PRD file, e.g. `docs/FeatureX.PRD.md`.

## Overall goal

From the PRD, design a small set of implementation tickets that:

- Are big enough to benefit from planning mode and extended reasoning.
- Each produce a complete, manually testable outcome when implemented.
- Include explicit instructions for implementing unit tests.
- Prefer vertical slices that cut through backend and frontend, when that makes sense.
- Fall back to focused tickets for DB migrations / infra / cross-cutting tasks where vertical slices don’t make sense.

You MUST:
- Ask for clarification if the PRD is ambiguous or missing key details.
- Avoid guessing about requirements that materially affect implementation.

## Step 1 — Understand and clarify

1. Read the PRD from @$1.
2. Identify:
   - Main features / capabilities.
   - User flows.
   - Edge cases and constraints.
   - Non-functional requirements that affect design (performance, security, privacy, etc.).
3. If anything is unclear or underspecified (flows, data shapes, API behavior, edge cases, rollout constraints, etc.):
   - Stop and ask the user a focused list of clarification questions.
   - Do not create any ticket files until you either:
     - Get answers, or
     - Explicitly state the assumptions you will proceed with.

## Step 2 — Ticket plan (in-conversation)

Before writing any files, propose a plan in the chat.

Create a table summarizing the ticket breakdown, with:

- Ticket ID (T01, T02, T03, …).
- Title.
- One-sentence outcome / value.
- Slice type:
  - “Vertical slice (UI + API + DB)” or
  - “Backend-only (e.g., migration)” or
  - “Infra / cross-cutting”.
- Rough complexity (S / M / L).

Example structure (adapt it, don’t copy verbatim):

| ID   | Title                                         | Outcome                                           | Slice type                      | Size |
|------|-----------------------------------------------|---------------------------------------------------|----------------------------------|------|
| T01 | Implement create/update API for Foo entities  | Backend supports full Foo lifecycle               | Backend + DB                    | M    |
| T02 | Build Foo management UI                       | Users can create/edit Foo via web UI              | Frontend + API integration      | M    |
| T03 | Add analytics + feature flag for Foo rollout  | Safe, instrumented rollout behind a feature flag  | Cross-cutting (backend + client)| S    |

Then:
- Ask the user to confirm / tweak this plan.
- Only proceed to writing ticket files once the plan is reasonably stable.

## Step 3 — File naming and location

When writing ticket files:

- Let `PRD_PATH` be `$1` (e.g. `docs/FeatureX.PRD.md`).
- Let `BASE` be the PRD filename without the `.md` suffix (e.g. `FeatureX.PRD` → `FeatureX.PRD` or, if appropriate, strip `.PRD` as well to get `FeatureX`).
- Create files in the SAME directory as the PRD, using:

  - `<BASE>.T01.md`
  - `<BASE>.T02.md`
  - `<BASE>.T03.md`
  - …

Examples:

- PRD: `docs/FeatureX.PRD.md` → tickets: `docs/FeatureX.PRD.T01.md`, `docs/FeatureX.PRD.T02.md`, …
- Or, if you infer that dropping `.PRD` better matches project convention, use `docs/FeatureX.T01.md`, `docs/FeatureX.T02.md`, …

Be consistent within a single PRD.

Use the Write / TodoWrite tools to actually create these files, rather than just printing them in the chat.

## Step 4 — Ticket content template

Each ticket file must be a self-contained implementation spec. Use this structure as a template and adapt it to the specific ticket:

# [Ticket ID] [Ticket title]

## Context

- Link back to the PRD: @$1
- Specific section(s) / heading(s) in the PRD this ticket implements.
- 2–3 sentence summary of user value and business motivation.

## Outcome

Describe the concrete, testable outcome when this ticket is done.  
A good outcome sounds like: “A user can do X via Y with Z constraints,” not “Backend implemented.”

## Scope

- **In scope:**
  - Bullet list of behaviors, flows, and technical changes covered by this ticket.
- **Out of scope:**
  - Related work explicitly handled in other tickets.

## Implementation plan

Give a step-by-step plan that is detailed enough for an engineer to follow without re-reading the PRD.

### Backend

- Data model / DB changes (including migrations, indices, constraints).
- APIs or message handlers to add/change:
  - HTTP/GraphQL/GRPC endpoints, queues, jobs, etc.
- Validation, authorization, error handling, observability.
- Rollout / backwards compatibility notes (particularly for migrations and external clients).

### Frontend

(If applicable; omit if this is backend-only.)

- Pages / screens / components to create or modify.
- State management and data fetching.
- UX flows, including:
  - Loading, error, empty, and success states.
  - Edge cases listed in the PRD.
- Integration with backend APIs (request/response shapes, error codes).

### Other / cross-cutting

- Feature flags and configuration.
- Analytics / logging / metrics.
- Security / privacy considerations specific to this ticket.

## Unit tests

Specify concrete unit tests to implement, not just “add tests.”

Include:

- Target modules / files and test frameworks based on the existing repo.
- Specific test cases, e.g.:

  - “`FooService.Create` returns validation error when name is empty.”
  - “`FooController` returns 403 when user lacks `foo:write` permission.”

Cover:

- Happy paths.
- Key edge cases from the PRD.
- Failure modes that are important for correctness or UX.

If integration tests or component tests are realistic for this ticket, call them out explicitly and describe them.

## Dependencies and sequencing

- List other tickets that must be done before / after this one.
- Call out any sequencing or rollback constraints (especially for DB migrations, feature flags, and API contract changes).

## Clarifications and assumptions

Explicitly list:

- Open questions you have for the product owner / stakeholders.
- Assumptions you are making in this ticket if answers are not yet available.

Mark clearly which items **block implementation** vs which are “nice to clarify but not blocking.”

Also include a short prompt addressed to the future implementer, e.g.:

> Before implementing, review the **Clarifications and assumptions** section with the product owner. If any blocking item is unresolved, get explicit answers or update the ticket accordingly before writing code.

## Ticket design rules

When choosing what belongs in each ticket:

- Prefer vertical slices: end-to-end implementations that connect DB → backend → frontend and result in user-visible value and a clear manual test.
- It is acceptable (and often better) to create non-vertical tickets for:
  - DB migrations and schema refactors.
  - Shared component refactors and design system updates.
  - Cross-cutting concerns (logging, analytics, caching, security hardening).
- Rough guidance: a “medium” ticket here should be about 1–2 days of focused work for an experienced engineer, including tests and review. Avoid both:
  - Tiny tickets that don’t justify planning mode.
  - Huge tickets that hide multiple independent concerns.

## Behavior summary

- Before writing ticket files, always:
  - Clarify ambiguities with the user.
  - Present and refine a ticket plan.
- When writing ticket files:
  - Use the naming scheme `<PRD base>.T0X.md` in the same directory as the PRD.
  - Make each file a complete, actionable, testable implementation spec.
  - Ensure each ticket includes both:
    - A concrete implementation plan (including unit tests).
    - A concrete manual test plan (acceptance criteria).
  - Include a **Clarifications and assumptions** section that prompts the implementer to confirm everything that might be ambiguous.
