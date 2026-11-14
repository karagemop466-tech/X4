// Shared navigation: mark active page; suggestions review state uses localStorage.
(function () {
  var here = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  document.querySelectorAll(".sidebar nav a").forEach(function (a) {
    var href = (a.getAttribute("href") || "").toLowerCase();
    if (href === here) a.classList.add("active");
    else a.classList.remove("active");
  });
})();
