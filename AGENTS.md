# AGENTS.md — NZ Campervan Trip 2027

> Guidance for AI agents (and collaborators) working in this repository.

## What this project is
A 61-day New Zealand campervan road trip (South + North Island) for two people,
**19 Mar 2027 (pickup Christchurch) → 18 May 2027 (dropoff Auckland)**.
The plan is built and maintained here so it can be iterated on continuously
(currently by the Hermes agent, but designed for any agent to pick up).

## Repository layout
- `itinerary.md` — **SOURCE OF TRUTH.** Full day-by-day plan: route (South Island
  loop incl. West Coast + Abel Tasman), accommodation, booking checklist, and the
  campsite reference table (names, prices, links). Edit here.
- `README.md` — Short human-facing overview.
- `TODO.md` — Open planning items beyond bookings, categorized.
- `AGENTS.md` — This file.

## Hard constraints (do not violate)
- **Dates are fixed** by the rental window (19 Mar – 18 May 2027).
- **Accommodation priority is STRICT:** 1) Freedom camping (free, self-contained
  required) → 2) DOC campsite (cheap) → 3) Holiday park (fallback, expensive).
  Never recommend a paid park when a free/DOC option exists for that stop.
- **Self-contained campervan required.** NZ law mandates a valid self-containment
  certificate (green sticker) for freedom camping from **7 Jun 2026**. This must be
  confirmed with the rental company.
- **Freedom-camping rules change frequently.** Verify every stay via the Rankers
  Camping NZ / CamperMate apps AND on-site signage before committing.
- Prices are 2026 rates (NZD, ~2 adults on a powered site/night); verify before booking.

## Critical booking deadlines (tracked as GitHub issues, label `booking`)
These sell out or have lead-time limits — act early:
- Hobbiton Movie Set Tour — **NOW** (sells out ~10 months ahead)
- Interislander/Bluebridge ferry Picton→Wellington (with camper) — ~6 months ahead
- Franz Josef Glacier Heli-Hike — ~2–3 months ahead
- Tongariro Alpine Crossing — booking mandatory for all since Oct 2024
- Milford Sound cruise, Waitomo, Kaikoura whale watch, Royal Albatross,
  Penguin Place, Cape Kidnappers — weeks ahead

## Conventions
- Plan prose is **German** (user is a German speaker). Keep it that way.
- Keep `itinerary.md` as the single source of truth; reference, don't duplicate.
- When adding a campsite, include: real name, price (NZD), booking URL, priority tier.
- Keep tables scannable; avoid heavy nesting.

## Git & GitHub workflow (no `gh` CLI installed)
- Token: `GITHUB_TOKEN` in `/home/hermes/.hermes/.env` (scope: `repo`).
- Local working copy: `/home/hermes/nz_trip_2027` (remote already configured).
- Push edits:
  ```bash
  export HOME=/home/hermes
  cd /home/hermes/nz_trip_2027
  git add -A && git commit -m "type: short summary" && git push
  ```
  (The remote URL already embeds the token; if the token is rotated, update both
  the `.env` file and the remote URL.)
- Manage issues/PRs via the GitHub REST API, e.g.:
  ```bash
  curl -s -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/jfeiler87/Nz27/issues
  ```
- **Never** commit the token or the `.env` file.

## For a new agent picking this up
1. Read `itinerary.md` and `TODO.md` in full.
2. Respect the accommodation priority and booking deadlines above.
3. For new actionable work, either edit the files or open a GitHub issue
   (label `booking` for reservations, `planning` for other tasks).
4. Commit with a clear message and push.
