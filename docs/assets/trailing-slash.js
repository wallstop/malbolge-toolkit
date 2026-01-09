(function () {
  // Ensure pages are served with a trailing slash so relative links resolve
  // correctly on GitHub Pages, even if the base URL is visited without it.
  if (typeof window === "undefined") return;
  var loc = window.location;

  // Skip file:// and URLs that already reference a file
  if (loc.protocol === "file:") return;
  if (/[./][^/]*\.[^/]*$/.test(loc.pathname)) return;

  if (!loc.pathname.endsWith("/")) {
    var newPath = loc.pathname + "/";
    var target = newPath + loc.search + loc.hash;
    window.location.replace(target);
  }
})();
