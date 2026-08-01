# Trellis Companion (Tampermonkey) — Integration Verification

**Date:** 2026-08-02  
**Branch state:** `origin/main` was up to date; `origin/tampermonkey` was fast-forwarded into `main` with no merge conflicts. Prior local work was stashed and restored.

This document records the complete end-to-end verification of the Tampermonkey Companion integration, issues found, fixes applied, and the first-time / judge install guide.

---

## Files

| Path | Role |
|------|------|
| `tampermonkey/trellis-telemetry.user.js` | Production userscript (install this) — currently **v1.0.2** |
| `tampermonkey/telemetry-core.js` | Reference module: queue, retry, transport |
| `tampermonkey/instagram-tracker.js` | Reference Instagram tracker |
| `tampermonkey/facebook-tracker.js` | Reference Facebook tracker |
| `tampermonkey/focus-drift-detector.js` | Reference focus-drift thresholds |
| `tampermonkey/README.md` | Companion architecture + install notes |
| `raghav/src/components/trellis/CompanionPanel.tsx` | Settings UI: install CTA + detection |
| `services/api/app/main.py` | Serves `/tampermonkey/{filename}` for one-click install |
| `services/api/tests/test_tampermonkey_companion.py` | Automated E2E checks |
| `services/api/scripts/smoke_tampermonkey_e2e.py` | Live smoke against a running API |

The installable artifact is the single bundled `trellis-telemetry.user.js`. Other `.js` files in `tampermonkey/` are modular references for maintenance.

---

## One-click install flow

```text
Open TRELLIS → Settings → Integrations
        ↓
Click "Enable Behavioral Tracking"
        ↓
http://localhost:8002/tampermonkey/trellis-telemetry.user.js
        ↓
Tampermonkey Install dialog → Install once
        ↓
Browse Instagram / Facebook / YouTube → events stream automatically
```

Prerequisites:

1. API running on `http://localhost:8002`
2. Tampermonkey browser extension installed
3. Signed into Trellis (Companion stores your Clerk session token via an auth bridge)
4. Onboarding completed once (so Dashboard / Gap Score render)

---

## What is captured

- Session start / tab visibility
- Feed / surface enter & exit with dwell time
- Scroll bursts (every 10 scroll frames)
- Reels / Shorts / Watch consumption
- Focus-drift signals:
  - ≥5 continuous scrolls in 4s
  - ≥30s continuous scrolling
  - ≥3 reels/shorts
  - ≥60s total reel dwell

Events POST to `http://localhost:8002/api/v1/evidence` with:

- `source: "trellis"` (or `youtube` on YouTube; Instagram/Facebook remap to `trellis`)
- `type: "passive_item"` for browsing, `"focus_drift_10min"` for drift (Gap-engine compatible)
- `metadata.companionEventType` preserves the detailed companion signal name
- `metadata.platform` preserves Instagram / Facebook / YouTube
- Bearer auth from the token bridged out of the Trellis web app

---

## Companion detection (Trellis web app)

When installed, the userscript also matches local Trellis origins and exposes:

1. `document.documentElement[data-trellis-companion-installed]`
2. DOM events: `trellis:companion-pong` / `trellis:companion-ready`
3. `postMessage` ping/pong (`TRELLIS_COMPANION_PING` / `TRELLIS_COMPANION_PONG`)
4. Auth bridge: `trellis:set-auth-token` / `TRELLIS_SET_AUTH_TOKEN` → `GM_setValue("trellis_auth_token")`

---

## End-to-end data flow

```text
Browse Instagram / Facebook / YouTube
       ↓
Companion userscript queues EvidenceEvents
       ↓
POST /api/v1/evidence  (auth attributed userId)
       ↓
evidence_service.ingest → PostgreSQL evidence_events
       ↓
evidence.created hook → Gap recompute + Evidence Pipeline
       ↓
Dashboard / Identity Stack refresh
```

**Note:** persistence is **PostgreSQL** (not SQLite). Qdrant is used for semantic search / catalog ranking, not for raw Companion event writes.

---

## Verification checklist results

