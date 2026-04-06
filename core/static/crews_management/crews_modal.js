function openCrewModal(title, dataUrl, crewId) {
    document.body.style.overflow = "hidden";

    const modal = document.getElementById("crew-modal");
    const titleElem = document.getElementById("crew-modal-title");
    const thead = modal.querySelector(".crew-header");
    const tbody = modal.querySelector(".crew-list");

    // titleElem.textContent = `Crew: ${title}`;
    titleElem.innerHTML = `Crew: ${title} <a href="/admin/cards/crew/?crew=${crewId}" target="_blank" rel="noopener noreferrer">(cards)</a>`;
    thead.innerHTML = "";
    tbody.innerHTML = "";

    fetch(dataUrl)
        .then(res => res.json())
        .then(json => {
            const records = json.data || [];
            if (records.length === 0) return;

            const columns = Object.keys(records[0]);

            // Заголовки
            const headerRow = document.createElement("tr");
            columns.forEach(col => {
                if (col === "id") return;
                const th = document.createElement("th");
                th.textContent = col;
                th.classList.add("sortable");
                th.dataset.column = col;
                headerRow.appendChild(th);
            });
            headerRow.appendChild(document.createElement("th"));  // Пустая для кнопок
            thead.appendChild(headerRow);

            // Строки
            records.forEach(row => {
                const tr = document.createElement("tr");
                tr.style.backgroundColor = "white";

                columns.forEach(col => {
                    if (col === "id") return;
                    const td = document.createElement("td");
                    td.innerHTML = row[col] || "";
                    tr.appendChild(td);
                });

                const tdBtns = document.createElement("td");
                tr.appendChild(tdBtns);

                tbody.appendChild(tr);
            });

            modal.classList.add("open");
            enableModalSorting();
        });
}

function enableModalSorting(modalSelector = ".modal", tableSelector = ".crew-table") {
    const table = document.querySelector(`${modalSelector} ${tableSelector}`);
    const headers = table.querySelectorAll("th.sortable");
    const tbody = table.querySelector("tbody");
    const storageKey = "crew_modal_sort";

    // Восстановить сортировку из localStorage
    let sortState = JSON.parse(localStorage.getItem(storageKey)) || {};

    const applySort = (col, direction) => {
        const rows = Array.from(tbody.querySelectorAll("tr"));
        const idx = Array.from(col.parentNode.children).indexOf(col);

        rows.sort((a, b) => {
            let valA = a.children[idx].innerText.trim();
            let valB = b.children[idx].innerText.trim();

            // Пытаемся сравнивать как число, если возможно
            let numA = parseFloat(valA.replace(/[^\d.]/g, ""));
            let numB = parseFloat(valB.replace(/[^\d.]/g, ""));

            if (!isNaN(numA) && !isNaN(numB)) {
                return direction === "asc" ? numA - numB : numB - numA;
            }

            return direction === "asc"
                ? valA.localeCompare(valB)
                : valB.localeCompare(valA);
        });

        rows.forEach(row => tbody.appendChild(row));

        // Сохраняем
        localStorage.setItem(storageKey, JSON.stringify({
            column: col.dataset.column,
            direction: direction
        }));

        updateSortIndicators(col, direction);
    };

    const updateSortIndicators = (activeCol, direction) => {
        headers.forEach(th => {
            th.classList.remove("asc", "desc");
            th.textContent = th.dataset.column; // жёстко сбрасываем заголовок
        });
        if (direction) {
            activeCol.classList.add(direction);
            activeCol.textContent = `${activeCol.dataset.column} ${direction === "asc" ? "▲" : "▼"}`;
        }
    };

    headers.forEach(col => {
        col.addEventListener("click", () => {
            const current = col.classList.contains("asc") ? "asc" : col.classList.contains("desc") ? "desc" : null;
            const next = current === "asc" ? "desc" : "asc";
            applySort(col, next);
        });
    });

    // Автоприменение сохранённой сортировки
    if (sortState.column && sortState.direction) {
        const col = Array.from(headers).find(th => th.dataset.column === sortState.column);
        if (col) applySort(col, sortState.direction);
    }
}

document.addEventListener("click", function (e) {
    const link = e.target.closest(".crew-name");
    if (!link) return;

    e.preventDefault();

    if (link.dataset.locked === "1") return;
    link.dataset.locked = "1";
    setTimeout(() => {
        delete link.dataset.locked;
    }, 2000);

    const crewName = link.textContent.trim();
    const dataUrl = link.getAttribute("data-content-employees");
    const crewId = link.getAttribute("data-crew-id");

    openCrewModal(crewName, dataUrl, crewId);
});


// Закрытие модалки по Close
document.addEventListener("click", function (e) {
    if (e.target.matches(".close-modal")) {
        e.target.closest(".modal").classList.remove("open");
        document.body.style.overflow = "";
    }
});

// Закрытие модалки по ESC
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        const openedModal = document.querySelector(".modal.open");
        if (openedModal) {
            openedModal.classList.remove("open");
            document.body.style.overflow = "";
        }
    }
});

// Закрытие модалки по клику вне контента
document.addEventListener("click", function (e) {
    const openedModal = document.querySelector(".modal.open");
    if (!openedModal) return;

    const isClickOutside = !e.target.closest(".modal-content");
    const isClickInsideModal = e.target.closest(".modal") === openedModal;

    if (isClickOutside && isClickInsideModal) {
        openedModal.classList.remove("open");
        document.body.style.overflow = "";
    }
});
