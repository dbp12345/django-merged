(function () {
    "use strict";
    const FIELDS = [
        "employees",
        "firecrew",
        "dispatch",
        "equipment_group",
        "saw",
        "radio",
        "phone",
        "truck",
        "equipment",
    ]; // Form ALLOWED_ATTACHMENT_FIELDS
    const FORM = "form#helpticket_form, form";

    const idFor = n => "id_" + n;
    const findRow = n => document.querySelector(".form-row.grp-row." + n) || document.querySelector(".grp-row." + n) || document.getElementById(idFor(n))?.closest(".form-row, .grp-row, .field-box") || null;
    const readText = r => r?.querySelector(".grp-readonly, .readonly, p, span")?.textContent?.trim() || "";

    // function hide(r){ if(r) r.style.visibility = "hidden"; }
    // function show(r){ if(r) r.style.visibility = "visible"; }
    function hide(r) {
        if (r) r.style.display = "none";
    }

    function show(r) {
        if (r) r.style.display = "";
    }

    function clearValue(name) {
        const inp = document.getElementById(idFor(name));
        if (inp) {
            inp.value = "";
            inp.dispatchEvent(new Event("change", {bubbles: true}));
            return;
        }
        const ro = findRow(name)?.querySelector(".grp-readonly, .readonly, p, span");
        if (ro) ro.textContent = "";
    }

    function showOnly(name) {
        for (const f of FIELDS) {
            const r = findRow(f);
            if (f === name) show(r); else {
                clearValue(f);
                hide(r);
            }
        }
    }

    function initOnce() {
        // если уже есть readonly заполнено — просто показать его и не рисовать селект
        for (const f of FIELDS) {
            const r = findRow(f);
            const txt = readText(r);
            if (txt && txt !== "-") {
                showOnly(f);
                return true;
            }
        }
        // вставим селект перед первой найденной строкой
        let ref = null;
        for (const f of FIELDS) {
            const r = findRow(f);
            if (r) {
                ref = r;
                break;
            }
        }
        if (!ref) return false;

        const wrapper = document.createElement("div");
        wrapper.className = "help-ticket-attach-wrapper";
        const sel = document.createElement("select");
        sel.id = "id_attached_type";
        sel.innerHTML = `<option value="">— none —</option>` + FIELDS.map(f => `<option value="${f}">${f}</option>`).join("");
        wrapper.appendChild(sel);
        ref.parentNode.insertBefore(wrapper, ref);

        // init state
        for (const f of FIELDS) {
            const inp = document.getElementById(idFor(f));
            const r = findRow(f);
            if (inp && inp.value) {
                sel.value = f;
                showOnly(f);
                break;
            }
            if (!inp && readText(r) && readText(r) !== "-") {
                sel.value = f;
                showOnly(f);
                break;
            }
        }
        sel.addEventListener("change", () => {
            if (!sel.value) {
                for (const f of FIELDS) hide(findRow(f));
                return;
            }
            showOnly(sel.value);
        });

        // клики по строкам делают их активными
        for (const f of FIELDS) {
            const r = findRow(f);
            if (!r) continue;
            r.style.cursor = "pointer";
            r.classList.add("field-catch")
            r.addEventListener("click", () => {
                sel.value = f;
                showOnly(f);
            });
        }
        return true;
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => {
        if (!initOnce()) {
            const root = document.querySelector(FORM) || document.body;
            new MutationObserver((m, obs) => {
                if (initOnce()) obs.disconnect();
            }).observe(root, {childList: true, subtree: true});
        }
    });
    else if (!initOnce()) {
        const root = document.querySelector(FORM) || document.body;
        new MutationObserver((m, obs) => {
            if (initOnce()) obs.disconnect();
        }).observe(root, {childList: true, subtree: true});
    }

})();