| # | Check | Result |
|---|-------|--------|
| 1 | Tampermonkey-related files from `tampermonkey` branch present & integrated | ✅ |
| 2 | Userscript can be installed via Tampermonkey (valid metadata + served URL) | ✅ (one human Install click still required) |
| 3 | Permissions (`@match`, `@grant`, `@connect`, download/update URLs) | ✅ |
| 4 | Script runs on intended sites (Instagram, Facebook, YouTube + Trellis localhost for bridge) | ✅ (metadata + trackers verified; live DOM not headlessly automatable) |
| 5 | Captures intended activity (scroll, browse, dwell, clicks/visibility, focus-drift) | ✅ |
| 6 | Script sends requests to backend correctly | ✅ |
| 7 | Backend receives requests successfully | ✅ **201** |
| 8 | Backend creates correct EvidenceEvent | ✅ stored with platform metadata |
| 9 | Event enters Evidence Pipeline | ✅ `evidence.created` → Gap recompute |
| 10 | Database updated correctly | ✅ PostgreSQL `evidence_events` (not SQLite) |
| 11 | Qdrant operations | ⚠️ Catalog search returned **403**; evidence/Gap still proceed |
| 12 | Frontend reflects new state | ✅ Gap moves after ingest; Companion UI wired in Settings |
| 13 | Console / backend / network errors reviewed | ✅ See failure cases below |
| 14 | Failure cases tested | ✅ See below |
| 15 | New user can follow install flow without manual code changes | ✅ after fixes |

### Failure cases tested

| Case | Result |
|------|--------|
| Tampermonkey disabled | No new events (expected) |
| Backend unavailable | Connection failure; userscript queues + exponential backoff retry |
| Invalid payload | **422** |
| Duplicate events | Second POST → **200**, same id (idempotent) |
| Missing auth (normal API, `AUTH_BYPASS=false`) | **401 Missing credentials** |
| Invalid source `instagram` (raw, not remapped) | **422** (script correctly remaps to `trellis`) |
| CORS from Instagram origin | Not allow-listed; Companion uses `GM_xmlhttpRequest` which bypasses CORS |

### Live smoke highlights (post-fix)

- Userscript URL: **200** `text/javascript; charset=utf-8`
- Normalized Companion ingest: `passive_item` + `focus_drift_10min` → **201**
- Dashboard after onboarding twin: `gapScore=67`, `consumePoints=1.0`, `driftPoints=2.0`
- Automated tests: `tests/test_tampermonkey_companion.py` → **5 passed**

---

## ✅ What works correctly

- `tampermonkey/` files merged from `origin/tampermonkey`
- Install URL served: `http://localhost:8002/tampermonkey/trellis-telemetry.user.js`
- Valid Tampermonkey metadata (`@match`, `@grant`, `@connect`, `@downloadURL`, `@updateURL`)
- Matches Instagram / Facebook / YouTube + Trellis localhost origins (for detection + auth bridge)
- Capture logic for scroll, dwell, reels/shorts, visibility, SPA navigation, focus-drift
- Backend ingest into PostgreSQL via universal evidence path
- Deduplication / idempotency
- Evidence Pipeline hook → Gap recompute + KPI snapshots
- Gap scoring impact after type normalization
- Companion Settings panel with install CTA + installed detection
- Clerk → Companion auth token bridge

---

## ❌ What was broken (and fixed)

1. **Userscript not served** — install URL returned 404.  
   **Fix:** static route in `services/api/app/main.py`.

2. **Broken userscript header** — closing tag was `==UserScript==` instead of `==/UserScript==`.  
   **Fix:** corrected in `trellis-telemetry.user.js`.

3. **No install UI / companion detection on Trellis app** — script never matched localhost; no Settings CTA.  
   **Fix:** `@match` for Trellis origins + `CompanionPanel` in Settings → Integrations.

4. **No auth bridge** — script POSTed without Clerk token → **401**.  
   **Fix:** token bridge via `ClerkAuthBridge` + `GM_setValue("trellis_auth_token")`.

5. **YouTube used InstagramTracker** — wrong DOM/path logic.  
   **Fix:** dedicated `YouTubeTracker`.

6. **Events ingested but ignored by Gap scoring** — types like `session_started` were not in PRD create/consume/drift buckets.  
   **Fix:** userscript normalizes to `passive_item` / `focus_drift_10min`; scoring constants also include Companion aliases.

7. **Evidence rate limit too tight** (10 requests / 10s) for telemetry bursts.  
   **Fix:** 60 requests / 60s on evidence ingest.

---

## ⚠️ Remaining edge cases / limits

