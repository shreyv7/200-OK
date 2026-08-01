// ==UserScript==
// @name         Trellis Companion - Behavioral Telemetry Collector
// @namespace    http://trellis.ai/
// @version      1.0.0
// @description  Automatic behavioral telemetry tracking for TRELLIS Evidence Pipeline
// @author       TRELLIS Team
// @match        https://*.instagram.com/*
// @match        https://*.facebook.com/*
// @match        https://*.youtube.com/*
// @connect      localhost
// @connect      127.0.0.1
// @connect      *
// @downloadURL  http://localhost:8002/tampermonkey/trellis-telemetry.user.js
// @updateURL    http://localhost:8002/tampermonkey/trellis-telemetry.user.js
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @run-at       document-idle
// ==UserScript==

(function () {
  "use strict";

  // =========================================================================
  // CONFIGURATION & CONSTANTS
  // =========================================================================
  const VERSION = "1.0.0";
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
  // COMPANION DETECTION MECHANISM FOR WEBSITE
  // Allows TRELLIS web app to detect Companion presence without frontend build changes
  // =========================================================================
  function setupCompanionDetection() {
    try {
      // 1. Set custom attribute on <html> element
      document.documentElement.setAttribute("data-trellis-companion-installed", VERSION);

      // 2. Dispatch custom DOM event
      const customEvent = new CustomEvent("trellis:companion-ready", {
        detail: { installed: true, version: VERSION, active: true },
      });
      window.dispatchEvent(customEvent);

      // 3. Window postMessage ping/pong listener
      window.addEventListener("message", (event) => {
        if (event.data && event.data.type === "TRELLIS_COMPANION_PING") {
          window.postMessage(
            {
              type: "TRELLIS_COMPANION_PONG",
              installed: true,
              version: VERSION,
              active: true,
            },
            "*"
          );
        }
      });
      logDebug("Companion detection mechanism registered (Attribute, CustomEvent & postMessage).");
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

    createEvent({ source, type, category, value = 1.0, baseWeight = 0.5, metadata = {} }) {
      // Preferred source for first-party Tampermonkey client telemetry is "trellis"
      let backendSource = "trellis";
      if (
        ["github", "google_calendar", "youtube", "notion", "trellis", "x"].includes(source)
      ) {
        backendSource = source;
      }

      const event = {
        timestamp: new Date().toISOString(),
        source: backendSource,
        type: type,
        category: category,
        identityAttributeIds: [],
        value: Number(value),
        baseWeight: Number(baseWeight),
        metadata: {
          platform: source,
          originalSource: source,
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
  // MAIN CONTROLLER INITIALIZATION
  // =========================================================================
  function init() {
    setupCompanionDetection();

    const host = window.location.hostname;
    logDebug("Starting Trellis Companion on host:", host);

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
      const tracker = new InstagramTracker(client, focusDetector);
      tracker.start();
    }

    // Auto-cleanup on window unload
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
