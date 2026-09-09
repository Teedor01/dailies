# Dailies Web

Next.js 14 (App Router) + TypeScript + Tailwind frontend for Dailies, talking
to the FastAPI backend in `../api/main.py`.

## Setup

```bash
npm install
cp .env.local.example .env.local   
npm run dev
```

The backend must be running separately:
```bash
cd ../api
uvicorn main:app --reload --port 8000
```

## Pages

- `/` -- Overview: aggregate stats across all investigations, most recent
  pipeline (live), recent investigations list, "New Investigation" button
- `/investigations` -- full list, filterable by status
- `/investigations/[id]` -- Timeline / Hypotheses / Evidence / Brief tabs,
  live-updating via SSE while the pipeline runs
- `/evidence` -- global Evidence Explorer, search + filter by type/step
- `/briefs` -- all generated briefs, citation-validation status

## Honest scope notes

- **Alerts** (shown in the sidebar mockup) is not built -- there's no
  backing data model for it in `controller.py`/`api/main.py` yet. Shown
  disabled in the sidebar rather than silently dropped, so the intended
  nav structure stays visible.
- **Overview's stat cards** show real numbers from `GET /overview`
  (investigation/running/brief/evidence counts) -- NOT the mockup's
  "Total Views / Avg Completion / Buffering Events / Social Mentions"
  tiles, since there's no backend endpoint aggregating those per-title
  view metrics yet. Wiring that up would need a new `/titles/{id}/stats`
  endpoint against `dailies.viewing_events` directly.
- **No chart library included.** The mockup's "Completion Rate by Region"
  line chart needs real per-hour data from ClickHouse that no current
  endpoint serves -- rather than fabricate placeholder numbers, this was
  left out. `recharts` can be added back when that endpoint exists.

## Verified before delivery

`npm run build` and `npm run lint` both pass clean (checked in the build
sandbox, not against a live backend -- API integration itself is untested
against the real FastAPI server since that requires your running instance).
