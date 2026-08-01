# TRELLIS Companion - Tampermonkey Telemetry Layer

Automatic behavioral telemetry for the TRELLIS Evidence Pipeline. Captures content consumption on **Instagram**, **Facebook**, and **YouTube**, then streams normalized `EvidenceEvent` payloads to the backend.

---

## Files

| File | Role |
|------|------|
| `trellis-telemetry.user.js` | Production userscript (install this) |
| `telemetry-core.js` | Reference module: queue, retry, transport |
| `instagram-tracker.js` | Reference Instagram tracker |
| `facebook-tracker.js` | Reference Facebook tracker |
| `focus-drift-detector.js` | Reference focus-drift thresholds |

The installable artifact is the single bundled `trellis-telemetry.user.js`. The other `.js` files are modular references for maintenance.

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

Note: persistence is **PostgreSQL** (not SQLite). Qdrant is used for semantic search / catalog ranking, not for raw Companion event writes.
