/**
 * TRELLIS Tampermonkey Telemetry Core Module
 * Verified against existing TRELLIS backend API (/api/v1/evidence & get_current_user authentication).
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.TrellisCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const CONFIG = {
    DEBUG: false,
    BACKEND_BASE_URL: "http://localhost:8002",
    EVIDENCE_ENDPOINT: "/api/v1/evidence",
    QUEUE_KEY: "trellis_telemetry_queue",
    SENT_IDS_KEY: "trellis_telemetry_sent_ids",
    AUTH_TOKEN_KEY: "trellis_auth_token",
    MAX_SENT_IDS: 500,
    BATCH_SIZE: 10,
    FLUSH_INTERVAL_MS: 5000,
    INITIAL_RETRY_DELAY_MS: 1000,
    MAX_RETRY_DELAY_MS: 60000,
    BACKOFF_FACTOR: 2,
  };

  function logDebug(...args) {
    if (CONFIG.DEBUG) {
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

  class StorageManager {
    static getQueue() {
      try {
        const item = localStorage.getItem(CONFIG.QUEUE_KEY);
        return item ? JSON.parse(item) : [];
      } catch (e) {
        logDebug("Error reading queue from localStorage", e);
        return [];
      }
    }

    static saveQueue(queue) {
      try {
        localStorage.setItem(CONFIG.QUEUE_KEY, JSON.stringify(queue));
      } catch (e) {
        logDebug("Error saving queue to localStorage", e);
      }
    }

    static getSentIds() {
      try {
        const item = localStorage.getItem(CONFIG.SENT_IDS_KEY);
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
          if (sent.length > CONFIG.MAX_SENT_IDS) {
            sent.shift();
          }
          localStorage.setItem(CONFIG.SENT_IDS_KEY, JSON.stringify(sent));
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
          const gmToken = GM_getValue(CONFIG.AUTH_TOKEN_KEY, null);
          if (gmToken) return gmToken;
        }
        return localStorage.getItem(CONFIG.AUTH_TOKEN_KEY) || null;
      } catch (e) {
        return null;
      }
    }
  }

  class TelemetryClient {
    constructor(customConfig = {}) {
      this.config = { ...CONFIG, ...customConfig };
      this.isFlushing = false;
      this.retryAttempts = 0;
      this.retryTimer = null;
      this.init();
    }

    init() {
      logDebug("Initializing Verified Telemetry Core Client...", this.config);
      window.addEventListener("online", () => {
        logDebug("Network connection restored. Flushing queue...");
        this.flushQueue();
      });

      setInterval(() => {
        this.flushQueue();
      }, this.config.FLUSH_INTERVAL_MS);

      setTimeout(() => this.flushQueue(), 1000);
    }

    createEvent({ source, type, category, value = 1.0, baseWeight = 0.5, metadata = {} }) {
      // Valid Pydantic SourceProviders: "github", "google_calendar", "youtube", "notion", "trellis", "x"
      // Preferred source for first-party Tampermonkey client telemetry is "trellis", embedding exact platform in metadata
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
      logDebug("Queued telemetry event:", event.type, event);

      if (queue.length >= this.config.BATCH_SIZE) {
        this.flushQueue();
      }
    }

    async sendEventToBackend(event) {
      const url = `${this.config.BACKEND_BASE_URL}${this.config.EVIDENCE_ENDPOINT}`;
      logDebug(`Posting event to backend endpoint: ${url}`, event);

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
            onerror: (err) => reject(new Error("GM_xmlhttpRequest failed")),
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
      logDebug(`Flushing ${queue.length} queued events...`);

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
      logDebug(`Flush cycle complete. Successfully transmitted ${processedCount} events.`);
    }

    scheduleRetry() {
      if (this.retryTimer) return;
      this.retryAttempts++;
      const delay = Math.min(
        this.config.INITIAL_RETRY_DELAY_MS * Math.pow(this.config.BACKOFF_FACTOR, this.retryAttempts - 1),
        this.config.MAX_RETRY_DELAY_MS
      );

      logDebug(`Scheduling retry attempt #${this.retryAttempts} in ${delay}ms`);
      this.retryTimer = setTimeout(() => {
        this.retryTimer = null;
        this.flushQueue();
      }, delay);
    }
  }

  return {
    CONFIG,
    logDebug,
    StorageManager,
    TelemetryClient,
  };
});
