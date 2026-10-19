/* WALL_UI_DEFAULT_GLOSSARY - name catalog paint (lazy; not on Session first paint).
 * Marker: WALL_UI_DEFAULT_GLOSSARY
 */
(function (global) {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  var _nameCatalog = null;

  function paintGlossaryFrom(rows) {
    var el = document.getElementById("glossary-body");
    if (!el) return;
    if (!rows) {
      el.innerHTML = '<div class="idle">Names are not on this floor yet.</div>';
      return;
    }
    var order = ["roster", "desk", "label", "res", "tree", "other"];
    var titles = {
      roster: "Roster",
      desk: "Desks",
      label: "Labels",
      res: "Resources",
      tree: "Trees",
      other: "Other"
    };
    var buckets = {};
    order.forEach(function (k) { buckets[k] = []; });
    var unnamed = 0;
    rows.forEach(function (r) {
      if (r && r.hidden) { unnamed += Number(r.n) || 0; return; }
      if (r.kind === "kpi") return;
      var k = buckets[r.kind] ? r.kind : "other";
      if (r.name) buckets[k].push({ name: String(r.name), deleted: !!r.deleted });
    });
    order.forEach(function (k) {
      buckets[k].sort(function (a, b) {
        return (a.deleted - b.deleted) || a.name.localeCompare(b.name);
      });
    });
    function sec(title, names, extra) {
      var body = names.length
        ? names.map(function (n) {
            return '<span class="name-id' + (n.deleted ? " deleted" : "") + '">' +
              esc(n.name) +
              (n.deleted ? ' <span class="name-n">deleted</span>' : "") +
              "</span>";
          }).join("")
        : "";
      var tail = extra || "";
      if (!body && !tail) {
        return '<div class="name-sec"><span class="name-h">' + esc(title) +
          '</span><span class="name-empty">none</span></div>';
      }
      return '<div class="name-sec"><span class="name-h">' + esc(title) +
        "</span>" + body + tail + "</div>";
    }
    var treeExtra = unnamed
      ? '<span class="name-id">unnamed <span class="name-n">| ' + unnamed + "</span></span>"
      : "";
    var html = order
      .filter(function (k) { return k !== "other" || buckets[k].length; })
      .map(function (k) { return sec(titles[k], buckets[k], k === "tree" ? treeExtra : ""); })
      .join("");
    if (el.dataset.sig === html) return;
    el.dataset.sig = html;
    el.innerHTML = html;
  }

  function paintGlossary() {
    var el = document.getElementById("glossary-body");
    if (!el) return;
    if (_nameCatalog) {
      paintGlossaryFrom(_nameCatalog);
      return;
    }
    if (el.dataset.loading === "1") return;
    el.dataset.loading = "1";
    el.innerHTML = '<div class="idle">Loading names...</div>';
    fetch("/api/v1/names?project=Office", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) {
        _nameCatalog = (j && j.catalog) || [];
        el.dataset.loading = "";
        paintGlossaryFrom(_nameCatalog);
      })
      .catch(function () {
        el.dataset.loading = "";
        paintGlossaryFrom(null);
      });
  }

  function setCatalog(rows) {
    _nameCatalog = rows || null;
  }

  global.WallGlossary = {
    paint: paintGlossary,
    paintFrom: paintGlossaryFrom,
    setCatalog: setCatalog,
    marker: "WALL_UI_DEFAULT_GLOSSARY"
  };
  global.WALL_UI_DEFAULT_GLOSSARY = "WALL_UI_DEFAULT_GLOSSARY";
})(typeof window !== "undefined" ? window : globalThis);
