// ==UserScript==
// @name         Trellis Companion - Behavioral Telemetry Collector
// @namespace    http://trellis.ai/
// @version      1.0.3
// @description  Automatic behavioral telemetry tracking for TRELLIS Evidence Pipeline
// @author       TRELLIS Team
// @match        https://*.instagram.com/*
// @match        https://instagram.com/*
// @match        https://*.facebook.com/*
// @match        https://facebook.com/*
// @match        https://*.youtube.com/*
// @match        https://youtube.com/*
// @match        http://localhost:8080/*
// @match        http://127.0.0.1:8080/*
// @match        http://localhost:5173/*
// @match        http://127.0.0.1:5173/*
// @match        http://localhost:3000/*
// @match        http://127.0.0.1:3000/*
// @connect      localhost
// @connect      127.0.0.1
// @connect      *
// @downloadURL  http://localhost:8002/tampermonkey/trellis-telemetry.user.js
// @updateURL    http://localhost:8002/tampermonkey/trellis-telemetry.user.js
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  // =========================================================================
  // CONFIGURATION & CONSTANTS
  // =========================================================================
  const VERSION = "1.0.3";
  const DEBUG = false; // Toggle debug console logging
  const BACKEND_BASE_URL = "http://localhost:8002"; // Pre-configured backend API URL
  const EVIDENCE_ENDPOINT = "/api/v1/evidence";
  const QUEUE_KEY = "trellis_telemetry_queue";
  const SENT_IDS_KEY = "trellis_telemetry_sent_ids";
  const AUTH_TOKEN_KEY = "trellis_auth_token";
  const MAX_SENT_IDS = 500;
  const BATCH_SIZE = 10;
  const FLUSH_INTERVAL_MS = 5000;
  const INITIAL_RETRY_DELAY_MS = 1000;
  const MAX_RETRY_DELAY_MS = 60000;
  const BACKOFF_FACTOR = 2;
  const TRELLIS_APP_HOSTS = ["localhost", "127.0.0.1"];

  function logDebug(...args) {
    if (DEBUG) {
      console.log("%c[Trellis Telemetry]", "color: #6366f1; font-weight: bold;", ...args);
    }
  }

  function generateEventId(event) {
    const raw = `${event.source}|${event.type}|${event.timestamp}|${event.value}|${JSON.stringify(event.metadata || {})}`;
    let hash = 0;
    for (let i = 0; i < raw.length; i++) {
      const char = raw.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    return "evt_" + Math.abs(hash).toString(36) + "_" + Date.now().toString(36);
  }

  // =========================================================================
  // COMPANION DETECTION + AUTH BRIDGE FOR TRELLIS WEB APP
  // DOM CustomEvents are reliable across Tampermonkey's sandbox boundary.
  // =========================================================================
  function replyCompanionPong() {
    const detail = { installed: true, version: VERSION, active: true };
    document.documentElement.setAttribute("data-trellis-companion-installed", VERSION);
    document.dispatchEvent(new CustomEvent("trellis:companion-pong", { detail, bubbles: true }));
    window.dispatchEvent(new CustomEvent("trellis:companion-ready", { detail }));
    window.postMessage({ type: "TRELLIS_COMPANION_PONG", ...detail }, "*");
  }

  function storeAuthToken(token) {
    if (!token || typeof token !== "string") return;
    try {
      if (typeof GM_setValue === "function") {
        GM_setValue(AUTH_TOKEN_KEY, token);
      }
      // Also mirror into page storage when running on the Trellis app origin.
      localStorage.setItem(AUTH_TOKEN_KEY, token);
      logDebug("Auth token stored for Companion telemetry.");
    } catch (e) {
      logDebug("Error storing auth token:", e);
    }
  }

  function requestAuthTokenFromApp() {
    // Ask the Trellis web app to re-broadcast a fresh Clerk JWT.
    document.dispatchEvent(new CustomEvent("trellis:request-auth-token", { bubbles: true }));
    window.postMessage({ type: "TRELLIS_REQUEST_AUTH_TOKEN" }, "*");
  }

  function setupCompanionDetection() {
    try {
      replyCompanionPong();

      window.addEventListener("message", (event) => {
        const data = event.data || {};
        if (data.type === "TRELLIS_COMPANION_PING") {
          replyCompanionPong();
        }
        if (data.type === "TRELLIS_SET_AUTH_TOKEN" && data.token) {
          storeAuthToken(data.token);
        }
      });

      document.addEventListener("trellis:companion-ping", () => replyCompanionPong());
      document.addEventListener("trellis:set-auth-token", (event) => {
        storeAuthToken(event.detail && event.detail.token);
      });

      // On Trellis origins, immediately ask the app for a token after install/refresh.
      const host = (window.location.hostname || "").toLowerCase();
      if (TRELLIS_APP_HOSTS.includes(host)) {
        requestAuthTokenFromApp();
        window.setTimeout(requestAuthTokenFromApp, 800);
        window.setTimeout(requestAuthTokenFromApp, 2500);
      }

      logDebug("Companion detection + auth bridge registered.");
    } catch (e) {
      logDebug("Error setting up companion detection:", e);
    }
  }

  // =========================================================================
  // LOCAL STORAGE & AUTH MANAGER
  // =========================================================================
  class StorageManager {
    static getQueue() {
      try {
        const item = localStorage.getItem(QUEUE_KEY);
        return item ? JSON.parse(item) : [];
      } catch (e) {
        logDebug("Error reading queue from localStorage", e);
        return [];
      }
    }

    static saveQueue(queue) {
      try {
        localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
      } catch (e) {
        logDebug("Error saving queue to localStorage", e);
      }
    }

    static getSentIds() {
      try {
        const item = localStorage.getItem(SENT_IDS_KEY);
        return item ? JSON.parse(item) : [];
      } catch (e) {
        return [];
      }
    }

    static markSent(id) {
      try {
        const sent = StorageManager.getSentIds();
        if (!sent.includes(id)) {
          sent.push(id);
          if (sent.length > MAX_SENT_IDS) {
            sent.shift();
          }
          localStorage.setItem(SENT_IDS_KEY, JSON.stringify(sent));
        }
      } catch (e) {
        logDebug("Error marking sent ID", e);
      }
    }

    static isSent(id) {
      const sent = StorageManager.getSentIds();
      return sent.includes(id);
    }

    static getAuthToken() {
      try {
        if (typeof GM_getValue === "function") {
          const gmToken = GM_getValue(AUTH_TOKEN_KEY, null);
          if (gmToken) return gmToken;
        }
        return localStorage.getItem(AUTH_TOKEN_KEY) || null;
      } catch (e) {
        return null;
      }
    }
  }

  // =========================================================================
  // TELEMETRY CLIENT & BACKEND TRANSPORT
  // =========================================================================
  class TelemetryClient {
    constructor() {
      this.isFlushing = false;
      this.retryAttempts = 0;
      this.retryTimer = null;
      this.init();
    }

    init() {
      logDebug("Initializing Telemetry Client...");
      window.addEventListener("online", () => {
        logDebug("Network online. Flushing telemetry queue...");
        this.flushQueue();
      });

      this.flushIntervalId = setInterval(() => {
        this.flushQueue();
      }, FLUSH_INTERVAL_MS);

      setTimeout(() => this.flushQueue(), 1000);
    }

    destroy() {
      if (this.flushIntervalId) clearInterval(this.flushIntervalId);
      if (this.retryTimer) clearTimeout(this.retryTimer);
    }

    normalizeForGapEngine(type, category) {
      // Gap scoring only buckets known PRD §9 types. Keep companion detail in metadata.
      if (category === "focus_drift" || String(type).startsWith("focus_drift")) {
        return { type: "focus_drift_10min", category: "focus_drift" };
      }
      if (category === "passive_learning") {
        return { type: "passive_item", category: "passive_learning" };
      }
      return { type, category };
    }

    createEvent({ source, type, category, value = 1.0, baseWeight = 0.5, metadata = {} }) {
      // Preferred source for first-party Tampermonkey client telemetry is "trellis"
      let backendSource = "trellis";
      if (
        ["github", "google_calendar", "youtube", "notion", "trellis", "x"].includes(source)
      ) {
        backendSource = source;
      }

      const normalized = this.normalizeForGapEngine(type, category);
      const event = {
        timestamp: new Date().toISOString(),
        source: backendSource,
        type: normalized.type,
        category: normalized.category,
        identityAttributeIds: [],
        value: Number(value),
        baseWeight: Number(baseWeight),
        metadata: {
          platform: source,
          originalSource: source,
          companionEventType: type,
          userAgent: navigator.userAgent,
          url: window.location.href,
          ...metadata,
        },
        simulated: false,
      };

      event.eventId = generateEventId(event);
      return event;
    }

    enqueue(eventData) {
      const event = this.createEvent(eventData);

      if (StorageManager.isSent(event.eventId)) {
        logDebug("Duplicate event suppressed:", event.eventId);
        return;
      }

      const queue = StorageManager.getQueue();
      if (queue.some((e) => e.eventId === event.eventId)) {
        logDebug("Event already in queue:", event.eventId);
        return;
      }

      queue.push(event);
      StorageManager.saveQueue(queue);
      logDebug("Queued event:", event.type, event);

      if (queue.length >= BATCH_SIZE) {
        this.flushQueue();
      }
    }

    async sendEventToBackend(event) {
      const url = `${BACKEND_BASE_URL}${EVIDENCE_ENDPOINT}`;
      logDebug(`Transmitting event to backend: ${url}`, event);

      const payload = {
        timestamp: event.timestamp,
        source: event.source,
        type: event.type,
        category: event.category,
        identityAttributeIds: event.identityAttributeIds || [],
        value: event.value,
        baseWeight: event.baseWeight,
        metadata: event.metadata || {},
        simulated: event.simulated || false,
      };

      const authToken = StorageManager.getAuthToken();
      const headers = {
        "Content-Type": "application/json",
      };
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }

      if (typeof GM_xmlhttpRequest === "function") {
        return new Promise((resolve, reject) => {
          GM_xmlhttpRequest({
            method: "POST",
            url: url,
            headers: headers,
            data: JSON.stringify(payload),
            onload: (res) => {
              if (res.status >= 200 && res.status < 300) {
                try {
                  resolve(JSON.parse(res.responseText));
                } catch (e) {
                  resolve({ success: true });
                }
              } else {
                reject(new Error(`HTTP error ${res.status}: ${res.responseText}`));
              }
            },
            onerror: (err) => reject(new Error("GM_xmlhttpRequest transport error")),
          });
        });
      }

      const response = await fetch(url, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      return await response.json();
    }

    async flushQueue() {
      if (this.isFlushing) return;
      const queue = StorageManager.getQueue();
      if (queue.length === 0) return;

      this.isFlushing = true;
      logDebug(`Flushing ${queue.length} pending events...`);

      const remainingQueue = [...queue];
      let processedCount = 0;

      for (const event of queue) {
        try {
          await this.sendEventToBackend(event);
          StorageManager.markSent(event.eventId);
          remainingQueue.shift();
          processedCount++;
          this.retryAttempts = 0;
        } catch (error) {
          logDebug("Failed to transmit event to backend:", error.message);
          this.scheduleRetry();
          break;
        }
      }

      StorageManager.saveQueue(remainingQueue);
      this.isFlushing = false;
      logDebug(`Flush cycle complete. Transmitted ${processedCount} events.`);
    }

    scheduleRetry() {
      if (this.retryTimer) return;
      this.retryAttempts++;
      const delay = Math.min(
        INITIAL_RETRY_DELAY_MS * Math.pow(BACKOFF_FACTOR, this.retryAttempts - 1),
        MAX_RETRY_DELAY_MS
      );

      logDebug(`Scheduling retry attempt #${this.retryAttempts} in ${delay}ms`);
      this.retryTimer = setTimeout(() => {
        this.retryTimer = null;
        this.flushQueue();
      }, delay);
    }
  }

  // =========================================================================
  // FOCUS DRIFT DETECTOR
  // =========================================================================
  class FocusDriftDetector {
    constructor(client, platform) {
      this.client = client;
      this.platform = platform;
      this.scrollHistory = [];
      this.scrollSessionStart = null;
      this.lastScrollTime = null;
      this.reelCount = 0;
      this.totalReelDwellSec = 0;
      this.driftTriggered = {
        scrollCount: false,
        scrollDuration: false,
        reelCount: false,
        reelDwell: false,
      };
    }

    recordScroll() {
      const now = Date.now();
      if (!this.scrollSessionStart || now - this.lastScrollTime > 4000) {
        this.scrollSessionStart = now;
        this.scrollHistory = [now];
        this.driftTriggered.scrollCount = false;
        this.driftTriggered.scrollDuration = false;
      } else {
        this.scrollHistory.push(now);
      }
      this.lastScrollTime = now;

      this.scrollHistory = this.scrollHistory.filter((t) => now - t <= 4000);
      const scrollDurationSec = Math.round((now - this.scrollSessionStart) / 1000);

      if (this.scrollHistory.length >= 5 && !this.driftTriggered.scrollCount) {
        this.driftTriggered.scrollCount = true;
        this.emitDrift("excessive_continuous_scrolling", this.scrollHistory.length, {
          continuousScrolls: this.scrollHistory.length,
          scrollDurationSec,
        });
      }

      if (scrollDurationSec >= 30 && !this.driftTriggered.scrollDuration) {
        this.driftTriggered.scrollDuration = true;
        this.emitDrift("long_continuous_scrolling", scrollDurationSec, {
          scrollDurationSec,
          scrollCount: this.scrollHistory.length,
        });
      }
    }

    recordReelView(dwellSec = 0) {
      this.reelCount++;
      this.totalReelDwellSec += Number(dwellSec);

      if (this.reelCount >= 3 && !this.driftTriggered.reelCount) {
        this.driftTriggered.reelCount = true;
        this.emitDrift("excessive_reel_consumption", this.reelCount, {
          reelCount: this.reelCount,
          totalReelDwellSec: this.totalReelDwellSec,
        });
      }

      if (this.totalReelDwellSec >= 60 && !this.driftTriggered.reelDwell) {
        this.driftTriggered.reelDwell = true;
        this.emitDrift("excessive_reel_dwell", this.totalReelDwellSec, {
          reelCount: this.reelCount,
          totalReelDwellSec: this.totalReelDwellSec,
        });
      }
    }

    emitDrift(type, value, metadata) {
      if (!this.client) return;
      this.client.enqueue({
        source: this.platform,
        type: `focus_drift_${type}`,
        category: "focus_drift",
        value: Number(value),
        baseWeight: 0.8,
        metadata: {
          driftType: type,
          platform: this.platform,
          ...metadata,
        },
      });
    }
  }

  // =========================================================================
  // INSTAGRAM TRACKER
  // =========================================================================
  class InstagramTracker {
    constructor(client, focusDetector) {
      this.client = client;
      this.focusDetector = focusDetector;
      this.currentPath = window.location.pathname;
      this.activeFeedType = null;
      this.feedEntryTime = null;
      this.scrollCount = 0;
      this.scrollTicking = false;
      this.lastReelUrl = null;
      this.reelStartTime = null;
    }

    start() {
      if (this.isIgnoredPath(this.currentPath)) return;

      this.client.enqueue({
        source: "instagram",
        type: "session_started",
        category: "passive_learning",
        value: 1.0,
        metadata: { path: this.currentPath },
      });

      this.evaluateFeedContext(this.currentPath);
      this.setupScrollListener();
      this.setupVisibilityListener();
      this.setupSPANavigationHooks();
      this.setupReelObserver();
    }

    isIgnoredPath(path) {
      const ignored = ["/accounts/login", "/direct/", "/explore/locations/", "/settings/"];
      return ignored.some((p) => path.startsWith(p));
    }

    evaluateFeedContext(path) {
      const prevFeed = this.activeFeedType;

      if (this.isIgnoredPath(path)) {
        if (prevFeed) this.exitCurrentFeed();
        return;
      }

      let newFeed = "general";
      if (path === "/" || path === "/feed/") {
        newFeed = "home_feed";
      } else if (path.startsWith("/reels/") || path.startsWith("/reel/")) {
        newFeed = "reels_feed";
      } else if (path.split("/").filter(Boolean).length === 1) {
        newFeed = "profile_feed";
      }

      if (prevFeed !== newFeed) {
        if (prevFeed) this.exitCurrentFeed();
        this.activeFeedType = newFeed;
        this.feedEntryTime = Date.now();

        this.client.enqueue({
          source: "instagram",
          type: "feed_entered",
          category: "passive_learning",
          value: 1.0,
          metadata: { feedType: newFeed, path },
        });

        if (newFeed === "reels_feed") {
          this.trackReelStart(path);
        }
      }
    }

    exitCurrentFeed() {
      if (!this.activeFeedType || !this.feedEntryTime) return;
      const dwellSeconds = Math.round((Date.now() - this.feedEntryTime) / 1000);

      this.client.enqueue({
        source: "instagram",
        type: "feed_exited",
        category: "passive_learning",
        value: Number(dwellSeconds),
        metadata: {
          feedType: this.activeFeedType,
          dwellSeconds,
          totalScrolls: this.scrollCount,
        },
      });

      if (this.activeFeedType === "reels_feed") {
        this.trackReelEnd(dwellSeconds);
      }

      this.activeFeedType = null;
      this.feedEntryTime = null;
      this.scrollCount = 0;
    }

    setupScrollListener() {
      window.addEventListener(
        "scroll",
        () => {
          if (!this.scrollTicking) {
            window.requestAnimationFrame(() => {
              this.handleScroll();
              this.scrollTicking = false;
            });
            this.scrollTicking = true;
          }
        },
        { passive: true }
      );
    }

    handleScroll() {
      if (this.isIgnoredPath(window.location.pathname)) return;
      this.scrollCount++;
      if (this.focusDetector) {
        this.focusDetector.recordScroll();
      }

      if (this.scrollCount % 10 === 0) {
        this.client.enqueue({
          source: "instagram",
          type: "feed_scroll",
          category: "passive_learning",
          value: 10,
          metadata: {
            feedType: this.activeFeedType || "general",
            scrollCount: this.scrollCount,
          },
        });
      }
    }

    setupVisibilityListener() {
      document.addEventListener("visibilitychange", () => {
        const isHidden = document.visibilityState === "hidden";
        this.client.enqueue({
          source: "instagram",
          type: isHidden ? "tab_hidden" : "tab_visible",
          category: "passive_learning",
          value: 1.0,
          metadata: {
            activeFeed: this.activeFeedType,
            path: window.location.pathname,
          },
        });

        if (isHidden && this.activeFeedType) {
          this.exitCurrentFeed();
        } else if (!isHidden && !this.activeFeedType) {
          this.evaluateFeedContext(window.location.pathname);
        }
      });
    }

    setupSPANavigationHooks() {
      const handleLocationChange = () => {
        const newPath = window.location.pathname;
        if (newPath !== this.currentPath) {
          this.client.enqueue({
            source: "instagram",
            type: "spa_navigation",
            category: "passive_learning",
            value: 1.0,
            metadata: { from: this.currentPath, to: newPath },
          });
          this.currentPath = newPath;
          this.evaluateFeedContext(newPath);
        }
      };

      const origPushState = history.pushState;
      history.pushState = function (...args) {
        origPushState.apply(this, args);
        handleLocationChange();
      };

      const origReplaceState = history.replaceState;
      history.replaceState = function (...args) {
        origReplaceState.apply(this, args);
        handleLocationChange();
      };

      window.addEventListener("popstate", handleLocationChange);
      window.addEventListener("hashchange", handleLocationChange);
    }

    trackReelStart(path) {
      this.lastReelUrl = path;
      this.reelStartTime = Date.now();
    }

    trackReelEnd(dwellSeconds) {
      if (!this.reelStartTime) return;
      const durationSec = Math.max(1, dwellSeconds || Math.round((Date.now() - this.reelStartTime) / 1000));

      this.client.enqueue({
        source: "instagram",
        type: "reel_view",
        category: "passive_learning",
        value: Number(durationSec),
        metadata: {
          reelUrl: this.lastReelUrl,
          dwellSeconds: durationSec,
        },
      });

      if (this.focusDetector) {
        this.focusDetector.recordReelView(durationSec);
      }

      this.lastReelUrl = null;
      this.reelStartTime = null;
    }

    setupReelObserver() {
      const observer = new MutationObserver(() => {
        if (window.location.pathname.includes("/reel")) {
          const video = document.querySelector("video");
          if (video && video !== this.activeVideoElement) {
            this.activeVideoElement = video;
            this.trackReelStart(window.location.pathname);
          }
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  // =========================================================================
  // FACEBOOK TRACKER
  // =========================================================================
  class FacebookTracker {
    constructor(client, focusDetector) {
      this.client = client;
      this.focusDetector = focusDetector;
      this.currentPath = window.location.pathname;
      this.activeFeedType = null;
      this.feedEntryTime = null;
      this.scrollCount = 0;
      this.scrollTicking = false;
      this.lastWatchUrl = null;
      this.watchStartTime = null;
    }

    start() {
      if (this.isIgnoredPath(this.currentPath)) return;

      this.client.enqueue({
        source: "facebook",
        type: "session_started",
        category: "passive_learning",
        value: 1.0,
        metadata: { path: this.currentPath },
      });

      this.evaluateFeedContext(this.currentPath);
      this.setupScrollListener();
      this.setupVisibilityListener();
      this.setupSPANavigationHooks();
      this.setupWatchObserver();
    }

    isIgnoredPath(path) {
      const ignored = ["/messages", "/marketplace", "/adsmanager", "/settings", "/login.php"];
      return ignored.some((p) => path.startsWith(p));
    }

    evaluateFeedContext(path) {
      const prevFeed = this.activeFeedType;

      if (this.isIgnoredPath(path)) {
        if (prevFeed) this.exitCurrentFeed();
        return;
      }

      let newFeed = "general";
      if (path === "/" || path === "/home.php" || path.startsWith("/newsfeed")) {
        newFeed = "home_feed";
      } else if (path.startsWith("/watch") || path.startsWith("/reel") || path.startsWith("/reels")) {
        newFeed = "watch_reels_feed";
      } else if (path.startsWith("/groups/")) {
        newFeed = "groups_feed";
      } else if (path.split("/").filter(Boolean).length === 1) {
        newFeed = "profile_timeline";
      }

      if (prevFeed !== newFeed) {
        if (prevFeed) this.exitCurrentFeed();
        this.activeFeedType = newFeed;
        this.feedEntryTime = Date.now();

        this.client.enqueue({
          source: "facebook",
          type: "feed_entered",
          category: "passive_learning",
          value: 1.0,
          metadata: { feedType: newFeed, path },
        });

        if (newFeed === "watch_reels_feed") {
          this.trackWatchStart(path);
        }
      }
    }

    exitCurrentFeed() {
      if (!this.activeFeedType || !this.feedEntryTime) return;
      const dwellSeconds = Math.round((Date.now() - this.feedEntryTime) / 1000);

      this.client.enqueue({
        source: "facebook",
        type: "feed_exited",
        category: "passive_learning",
        value: Number(dwellSeconds),
        metadata: {
          feedType: this.activeFeedType,
          dwellSeconds,
          totalScrolls: this.scrollCount,
        },
      });

      if (this.activeFeedType === "watch_reels_feed") {
        this.trackWatchEnd(dwellSeconds);
      }

      this.activeFeedType = null;
      this.feedEntryTime = null;
      this.scrollCount = 0;
    }

    setupScrollListener() {
      window.addEventListener(
        "scroll",
        () => {
          if (!this.scrollTicking) {
            window.requestAnimationFrame(() => {
              this.handleScroll();
              this.scrollTicking = false;
            });
            this.scrollTicking = true;
          }
        },
        { passive: true }
      );
    }

    handleScroll() {
      if (this.isIgnoredPath(window.location.pathname)) return;
      this.scrollCount++;
      if (this.focusDetector) {
        this.focusDetector.recordScroll();
      }

      if (this.scrollCount % 10 === 0) {
        this.client.enqueue({
          source: "facebook",
          type: "feed_scroll",
          category: "passive_learning",
          value: 10,
          metadata: {
            feedType: this.activeFeedType || "general",
            scrollCount: this.scrollCount,
          },
        });
      }
    }

    setupVisibilityListener() {
      document.addEventListener("visibilitychange", () => {
        const isHidden = document.visibilityState === "hidden";
        this.client.enqueue({
          source: "facebook",
          type: isHidden ? "tab_hidden" : "tab_visible",
          category: "passive_learning",
          value: 1.0,
          metadata: {
            activeFeed: this.activeFeedType,
            path: window.location.pathname,
          },
        });

        if (isHidden && this.activeFeedType) {
          this.exitCurrentFeed();
        } else if (!isHidden && !this.activeFeedType) {
          this.evaluateFeedContext(window.location.pathname);
        }
      });
    }

    setupSPANavigationHooks() {
      const handleLocationChange = () => {
        const newPath = window.location.pathname;
        if (newPath !== this.currentPath) {
          this.client.enqueue({
            source: "facebook",
            type: "spa_navigation",
            category: "passive_learning",
            value: 1.0,
            metadata: { from: this.currentPath, to: newPath },
          });
          this.currentPath = newPath;
          this.evaluateFeedContext(newPath);
        }
      };

      const origPushState = history.pushState;
      history.pushState = function (...args) {
        origPushState.apply(this, args);
        handleLocationChange();
      };

      const origReplaceState = history.replaceState;
      history.replaceState = function (...args) {
        origReplaceState.apply(this, args);
        handleLocationChange();
      };

      window.addEventListener("popstate", handleLocationChange);
      window.addEventListener("hashchange", handleLocationChange);
    }

    trackWatchStart(path) {
      this.lastWatchUrl = path;
      this.watchStartTime = Date.now();
    }

    trackWatchEnd(dwellSeconds) {
      if (!this.watchStartTime) return;
      const durationSec = Math.max(1, dwellSeconds || Math.round((Date.now() - this.watchStartTime) / 1000));

      this.client.enqueue({
        source: "facebook",
        type: "reel_view",
        category: "passive_learning",
        value: Number(durationSec),
        metadata: {
          watchUrl: this.lastWatchUrl,
          dwellSeconds: durationSec,
        },
      });

      if (this.focusDetector) {
        this.focusDetector.recordReelView(durationSec);
      }

      this.lastWatchUrl = null;
      this.watchStartTime = null;
    }

    setupWatchObserver() {
      const observer = new MutationObserver(() => {
        if (window.location.pathname.includes("/watch") || window.location.pathname.includes("/reel")) {
          const video = document.querySelector("video");
          if (video && video !== this.activeVideoElement) {
            this.activeVideoElement = video;
            this.trackWatchStart(window.location.pathname);
          }
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  }

  // =========================================================================
  // YOUTUBE TRACKER
  // =========================================================================
  class YouTubeTracker {
    constructor(client, focusDetector) {
      this.client = client;
      this.focusDetector = focusDetector;
      this.currentPath = window.location.pathname + window.location.search;
      this.activeSurface = null;
      this.surfaceEntryTime = null;
      this.scrollCount = 0;
      this.scrollTicking = false;
      this.watchStartTime = null;
      this.lastWatchUrl = null;
    }

    start() {
      this.client.enqueue({
        source: "youtube",
        type: "session_started",
        category: "passive_learning",
        value: 1.0,
        metadata: { path: this.currentPath },
      });

      this.evaluateSurface(this.currentPath);
      this.setupScrollListener();
      this.setupVisibilityListener();
      this.setupSPANavigationHooks();
      this.setupWatchObserver();
    }

    evaluateSurface(pathWithQuery) {
      const path = pathWithQuery.split("?")[0] || "/";
      let surface = "general";
      if (path === "/" || path === "/feed") surface = "home_feed";
      else if (path.startsWith("/shorts")) surface = "shorts_feed";
      else if (path.startsWith("/watch") || pathWithQuery.includes("v=")) surface = "watch_page";
      else if (path.startsWith("/results")) surface = "search_results";

      if (this.activeSurface !== surface) {
        if (this.activeSurface) this.exitCurrentSurface();
        this.activeSurface = surface;
        this.surfaceEntryTime = Date.now();
        this.client.enqueue({
          source: "youtube",
          type: "feed_entered",
          category: "passive_learning",
          value: 1.0,
          metadata: { feedType: surface, path: pathWithQuery },
        });
        if (surface === "shorts_feed" || surface === "watch_page") {
          this.trackWatchStart(pathWithQuery);
        }
      }
    }

    exitCurrentSurface() {
      if (!this.activeSurface || !this.surfaceEntryTime) return;
      const dwellSeconds = Math.round((Date.now() - this.surfaceEntryTime) / 1000);
      this.client.enqueue({
        source: "youtube",
        type: "feed_exited",
        category: "passive_learning",
        value: Number(dwellSeconds),
        metadata: {
          feedType: this.activeSurface,
          dwellSeconds,
          totalScrolls: this.scrollCount,
        },
      });
      if (this.activeSurface === "shorts_feed" || this.activeSurface === "watch_page") {
        this.trackWatchEnd(dwellSeconds);
      }
      this.activeSurface = null;
      this.surfaceEntryTime = null;
      this.scrollCount = 0;
    }

    setupScrollListener() {
      window.addEventListener(
        "scroll",
        () => {
          if (!this.scrollTicking) {
            window.requestAnimationFrame(() => {
              this.scrollCount++;
              if (this.focusDetector) this.focusDetector.recordScroll();
              if (this.scrollCount % 10 === 0) {
                this.client.enqueue({
                  source: "youtube",
                  type: "feed_scroll",
                  category: "passive_learning",
                  value: 10,
                  metadata: {
                    feedType: this.activeSurface || "general",
                    scrollCount: this.scrollCount,
                  },
                });
              }
              this.scrollTicking = false;
            });
            this.scrollTicking = true;
          }
        },
        { passive: true }
      );
    }

    setupVisibilityListener() {
      document.addEventListener("visibilitychange", () => {
        const isHidden = document.visibilityState === "hidden";
        this.client.enqueue({
          source: "youtube",
          type: isHidden ? "tab_hidden" : "tab_visible",
          category: "passive_learning",
          value: 1.0,
          metadata: { activeFeed: this.activeSurface, path: window.location.pathname },
        });
        if (isHidden && this.activeSurface) this.exitCurrentSurface();
        else if (!isHidden && !this.activeSurface) {
          this.evaluateSurface(window.location.pathname + window.location.search);
        }
      });
    }

    setupSPANavigationHooks() {
      const handleLocationChange = () => {
        const next = window.location.pathname + window.location.search;
        if (next !== this.currentPath) {
          this.client.enqueue({
            source: "youtube",
            type: "spa_navigation",
            category: "passive_learning",
            value: 1.0,
            metadata: { from: this.currentPath, to: next },
          });
          this.currentPath = next;
          this.evaluateSurface(next);
        }
      };
      const origPushState = history.pushState;
      history.pushState = function (...args) {
        origPushState.apply(this, args);
        handleLocationChange();
      };
      const origReplaceState = history.replaceState;
      history.replaceState = function (...args) {
        origReplaceState.apply(this, args);
        handleLocationChange();
      };
      window.addEventListener("popstate", handleLocationChange);
      window.addEventListener("yt-navigate-finish", handleLocationChange);
    }

    trackWatchStart(url) {
      this.lastWatchUrl = url;
      this.watchStartTime = Date.now();
    }

    trackWatchEnd(dwellSeconds) {
      if (!this.watchStartTime) return;
      const durationSec = Math.max(
        1,
        dwellSeconds || Math.round((Date.now() - this.watchStartTime) / 1000)
      );
      this.client.enqueue({
        source: "youtube",
        type: this.activeSurface === "shorts_feed" ? "reel_view" : "watch_view",
        category: "passive_learning",
        value: Number(durationSec),
        metadata: { watchUrl: this.lastWatchUrl, dwellSeconds: durationSec },
      });
      if (this.focusDetector && this.activeSurface === "shorts_feed") {
        this.focusDetector.recordReelView(durationSec);
      }
      this.lastWatchUrl = null;
      this.watchStartTime = null;
    }

    setupWatchObserver() {
      const observer = new MutationObserver(() => {
        const path = window.location.pathname;
        if (path.startsWith("/watch") || path.startsWith("/shorts")) {
          const video = document.querySelector("video");
          if (video && video !== this.activeVideoElement) {
            this.activeVideoElement = video;
            this.trackWatchStart(window.location.pathname + window.location.search);
          }
        }
      });
      observer.observe(document.documentElement, { childList: true, subtree: true });
    }
  }

  // =========================================================================
  // MAIN CONTROLLER INITIALIZATION
  // =========================================================================
  function isTrellisAppHost(host) {
    return TRELLIS_APP_HOSTS.includes(host);
  }

  function init() {
    setupCompanionDetection();

    const host = window.location.hostname;
    logDebug("Starting Trellis Companion on host:", host);

    // On the Trellis web app we only expose detection + auth bridging.
    if (isTrellisAppHost(host)) {
      logDebug("Trellis app host detected — companion bridge only (no site trackers).");
      return;
    }

    const client = new TelemetryClient();

    if (host.includes("instagram.com")) {
      const focusDetector = new FocusDriftDetector(client, "instagram");
      const tracker = new InstagramTracker(client, focusDetector);
      tracker.start();
    } else if (host.includes("facebook.com")) {
      const focusDetector = new FocusDriftDetector(client, "facebook");
      const tracker = new FacebookTracker(client, focusDetector);
      tracker.start();
    } else if (host.includes("youtube.com")) {
      const focusDetector = new FocusDriftDetector(client, "youtube");
      const tracker = new YouTubeTracker(client, focusDetector);
      tracker.start();
    }

    window.addEventListener("beforeunload", () => {
      client.flushQueue();
      client.destroy();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
