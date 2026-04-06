document.addEventListener("DOMContentLoaded", function () {
    const STORAGE_KEY = "inlineGroupClosedStates";
    const savedStates = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");

    document.querySelectorAll(".inline-group[id]").forEach(function (group) {
        const id = group.id;

        if (savedStates[id]) {
            group.classList.add("closed");
        } else {
            group.classList.remove("closed");
        }

        const toggle = group.querySelector(".grp-collapse-handler");
        if (toggle) {
            toggle.addEventListener("click", function (e) {
                e.stopPropagation(); // на всякий случай, если что-то bubbling
                group.classList.toggle("closed");
                savedStates[id] = group.classList.contains("closed");
                localStorage.setItem(STORAGE_KEY, JSON.stringify(savedStates));
            });
        }
    });
});