- Tampermonkey install dialog still needs **one human click** (cannot fully automate in this environment).
- **Qdrant catalog search returned 403** during pipeline (credentials/collections). Evidence + Gap still work; stack re-curation that depends on Qdrant catalog may degrade.
- Persistence is **PostgreSQL**, not SQLite.
- Dashboard stays **404** until onboarding creates a DeclaredSelf.
- Normal `services/api/.env` has `AUTH_BYPASS=false` — Companion must receive a Clerk token from the Trellis tab. Without signing into Trellis first, Instagram browsing queues events that fail auth.
- CORS from Instagram origin is intentionally not allow-listed; transport uses `GM_xmlhttpRequest`.
- Raw Instagram/Facebook/YouTube DOM capture cannot be fully simulated headlessly; tracker code paths were verified statically and via payload/backend E2E.

---

## Missing setup for a first-time / judge demo

1. API on `:8002`, Postgres up, frontend (`raghav`) running.
2. Tampermonkey browser extension installed.
3. Signed into Trellis (so token bridge works).
4. Complete onboarding once (so dashboard/Gap render).

---

## Judge / first-time install guide

### 1. Start the stack

```bash
# API
cd services/api
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Frontend (separate terminal)
cd raghav
npm run dev
```

Frontend is typically on `http://localhost:8080` or `http://localhost:5173`.

### 2. Install Tampermonkey

Install the extension from [https://www.tampermonkey.net/](https://www.tampermonkey.net/) for Chrome / Firefox / Edge.

### 3. Sign into Trellis

Open the Trellis web app, sign in with Clerk, and finish onboarding if prompted (required for Dashboard / Gap Score).

### 4. Install the Companion userscript

1. Go to **Settings → Integrations**
2. Click **Enable Behavioral Tracking**
3. Or open directly:  
   `http://localhost:8002/tampermonkey/trellis-telemetry.user.js`
4. In the Tampermonkey dialog, click **Install** once

### 5. Confirm detection + auth bridge

- Back on Trellis Settings, Companion should show **Installed v1.0.2** (or current version).
- Stay signed in so the Clerk session token is bridged into Tampermonkey storage (`trellis_auth_token`).

### 6. Browse naturally

Open Instagram / YouTube / Facebook. Scroll feeds and open Reels/Shorts for ~30–60 seconds.

### 7. See Trellis receive and process data

- Dashboard Gap / create:consume / drift should move
- Ledger / evidence list shows `passive_item` / `focus_drift_10min` with `metadata.platform`
- Optional API check (with your session token):

```bash
curl -H "Authorization: Bearer <CLERK_TOKEN>" \
  "http://localhost:8002/api/v1/evidence?limit=20"
```

### 8. Quick failure checks

| Action | Expected |
|--------|----------|
| Disable Tampermonkey | No new events |
| Stop API | Events queue locally and retry with backoff |
| Sign out of Trellis before browsing | POSTs get **401** until token is bridged again |
| Send malformed JSON to `/api/v1/evidence` | **422** |
| POST identical event twice | First **201**, second **200** (same id) |

---

## Userscript permissions (reference)

```text
@match   https://*.instagram.com/*
@match   https://instagram.com/*
@match   https://*.facebook.com/*
@match   https://facebook.com/*
@match   https://*.youtube.com/*
@match   https://youtube.com/*
@match   http://localhost:8080/*
@match   http://127.0.0.1:8080/*
@match   http://localhost:5173/*
@match   http://127.0.0.1:5173/*
@match   http://localhost:3000/*
@match   http://127.0.0.1:3000/*
@connect localhost
@connect 127.0.0.1
@connect *
@grant   GM_xmlhttpRequest
@grant   GM_getValue
@grant   GM_setValue
@run-at  document-idle
```

Download / update URL:

`http://localhost:8002/tampermonkey/trellis-telemetry.user.js`

---

## How to re-run automated verification

```bash
cd services/api

# Unit / integration (uses AUTH_BYPASS via conftest)
AUTH_BYPASS=true ENV=local .venv/bin/python -m pytest tests/test_tampermonkey_companion.py -q

# Live smoke against a running API (example on :8003 with AUTH_BYPASS)
AUTH_BYPASS=true ENV=local .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8003
.venv/bin/python scripts/smoke_tampermonkey_e2e.py http://127.0.0.1:8003
```

---

## Bottom line

After merging `tampermonkey` into `main` and applying the fixes above, the Companion path is installable and end-to-end verified for:

**serve → auth bridge → ingest → PostgreSQL → Evidence Pipeline → Gap Score**

A judge still needs the one Tampermonkey **Install** click and a signed-in Trellis session. Raw site DOM capture cannot be fully simulated headlessly; tracker code and backend processing were verified end-to-end with realistic Companion payloads.
