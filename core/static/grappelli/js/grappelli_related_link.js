document.addEventListener("DOMContentLoaded", function() {
  "use strict";
  const SEL = "a.grp-related-widget-wrapper-link.change-related, a.change-related";

  const clean = href => {
    if (!href) return href;
    try {
      const u = new URL(href, location.href);
      u.searchParams.delete("_popup");
      u.searchParams.delete("_to_field");
      return u.href;
    } catch (e) {
      return href.replace(/([?&])_popup=1(&|$)/, (m,p1,p2)=> p2 === "&" ? p1 : "").replace(/[?&]$/,"");
    }
  };

  // привести в порядок существующие атрибуты
  document.querySelectorAll(SEL).forEach(a => {
    const raw = a.getAttribute("href") || a.getAttribute("data-href-template") || "";
    const cleaned = clean(raw);
    if (cleaned) {
      a.setAttribute("href", cleaned);
      if (a.hasAttribute("data-href-template")) a.setAttribute("data-href-template", cleaned);
    }
    a.removeAttribute("onclick");
    a.removeAttribute("onmousedown");
  });

  // перехват в capture — сработает раньше делегатов, которые могут открывать popup
  document.addEventListener("click", function(ev) {
    const a = ev.target && ev.target.closest && ev.target.closest(SEL);
    if (!a) return;
    const href = a.getAttribute("href") || a.getAttribute("data-href-template") || "";
    if (!href || href.indexOf("__fk__") !== -1) { ev.preventDefault(); ev.stopImmediatePropagation(); return; }
    ev.preventDefault();
    ev.stopImmediatePropagation();
    location.href = href;
  }, true);
});
