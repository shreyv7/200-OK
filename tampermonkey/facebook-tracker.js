/**
 * TRELLIS Facebook Telemetry Tracker Module
 * Detects feed scrolling, Watch/Reels consumption, SPA navigation, and visibility states on facebook.com
 */

(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.FacebookTracker = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const IGNORED_PATHS = [
    "/messages",
    "/marketplace",
    "/adsmanager",
    "/settings",
    "/login.php",
    "/gaming/",
    "/groups/create",
    "/events/create",
  ];

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
      if (this.isIgnoredPath(this.currentPath)) {
        return;
      }

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
      return IGNORED_PATHS.some((ignored) => path.startsWith(ignored));
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

  return FacebookTracker;
});
