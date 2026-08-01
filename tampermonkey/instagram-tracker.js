/**
 * TRELLIS Instagram Telemetry Tracker Module
 * Detects feed scrolling, Reels consumption, SPA navigation, and visibility states on instagram.com
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.InstagramTracker = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const IGNORED_PATHS = [
    "/accounts/login",
    "/accounts/emailsignup",
    "/direct/",
    "/explore/locations/",
    "/settings/",
    "/privacy/",
  ];

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
      this.activeVideoObserver = null;
    }

    start() {
      if (this.isIgnoredPath(this.currentPath)) {
        return;
      }

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
      return IGNORED_PATHS.some((ignored) => path.startsWith(ignored));
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

      // Periodically emit scroll telemetry every 10 scroll ticks
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
      // Observe video element playback on Instagram Reels
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

  return InstagramTracker;
});
