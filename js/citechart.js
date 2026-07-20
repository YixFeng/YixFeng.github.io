(function () {
  var SVGNS = "http://www.w3.org/2000/svg";
  var W = 290;
  var H = 58;
  var TOP = 20;
  var BAR_DELAY = 90;
  var BAR_MS = 380;
  var CURVE_MS = 1000;
  var LABEL_MS = 450;
  var FALLBACK_DATA = {
    total: 31,
    hIndex: 2,
    years: [2024, 2025, 2026],
    perYear: [1, 10, 20]
  };

  function el(name, attrs) {
    var node = document.createElementNS(SVGNS, name);
    Object.keys(attrs).forEach(function (key) {
      node.setAttribute(key, attrs[key]);
    });
    return node;
  }

  function fmt(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function smoothPath(points) {
    var d = "M" + points[0][0] + " " + points[0][1];
    for (var i = 1; i < points.length - 1; i++) {
      var mx = (points[i][0] + points[i + 1][0]) / 2;
      var my = (points[i][1] + points[i + 1][1]) / 2;
      d += " Q" + points[i][0] + " " + points[i][1] + " " + mx + " " + my;
    }
    var last = points[points.length - 1];
    d += " T" + last[0] + " " + last[1];
    return d;
  }

  function render(host, data) {
    var years = data.years || [];
    var perYear = data.perYear || [];
    var n = Math.min(years.length, perYear.length);
    if (!n) return;

    var total = data.total || perYear.reduce(function (sum, value) {
      return sum + value;
    }, 0);
    var maxPerYear = Math.max.apply(null, perYear.slice(0, n));
    var cumulative = [];
    perYear.slice(0, n).reduce(function (sum, value) {
      cumulative.push(sum + value);
      return sum + value;
    }, 0);
    var maxCumulative = cumulative[cumulative.length - 1];

    var svg = el("svg", {
      viewBox: "0 0 " + W + " " + H,
      role: "img",
      "aria-label": fmt(total) + " citations on Google Scholar"
    });

    var gap = n > 1 ? 8 : 0;
    var barWidth = (W - gap * (n - 1)) / n;
    var area = H - TOP - 1;
    var points = [];

    for (var i = 0; i < n; i++) {
      var x = i * (barWidth + gap);
      var h = Math.max(3, (perYear[i] / maxPerYear) * area);
      var rect = el("rect", {
        class: "cite-bar",
        x: x.toFixed(1),
        y: (H - h).toFixed(1),
        width: barWidth.toFixed(1),
        height: h.toFixed(1),
        rx: 2
      });
      var title = el("title", {});
      title.textContent = years[i] + ": " + fmt(perYear[i]) + " citations";
      rect.appendChild(title);
      svg.appendChild(rect);
      points.push([x + barWidth / 2, H - 2 - (cumulative[i] / maxCumulative) * area]);
    }

    var curve = el("path", {
      class: "cite-curve",
      d: smoothPath(points),
      fill: "none"
    });
    svg.appendChild(curve);

    var label = el("text", {
      class: "cite-label",
      x: 0,
      y: 13
    });
    label.textContent =
      fmt(total) + " citations" + (data.hIndex ? " · h-index " + data.hIndex : "");
    svg.appendChild(label);

    host.appendChild(svg);

    var reduced =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !svg.querySelector("rect").animate) return;

    var bars = svg.querySelectorAll("rect");
    for (var b = 0; b < bars.length; b++) {
      bars[b].animate([{ transform: "scaleY(0)" }, { transform: "scaleY(1)" }], {
        duration: BAR_MS,
        delay: b * BAR_DELAY,
        easing: "cubic-bezier(0.25, 0.6, 0.35, 1)",
        fill: "backwards"
      });
    }

    var curveDelay = (n - 1) * BAR_DELAY + BAR_MS;
    var length = curve.getTotalLength();
    curve.style.strokeDasharray = length;
    curve.style.strokeDashoffset = 0;
    curve.animate([{ strokeDashoffset: length + "px" }, { strokeDashoffset: "0px" }], {
      duration: CURVE_MS,
      delay: curveDelay,
      easing: "ease-out",
      fill: "both"
    });
    label.animate([{ opacity: 0 }, { opacity: 1 }], {
      duration: LABEL_MS,
      delay: curveDelay + CURVE_MS,
      fill: "backwards"
    });
  }

  function init() {
    var host = document.getElementById("citeChart");
    if (!host || host.getAttribute("data-ready") || !window.fetch) return;
    host.setAttribute("data-ready", "1");
    fetch("data/citations.json")
      .then(function (response) {
        if (!response.ok) throw new Error("Citation data unavailable");
        return response.json();
      })
      .then(function (data) {
        render(host, data);
      })
      .catch(function () {
        render(host, FALLBACK_DATA);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
