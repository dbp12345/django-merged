document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("tr").forEach((row) => {
        const statusCell = row.querySelector("td.field-status select");
        if (!statusCell) return;

        const val = statusCell.value.trim().toLowerCase();

        if (val === "on fire") {
            row.classList.add("on-fire-status");
        } else if (val === "scheduled") {
            row.classList.add("scheduled-status");
        } else if (val === "not on fire") {
            row.classList.add("not-on-fire-status");
        }
    });
});
