/**
 * TRELLIS Focus Drift Detector Module
 * Evaluates real-time scrolling and reel consumption thresholds to generate focus_drift EvidenceEvents.
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.FocusDriftDetector = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const DRIFT_THRESHOLDS = {
    CONTINUOUS_SCROLL_COUNT: 5,
    SCROLL_WINDOW_MS: 4000,
    LONG_SCROLL_DURATION_SEC: 30,
    REEL_COUNT_THRESHOLD: 3,
    REEL_DWELL_THRESHOLD_SEC: 60,
  };

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
      if (!this.scrollSessionStart || now - this.lastScrollTime > DRIFT_THRESHOLDS.SCROLL_WINDOW_MS) {
        // Reset scrolling session
        this.scrollSessionStart = now;
        this.scrollHistory = [now];
        this.driftTriggered.scrollCount = false;
        this.driftTriggered.scrollDuration = false;
      } else {
        this.scrollHistory.push(now);
      }
      this.lastScrollTime = now;

      // Filter scroll ticks within window
      this.scrollHistory = this.scrollHistory.filter(
        (t) => now - t <= DRIFT_THRESHOLDS.SCROLL_WINDOW_MS
      );

      const scrollDurationSec = Math.round((now - this.scrollSessionStart) / 1000);

      // Check Rule 1: Continuous scroll count > 5
      if (
        this.scrollHistory.length >= DRIFT_THRESHOLDS.CONTINUOUS_SCROLL_COUNT &&
        !this.driftTriggered.scrollCount
      ) {
        this.driftTriggered.scrollCount = true;
        this.emitDrift("excessive_continuous_scrolling", this.scrollHistory.length, {
          continuousScrolls: this.scrollHistory.length,
          scrollDurationSec,
          reason: `More than ${DRIFT_THRESHOLDS.CONTINUOUS_SCROLL_COUNT} continuous scrolls detected in short succession.`,
        });
      }

      // Check Rule 2: Long continuous scrolling session
      if (
        scrollDurationSec >= DRIFT_THRESHOLDS.LONG_SCROLL_DURATION_SEC &&
        !this.driftTriggered.scrollDuration
      ) {
        this.driftTriggered.scrollDuration = true;
        this.emitDrift("long_continuous_scrolling", scrollDurationSec, {
          scrollDurationSec,
          scrollCount: this.scrollHistory.length,
          reason: `Continuous scrolling duration exceeded ${DRIFT_THRESHOLDS.LONG_SCROLL_DURATION_SEC} seconds.`,
        });
      }
    }

    recordReelView(dwellSec = 0) {
      this.reelCount++;
      this.totalReelDwellSec += Number(dwellSec);

      // Check Rule 3: Excessive reel view count
      if (this.reelCount >= DRIFT_THRESHOLDS.REEL_COUNT_THRESHOLD && !this.driftTriggered.reelCount) {
        this.driftTriggered.reelCount = true;
        this.emitDrift("excessive_reel_consumption", this.reelCount, {
          reelCount: this.reelCount,
          totalReelDwellSec: this.totalReelDwellSec,
          reason: `Consumed ${this.reelCount} short-form reels/shorts in rapid succession.`,
        });
      }

      // Check Rule 4: Excessive reel dwell time
      if (
        this.totalReelDwellSec >= DRIFT_THRESHOLDS.REEL_DWELL_THRESHOLD_SEC &&
        !this.driftTriggered.reelDwell
      ) {
        this.driftTriggered.reelDwell = true;
        this.emitDrift("excessive_reel_dwell", this.totalReelDwellSec, {
          reelCount: this.reelCount,
          totalReelDwellSec: this.totalReelDwellSec,
          reason: `Total short-form reel dwell time exceeded ${DRIFT_THRESHOLDS.REEL_DWELL_THRESHOLD_SEC} seconds.`,
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
        baseWeight: 0.8, // Focus drift has higher impact weight on Identity Gap
        metadata: {
          driftType: type,
          platform: this.platform,
          ...metadata,
        },
      });
    }

    reset() {
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
  }

  return FocusDriftDetector;
});
