(function () {
  var d = document.getElementById("lang");
  if (!d) return;
  var sum = d.querySelector("summary");
  var items = function () { return Array.prototype.slice.call(d.querySelectorAll("a")); };
  function close(focus) { d.removeAttribute("open"); if (focus) sum.focus(); }
  document.addEventListener("click", function (e) { if (d.open && !d.contains(e.target)) close(false); });
  document.addEventListener("focusin", function (e) { if (d.open && !d.contains(e.target)) close(false); });
  d.addEventListener("keydown", function (e) {
    var list = items(), i = list.indexOf(document.activeElement);
    if (e.key === "Escape" && d.open) { e.preventDefault(); close(true); }
    else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!d.open) d.setAttribute("open", "");
      var n = e.key === "ArrowDown" ? i + 1 : i - 1;
      if (i === -1) n = e.key === "ArrowDown" ? 0 : list.length - 1;
      list[(n + list.length) % list.length].focus();
    } else if (e.key === "Home" && i > -1) { e.preventDefault(); list[0].focus(); }
    else if (e.key === "End" && i > -1) { e.preventDefault(); list[list.length - 1].focus(); }
  });
  d.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-lang]");
    if (a) { try { localStorage.setItem("lang", a.getAttribute("data-lang")); } catch (err) {} }
  });
})();
