/* WALL_UI_DEFAULT_FLOOR - thin shell module for default pack (fungible cut 5).
 * Path A: pack-overridable floor domain seam (ensure-paint contract + layout helpers).
 * Paint still mostly in board.html; packs override this file without forking whole board.
 * Marker: WALL_UI_DEFAULT_FLOOR
 */
(function (global) {
  "use strict";

  function floorStateRank(st) {
    var s = String(st || "").toLowerCase();
    if (s === "working" || s === "busy") return 3;
    if (s === "waiting" || s === "blocked") return 2;
    if (s === "idle") return 1;
    if (s === "stale" || s === "dead") return 0;
    return 1;
  }
  function floorHostOf(d, hostByOwner) {
    hostByOwner = hostByOwner || {};
    var owner = String((d && d.owner) || "").trim();
    if (!owner) return "";
    if (d && d.host) return String(d.host);
    return String(hostByOwner[owner] || "");
  }
  function floorLayout(desks) {
    desks = desks || [];
    var n = Math.max(desks.length, 1);
    var cx = 400, cy = 170, R = Math.min(140, 40 + n * 28);
    return desks.map(function (d, i) {
      var ang = -Math.PI / 2 + (2 * Math.PI * i) / n;
      var out = {};
      Object.keys(d || {}).forEach(function (k) { out[k] = d[k]; });
      out.x = cx + R * Math.cos(ang);
      out.y = cy + R * Math.sin(ang);
      return out;
    });
  }
  function floorEnsurePaintContract() {
    return {
      marker: "WALL_UI_DEFAULT_FLOOR",
      calls_paintFloorMode: true,
      uses_office_glance: true,
      rAF_second_paint: true,
      load_if_empty: true
    };
  }

  var api = {
    floorStateRank: floorStateRank,
    floorHostOf: floorHostOf,
    floorLayout: floorLayout,
    floorEnsurePaintContract: floorEnsurePaintContract
  };
  Object.keys(api).forEach(function (k) { global[k] = api[k]; });
  global.WallFloor = api;
  global.WALL_UI_DEFAULT_FLOOR = "WALL_UI_DEFAULT_FLOOR";
})(typeof window !== "undefined" ? window : globalThis);
