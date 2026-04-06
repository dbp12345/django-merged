document.addEventListener("DOMContentLoaded", function () {
    let breadcrumbs = document.querySelector("#grp-breadcrumbs ul");

    if (breadcrumbs) {
        let lastItem = breadcrumbs.querySelector("li:last-child");
        if (lastItem) {
            lastItem.innerHTML = lastItem.innerHTML.replace(/&rsaquo;|›/g, "").trim();
            if (lastItem.innerHTML == "Employees") {
                lastItem.innerHTML = "<a href=\"/admin/company/employees/\" onclick=\"document.getElementById('filter-panel').classList.remove('open'); localStorage.setItem('panelOpen', 'false');\" style=\"background-image: none;\">Employees</a>";
            }
        }

        let li_items = breadcrumbs.querySelectorAll("li");
        li_items.forEach(item => {
            if (item.innerHTML.trim() === "›") {
                item.remove();
            }
        });

        let items = breadcrumbs.querySelectorAll("li > a");
        const removeTexts = ["Company", "Training", "Firecrew", "Synchronization", "Core", "Dispatch"];
        items.forEach(item => {
            if (removeTexts.includes(item.textContent.trim())) {
                item.remove();
            }
        });
    }
});
