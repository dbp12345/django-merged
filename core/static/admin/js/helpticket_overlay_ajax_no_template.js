// минималистичный скрипт — находит id из URL и рендерит карточки в body
document.addEventListener("DOMContentLoaded", function () {
  try {
    var path = window.location.pathname.replace(/\/+$/, "").split("/");
    var changeIndex = path.indexOf("change");
    if (changeIndex === -1) return;
    var objectId = path[changeIndex - 1];
    if (!objectId) return;

    var endpoint = window.location.pathname.replace(/\/change\/?$/, "/tickets-json/");

    fetch(endpoint, { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw r; return r.json(); })
      .then(function (data) {
        if (!data || !Array.isArray(data.tickets) || data.tickets.length === 0) return;

        var container = document.createElement("div");
        container.id = "ticket-overlay-container";
        document.body.appendChild(container);

        // global close button
        var closeAll = document.createElement("button");
        closeAll.className = "ticket-close-all";
        closeAll.setAttribute("aria-label", "Close tickets");
        closeAll.textContent = "×";
        closeAll.addEventListener("click", function (e) {
          e.preventDefault();
          container.style.display = "none";
        });
        container.appendChild(closeAll);

        data.tickets.forEach(function (t) {
          var el = document.createElement("div");
          // классы для раскраски: status-<status>, priority-<priority>
          el.className = "ticket " + "status-" + cssSafe(t.status) + " " + "priority-" + cssSafe(t.priority);

          // close button for this ticket
          var closeBtn = document.createElement("button");
          closeBtn.className = "ticket-close";
          closeBtn.setAttribute("aria-label", "Close ticket");
          closeBtn.textContent = "×";
          closeBtn.addEventListener("click", function (ev) {
            ev.preventDefault();
            el.style.display = "none";
          });
          el.appendChild(closeBtn);

          // title
          var title = document.createElement("a");
          title.href = "/admin/core/helpticket/" + encodeURIComponent(t.id) + "/change/";
          title.target = "_blank";
          title.className = "ticket-title";
          title.textContent = t.title || ("#"+t.id);
          el.appendChild(title);



          var meta = document.createElement("div");
          meta.className = "ticket-meta";
          meta.innerHTML = (t.status ? "<span class='ticket-field ticket-field-status'>"+escapeHtml(t.status)+"</span>" : "")
                         + (t.priority ? " <span class='ticket-field ticket-field-priority'>"+escapeHtml(t.priority)+"</span>" : "");
          el.appendChild(meta);

          // var more = document.createElement("div");
          // more.className = "ticket-more";
          // more.innerHTML = "<small>For: " + (t.attached && t.attached.label ? escapeHtml(t.attached.label) : "—") + "</small><br>"
          //                + "<small>Assigned: " + (t.assigned_to ? escapeHtml(t.assigned_to) : "—") + "</small>";
          // el.appendChild(more);

          if (t.body) {
            var body = document.createElement("div");
            body.className = "ticket-body";
            body.textContent = t.body;
            el.appendChild(body);
          }

          if (t.document_url) {
            var a = document.createElement("a");
            a.href = t.document_url;
            a.target = "_blank";
            a.className = "ticket-doc";
            a.textContent = "document";
            el.appendChild(a);
          }


          container.appendChild(el);
        });
      })
      .catch(function (err) {
        // тихо — никуда не ломаем
        console && console.debug && console.debug("tickets overlay error", err);
      });

  } catch (e) {
    console && console.debug && console.debug("tickets overlay init failed", e);
  }

  function escapeHtml(s) {
    return String(s || "").replace(/[&<>"']/g, function (m) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"})[m]; });
  }
  function cssSafe(s) {
    return String(s || "").replace(/[^a-z0-9_\-]/gi, "-").toLowerCase();
  }
});
