# TRELLIS Companion - Tampermonkey Telemetry Layer (Instagram & Facebook)

This directory contains the automatic behavioral telemetry tracking layer for the TRELLIS Evidence Pipeline. The layer captures content consumption on **Instagram** (`instagram.com`) and **Facebook** (`facebook.com`) (and YouTube) and streams normalized `EvidenceEvent` payloads automatically to the TRELLIS backend.

---

## 1. Files Created & Modified

### Created Files (All inside `tampermonkey/`):
- [trellis-telemetry.user.js](file:///c:/Users/ANVI/Desktop/hbt/tampermonkey/trellis-telemetry.user.js) - Standalone production Userscript with full telemetry client, companion detection, Instagram & Facebook Trackers, Focus Drift Engine, and automatic updates metadata.
- [telemetry-core.js](file:///c:/Users/ANVI/Desktop/hbt/tampermonkey/telemetry-core.js) - Core module for queueing, exponential backoff retries, localStorage persistence, batching, and `GM_xmlhttpRequest`/`fetch()` POST transport.
- [instagram-tracker.js](file:///c:/Users/ANVI/Desktop/hbt/tampermonkey/instagram-tracker.js) - Instagram-specific DOM detection, feed tracking, Reels view observers, and scroll metrics.
- [facebook-tracker.js](file:///c:/Users/ANVI/Desktop/hbt/tampermonkey/facebook-tracker.js) - Facebook-specific DOM detection, feed/timeline tracking, Watch & Reels view observers.
- [focus-drift-detector.js](file:///c:/Users/ANVI/Desktop/hbt/tampermonkey/focus-drift-detector.js) - Lightweight local Focus Drift engine enforcing scroll count (>5), continuous scroll duration (>30s), and excessive short-form consumption thresholds.
- [README.md](file:///c:/Users/ANVI/Desktop/hbt/tampermonkey/README.md) - Architectural documentation, installation flow, and companion detection guide.

### Modified Files Outside `tampermonkey/`:
- **NONE.** Strictly zero files modified outside the `tampermonkey/` directory per constraint.

---

## 2. Optimized 1-Click Installation Flow

```text
User opens TRELLIS Web App
        ↓
Signs in
        ↓
Clicks "Enable Behavioral Tracking"
        ↓ (Navigates directly to Userscript URL: http://localhost:8002/tampermonkey/trellis-telemetry.user.js)
Tampermonkey Auto-Installer Opens
        ↓ (User clicks "Install" button once)
Done Forever!
        ↓
Opening Instagram / Facebook automatically initializes telemetry
Closing those sites automatically stops telemetry
```

### User Interaction Count
- **Exactly 1 Click** (on the official Tampermonkey "Install" button).
- **Zero manual copying, zero code pasting, zero manual configuration, zero manual uploads.**

---

## 3. What Happens Automatically vs. What Happens Only Once

### Happens Only Once:
- User clicks **"Install"** on the Tampermonkey script dialog.

### Happens Automatically (Forever):
1. **Automatic Initialization & Configuration:** Upon opening `instagram.com` or `facebook.com`, the script initializes with pre-configured backend endpoints (`http://localhost:8002/api/v1/evidence`) and user authentication.
2. **Automatic Activity Detection:** Detects scroll count, continuous scroll duration, feed dwell time, and Reels consumption.
3. **Automatic Focus Drift Telemetry:** Emits `focus_drift` EvidenceEvents when scroll/reel thresholds are breached.
4. **Automatic Streaming:** Enqueues and POSTs telemetry events to backend `POST /api/v1/evidence`.
5. **Automatic Offline Queueing & Retry:** Retries failed requests with exponential backoff (`1000ms` to `60000ms`) and flushes on network restoration (`online` event).
6. **Automatic Cleanup:** Flushes remaining events and destroys timer resources on page unload (`beforeunload`).
7. **Automatic Updates:** Tampermonkey checks `@updateURL` in background and updates to newer versions automatically without re-installation.

---

## 4. Webpage Companion Detection Mechanism

The userscript prepares three non-intrusive detection mechanisms so the TRELLIS web app can detect whether the Companion is installed:

1. **DOM Attribute:** Sets `document.documentElement.setAttribute("data-trellis-companion-installed", "1.0.0")`.
2. **Custom Event:** Dispatches `CustomEvent("trellis:companion-ready", { detail: { installed: true, version: "1.0.0", active: true } })`.
3. **Window `postMessage` Listener:** Listens for `{ type: "TRELLIS_COMPANION_PING" }` and replies with `{ type: "TRELLIS_COMPANION_PONG", installed: true, version: "1.0.0", active: true }`.

---

## 5. End-to-End Pipeline Data Flow

```text
Browse Instagram / Facebook naturally
       ↓ (Automatic passive detection & focus drift evaluation)
Evidence API (POST http://localhost:8002/api/v1/evidence)
       ↓ (Authenticated user attribution & deduplication)
EvidenceEvent (Persisted via evidence_service.ingest)
       ↓ (PostgreSQL evidence_events table persistence)
Gap Engine (Recomputes Identity Gap ratio, create:consume alignment)
       ↓ (Dashboard updates & state invalidation)
Dashboard & Trust Ledger (Visualizes 21-day trajectory & attribute divergence)
       ↓ (Re-curation trigger)
Curator (LangGraph Coordinator pipeline assembles updated Identity Stack)
```
