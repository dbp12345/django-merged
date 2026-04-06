document.addEventListener("DOMContentLoaded", function () {
    let settingsModal = document.getElementById("settings-modal");
    let closeSettingsBtn = settingsModal.querySelector(".close-modal");
    let contactsList = document.getElementById("contacts-list");
    let settingsChanged = false;
    let currentFilterId = null;

    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".open-advanced-settings");
        if (!btn) return;

        e.preventDefault();
        currentFilterId = btn.dataset.id;

        fetch(`/admin/columns-settings/${currentFilterId}/columns/`)
            .then(response => response.json())
            .then(data => {
                contactsList.innerHTML = "";
                data.forEach(setting => {
                    let li = document.createElement("li");
                    li.classList.add("contact-item");
                    li.setAttribute("data-name", setting.field_name);
                    li.innerHTML = `
                            <input type="checkbox" class="visibility-toggle" ${setting.visible ? "checked" : ""}>
                            ${setting.field_name}
                        `;
                    contactsList.appendChild(li);
                });

                new Sortable(contactsList, {
                    animation: 150,
                    onEnd: () => settingsChanged = true
                });

                document.querySelectorAll(".visibility-toggle").forEach(input => {
                    input.addEventListener("change", () => {
                        settingsChanged = true;
                    });
                });

                settingsModal.classList.add("open");
            })
            .catch(error => console.error("Settings load error:", error));
    });

    closeSettingsBtn.addEventListener("click", function () {
        settingsModal.classList.remove("open");
        if (settingsChanged) {
            saveSettings();
        }
    });

    function saveSettings() {
        let visibleFields = [];
        document.querySelectorAll(".contact-item").forEach(item => {
            let isChecked = item.querySelector(".visibility-toggle").checked;
            let name = item.getAttribute("data-name");
            if (isChecked) {
                visibleFields.push(name);
            }
        });

        fetch(`/admin/columns-settings-update/${currentFilterId}/columns/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({columns: visibleFields})
        })
            .then(response => response.json())
            .then(data => {
                console.log("Column settings updated");
                location.reload();
            })
            .catch(error => console.error("Settings save error:", error));
    }

    document.getElementById("select-all").addEventListener("click", () => {
        document.querySelectorAll(".visibility-toggle").forEach(input => {
            input.checked = true;
        });
        settingsChanged = true;
    });

    document.getElementById("deselect-all").addEventListener("click", () => {
        document.querySelectorAll(".visibility-toggle").forEach(input => {
            input.checked = false;
        });
        settingsChanged = true;
    });

    document.getElementById("sort-alpha").addEventListener("click", () => {
        const items = Array.from(contactsList.querySelectorAll(".contact-item"));
        items.sort((a, b) => {
            const nameA = a.getAttribute("data-name").toLowerCase();
            const nameB = b.getAttribute("data-name").toLowerCase();
            return nameA.localeCompare(nameB);
        });

        items.forEach(item => contactsList.appendChild(item));
        settingsChanged = true;
    });
});