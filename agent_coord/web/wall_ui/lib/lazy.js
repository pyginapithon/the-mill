/* WALL_UI_LIB_LAZY - script/CSS single-flight loader + domain ensure (Wave 2 / #40).
 * Marker: WALL_UI_LIB_LAZY
 */
(function (global) {
  "use strict";

  var pending = {};
  var loaded = {};

  function loadScript(src) {
    src = String(src || "");
    if (!src) return Promise.resolve();
    if (loaded[src]) return Promise.resolve();
    if (pending[src]) return pending[src];
    pending[src] = new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.onload = function () {
        loaded[src] = true;
        delete pending[src];
        resolve();
      };
      s.onerror = function () {
        delete pending[src];
        reject(new Error("wallLoadScript failed: " + src));
      };
      (document.head || document.documentElement).appendChild(s);
    });
    return pending[src];
  }

  function loadCss(href) {
    href = String(href || "");
    if (!href) return Promise.resolve();
    if (loaded[href]) return Promise.resolve();
    if (pending[href]) return pending[href];
    var existing = document.querySelector('link[data-wall-lazy="' + href.replace(/"/g, "") + '"]');
    if (existing) {
      loaded[href] = true;
      return Promise.resolve();
    }
    pending[href] = new Promise(function (resolve, reject) {
      var link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.setAttribute("data-wall-lazy", href);
      link.onload = function () {
        loaded[href] = true;
        delete pending[href];
        resolve();
      };
      link.onerror = function () {
        delete pending[href];
        reject(new Error("wallLoadCss failed: " + href));
      };
      (document.head || document.documentElement).appendChild(link);
    });
    return pending[href];
  }

  /* Root-absolute hrefs: under /project|/station|/role pathname,
   * relative mail/mail.js would resolve to /project/mail/mail.js (404). */
  /* WALL_DOMAIN_PINS_WOW182: all domain JS/CSS root-absolute + tip bust. */
  var DOMAINS = {
    mail: {
      js: "/mail/mail.js?v=wow285",
      css: "/mail/mail.css?v=wow238",
      marker: "WALL_UI_DEFAULT_MAIL"
    },
    score: {
      js: "/score/score.js?v=wow182",
      css: "/score/score.css?v=wow238",
      marker: "WALL_UI_DEFAULT_SCORE"
    },
    todo: {
      js: "/todo/todo.js?v=wow182",
      css: "/todo/todo.css?v=wow238",
      marker: "WALL_UI_DEFAULT_TODO"
    }
  };

  function ensureDomain(name) {
    var d = DOMAINS[String(name || "").toLowerCase()];
    if (!d) return Promise.resolve(null);
    var jsP = global[d.marker]
      ? Promise.resolve()
      : loadScript(d.js);
    var cssP = loadCss(d.css).catch(function () { /* CSS missing is non-fatal */ });
    return Promise.all([jsP, cssP]).then(function () { return d.marker; });
  }


  /* Session first-paint split: glossary / floor map / admin invite load on demand. */
  var MODULES = {
    glossary: {
      js: "/glossary/glossary.js?v=wow285",
      marker: "WALL_UI_DEFAULT_GLOSSARY"
    },
    floorMap: {
      js: "/floor/map-paint.js?v=wow280",
      marker: "WALL_UI_DEFAULT_FLOOR_MAP"
    },
    adminInvite: {
      js: "/admin/invite.js?v=wow280",
      marker: "WALL_UI_DEFAULT_ADMIN_INVITE"
    }
  };

  function ensureModule(name) {
    var m = MODULES[String(name || "")];
    if (!m) return Promise.resolve(null);
    if (global[m.marker]) return Promise.resolve(m.marker);
    return loadScript(m.js).then(function () { return m.marker; });
  }

  global.wallLoadScript = loadScript;
  global.wallLoadCss = loadCss;
  global.wallEnsureDomain = ensureDomain;
  global.wallEnsureModule = ensureModule;
  global.WALL_UI_LIB_LAZY = "WALL_UI_LIB_LAZY";
  global.WALL_UI_LIB_LAZY_DOMAINS = Object.keys(DOMAINS);
  global.WALL_LAZY_MODULES = Object.keys(MODULES);
})(typeof window !== "undefined" ? window : globalThis);
