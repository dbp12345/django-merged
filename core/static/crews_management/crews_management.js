function loadEmployeesData() {
    fetch("/admin/crews-management/data/")
        .then(response => response.json())
        .then(data => {
            updateTables(data.employees, data.filter_counts);
            updateCrewZones(data.crews);
            spinnerOff();
        })
        .catch(error => console.error("Error loading employee data:", error));
}

function updateTables(employeesData, filterCounts) {
    document.querySelectorAll(".table-wrapper").forEach(wrapper => {
        let filterId = wrapper.getAttribute("data-filter-id");
        let tableBody = wrapper.querySelector("tbody");
        let counter = wrapper.querySelector(".filter-counter");
        let table = wrapper.querySelector("table");
        let headerRow = wrapper.querySelector("thead .dynamic-header-row");

        tableBody.innerHTML = "";
        headerRow.innerHTML = "";

        if (employeesData[filterId] && employeesData[filterId].length > 0) {
            // Получаем ключи, кроме id и status_color
            let firstEmployee = employeesData[filterId][0];
            let displayFields = Object.keys(firstEmployee).filter(k => !["id", "status_color"].includes(k));


            let infoTh = document.createElement("th");
            infoTh.textContent = "";  // пусто или можно "Info"
            headerRow.appendChild(infoTh);

            // Отрисовываем заголовки
            displayFields.forEach(field => {
                let th = document.createElement("th");
                th.classList.add("sortable");
                th.textContent = field;
                headerRow.appendChild(th);
            });

            let th = document.createElement("th");
            headerRow.appendChild(th);


            // Отрисовываем строки
            employeesData[filterId].forEach(employee => {
                let row = document.createElement("tr");
                row.classList.add("employee-row", "target");
                row.dataset.employeeId = employee.id;
                row.setAttribute("draggable", "true");
                row.style.backgroundColor = employee.status_color || "white";
                row.style.visibility = "visible"; // Ensure row is visible by default
                row.title = employee.status;

                // 🛈 Первая колонка
                let infoCell = document.createElement("td");
                let infoBtn = document.createElement("div");
                infoBtn.textContent = "ⓘ";
                infoBtn.classList.add("info-btn");
                infoBtn.addEventListener("click", function (e) {
                    getFireRunForEmployee(employee.id, e.pageX, e.pageY);
                });
                infoCell.appendChild(infoBtn);
                row.appendChild(infoCell);

                displayFields.forEach(key => {
                    let cell = document.createElement("td");
                    cell.textContent = employee[key] || "";
                    row.appendChild(cell);
                });

                let cell = document.createElement("td");
                let editBtn = document.createElement("div");
                editBtn.textContent = "➜";
                editBtn.classList.add("edit-btn");
                editBtn.addEventListener("click", function () {
                    editEmployeeById(employee.id);
                });
                cell.appendChild(editBtn);
                row.appendChild(cell);

                row.addEventListener("dragstart", function (event) {
                    let clone = row.cloneNode(true);
                    clone.classList.add("dragging-clone");
                    clone.style.position = "fixed";
                    clone.style.pointerEvents = "none";
                    clone.style.zIndex = "1000";
                    document.body.appendChild(clone);
                    event.dataTransfer.setData("text/plain", employee.id);
                });

                tableBody.appendChild(row);
            });

            // counter.textContent = filterCounts[filterId] || 0; /*это считаем на беке. Убрали для скорости*/
            counter.textContent = employeesData[filterId].length;
        } else {
            counter.textContent = "0";
        }

        enableSorting();

        if (table) {
            let currentSort = table.getAttribute("data-sort");
            let currentOrder = table.getAttribute("data-order");

            if (currentSort !== null) {
                sortTable(table, currentSort, currentOrder);
            }
        }
    });

    applySearchFilters();
    
    // Re-apply global search if active
    let globalSearchInput = document.getElementById("global-search-input");
    if (globalSearchInput && globalSearchInput.value.trim()) {
        globalEmployeeSearch();
    }
}

function sortCrewTable(table, columnIndex, order) {
    let tbody = table.querySelector("tbody");
    let rows = Array.from(tbody.querySelectorAll("tr"));

    // Отделяем boss-строку, если есть чекбокс с checked
    let bossRowIndex = rows.findIndex(row => {
        let checkbox = row.querySelector('input[type="checkbox"]');
        return checkbox && checkbox.checked;
    });

    let bossRow = null;
    if (bossRowIndex !== -1) {
        bossRow = rows.splice(bossRowIndex, 1)[0]; // удаляем из массива
    }

    rows.sort((rowA, rowB) => {
        let cellA = rowA.cells[columnIndex].textContent.trim();
        let cellB = rowB.cells[columnIndex].textContent.trim();

        let numA = parseFloat(cellA);
        let numB = parseFloat(cellB);

        if (!isNaN(numA) && !isNaN(numB)) {
            return order === "asc" ? numA - numB : numB - numA;
        }
        return order === "asc" ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
    });

    tbody.innerHTML = "";
    if (bossRow) tbody.appendChild(bossRow); // босс всегда первым
    rows.forEach(row => tbody.appendChild(row));
}


function crewZoneSortHandler(event) {
    let th = event.target;
    let table = th.closest("table");
    let columnIndex = th.cellIndex;
    let crewId = table.closest(".crew-zone").getAttribute("data-crew-id");

    let currentSort = localStorage.getItem(`crew_sort_${crewId}`);
    let currentOrder = localStorage.getItem(`crew_order_${crewId}`) || "asc";

    if (currentSort == columnIndex) {
        currentOrder = currentOrder === "asc" ? "desc" : "asc";
    } else {
        currentOrder = "asc";
    }

    localStorage.setItem(`crew_sort_${crewId}`, columnIndex);
    localStorage.setItem(`crew_order_${crewId}`, currentOrder);

    // убираем классы со всех th
    table.querySelectorAll("th").forEach(header => {
        header.classList.remove("sort-asc", "sort-desc");
    });

    th.classList.add(currentOrder === "asc" ? "sort-asc" : "sort-desc");

    sortCrewTable(table, columnIndex, currentOrder);
}


function enableCrewZoneSorting() {
    document.querySelectorAll(".crew-zone table thead th").forEach(th => {
        if (th.cellIndex >= 9) return; // Пропускаем колонку "X / ➜"

        th.classList.add("sortable");

        th.removeEventListener("click", crewZoneSortHandler); // защита от дублирования
        th.addEventListener("click", crewZoneSortHandler);
    });

    // Восстановление сортировки из localStorage
    document.querySelectorAll(".crew-zone table").forEach(table => {
        let crewId = table.closest(".crew-zone").getAttribute("data-crew-id");
        let sort = localStorage.getItem(`crew_sort_${crewId}`);
        let order = localStorage.getItem(`crew_order_${crewId}`);
        if (sort !== null && order) {
            sortCrewTable(table, parseInt(sort), order);
        }
    });

    document.querySelectorAll(".crew-zone table thead th").forEach(th => {
        if (th.cellIndex >= 5) return;

        let crewId = th.closest(".crew-zone").getAttribute("data-crew-id");
        let sort = localStorage.getItem(`crew_sort_${crewId}`);
        let order = localStorage.getItem(`crew_order_${crewId}`);

        if (sort !== null && parseInt(sort) === th.cellIndex) {
            th.classList.add(order === "desc" ? "sort-desc" : "sort-asc");
        }
    });
}

function updateCrewZones(crewData) {
    document.querySelectorAll(".crew-zone").forEach(zone => {
        let crewId = zone.getAttribute("data-crew-id");
        let tbody = zone.querySelector(".crew-list");
        let counter = zone.querySelector(".crew-counter");
        let counterForFFT1 = zone.querySelector(".crew-counter-fft1");
        let counterForMSPA = zone.querySelector(".crew-counter-mspa");
        let counterForSaw = zone.querySelector(".crew-counter-saw");
        let fft1Count = 0;
        let mspaCount = 0;
        let sawCount = 0;
        let thead = zone.querySelector(".crew-header");

        tbody.innerHTML = "";

        let employees = crewData?.[crewId]?.employees || [];
        let count = employees.length;

        if (thead) {
            thead.style.display = count > 0 ? "" : "none";
        }

        employees.forEach(emp => {
            let tr = document.createElement("tr");
            tr.dataset.employeeId = emp.id;
            tr.title = emp.status;
            tr.classList.add("target");
            tr.style.backgroundColor = emp.status_color || "white";
            tr.style.visibility = "visible"; // Ensure row is visible by default

            let crwbTd = document.createElement("td");
            crwbTd.classList.add("edit-crwb");

            let oneTd = document.createElement("td");

            oneTd.innerHTML = `<span class="clickable-name">${emp.one}</span>`;

            let infoBtn = document.createElement("div");
            infoBtn.textContent = "ⓘ";
            infoBtn.classList.add("info-btn");
            infoBtn.addEventListener("click", function (e) {
                getFireRunForEmployee(emp.id, e.pageX, e.pageY);
            });
            oneTd.appendChild(infoBtn);

            oneTd.classList.add("edit-one");
            oneTd.querySelector("span").addEventListener("click", function () {
                editEmployeeById(emp.id);
            });

            let twoTd = document.createElement("td");
            let twoSpan = document.createElement("span");
            let symbolSVG = '<svg width="10" height="10"><use href="#thin_empty"></use></svg>';
            const twoText = typeof emp?.two === "string" ? emp.two : "";
            const f1tFires = emp.rec_f1t_hotline_fires;
            const f1tDays = emp.rec_f1t_fire_days;
            const crwbFires = emp.rec_crwb_hotline_fires;
            const crwbDays = emp.rec_crwb_fire_days;

            if (twoText.includes("FFT1")) {
                if (crwbFires == 1) {
                    symbolSVG = '<svg width="10" height="10"><use href="#thin_bar1"></use></svg>';
                } else if (crwbFires == 2) {
                    symbolSVG = '<svg width="10" height="10"><use href="#thin_bar2"></use></svg>';
                } else if (crwbFires >= 3) {
                    if (crwbDays >= 15) {
                        symbolSVG = '<svg width="10" height="10"><use href="#thin_bar3_v"></use></svg>';
                    } else {
                        symbolSVG = '<svg width="10" height="10"><use href="#thin_bar3"></use></svg>';
                    }
                }
            } else if (twoText.includes("FFT2")) {
                if (f1tFires == 1) {
                    symbolSVG = '<svg width="10" height="10"><use href="#thin_bar1"></use></svg>';
                } else if (f1tFires == 2) {
                    symbolSVG = '<svg width="10" height="10"><use href="#thin_bar2"></use></svg>';
                } else if (f1tFires >= 3) {
                    if (f1tDays >= 15) {
                        symbolSVG = '<svg width="10" height="10"><use href="#thin_bar3_v"></use></svg>';
                    } else {
                        symbolSVG = '<svg width="10" height="10"><use href="#thin_bar3"></use></svg>';
                    }
                }
            }

            twoTd.classList.add("edit-two");
            twoSpan.innerHTML =
                symbolSVG +
                (twoText && twoText.length > 11
                    ? twoText.slice(0, 11) + "…"
                    : (twoText || ""));
            twoSpan.title = twoText;

            // if job title contains
            //
            // FFT2
            // Rec(fd) F2 Fire Days =>15
            // Rec(fd) F2 Fire =>3
            //
            //
            // FFT1
            // Rec(fd) F1 Fire Days =>15
            // Rec(fd) F1 Fire =>3
            //
            // bold and underline
            const f1Days = emp.rec_f1_fire_days;
            const f1Fires = emp.rec_f1_hotline_fires;
            const f2Days = emp.rec_f2_fire_days;
            const f2Fires = emp.rec_f2_hotline_fires;

            if ((f1Days >= 15 && f1Fires >= 3 && twoText.includes("FFT1")) ||
                (f2Days >= 15 && f2Fires >= 3 && twoText.includes("FFT2"))) {
                twoSpan.classList.add("job-underline");
            }

            //     // TODO добавить это и в таблицы 4 основные ниже которые
            let currenttraineeCheckbox = document.createElement("input");
            currenttraineeCheckbox.type = "checkbox";
            currenttraineeCheckbox.title = "Current trainee";
            currenttraineeCheckbox.checked = emp.current_trainee === true;
            currenttraineeCheckbox.dataset.employeeId = String(emp.id);

            currenttraineeCheckbox.addEventListener("change", function () {
                const checkbox = this;
                const employeeId = checkbox.dataset.employeeId;
                if (!employeeId) return;

                const status = checkbox.checked; // use .checked, not .value
                checkbox.disabled = true; // prevent double-submit

                fetch("/admin/employee/employee-param-change/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                    },
                    body: JSON.stringify({
                        employee_id: employeeId,
                        status: status,
                        param_name: "Current trainee"
                    })
                })
                    .then(res => {
                        if (!res.ok) throw new Error("Request failed");
                        return loadEmployeesData();
                    })
                    .catch(() => {
                        checkbox.checked = !status; // rollback on failure
                    })
                    .finally(() => {
                        checkbox.disabled = false;
                    });
            });

            twoTd.appendChild(currenttraineeCheckbox);
            twoTd.appendChild(twoSpan);

            let threeTd = document.createElement("td");
            threeTd.textContent = emp.three;

            let fourTd = document.createElement("td");
            fourTd.textContent = emp.four;

            let fiveTd = document.createElement("td");
            fiveTd.classList.add("edit-five");
            fiveTd.textContent = emp.five;

            let sixTd = document.createElement("td");
            sixTd.textContent = emp.six;

            let sevenTd = document.createElement("td");
            sevenTd.textContent = emp.seven;

            let eightTd = document.createElement("td");
            eightTd.textContent = emp.eight;

            let actionTd = document.createElement("td");

            // let removeBtn = document.createElement("div");
            // removeBtn.textContent = "✕";
            // removeBtn.classList.add("remove-btn");
            // removeBtn.addEventListener("click", function () {
            //     removeEmployeeFromCrew(emp.id);
            // });
            // actionTd.appendChild(removeBtn);

            if (twoText && twoText.includes("FFT1")) {
                fft1Count += 1;
            }
            if (emp.three) {
                sawCount += 1;
            }
            if (emp.four) {
                mspaCount += 1;
            }

            // let editBtn = document.createElement("div");
            // editBtn.textContent = "➜";
            // editBtn.classList.add("edit-btn");
            // editBtn.addEventListener("click", function () {
            //     editEmployeeById(emp.id);
            // });
            // actionTd.appendChild(editBtn);


            let bossCheckbox = document.createElement("input");
            bossCheckbox.type = "checkbox";
            bossCheckbox.title = "Set Crew Boss";
            bossCheckbox.checked = emp.is_boss === true;

            bossCheckbox.addEventListener("change", function () {
                let newBoss = bossCheckbox.checked ? emp.id : null;

                fetch("/admin/crews-management/assign-crwb/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({employee_id: newBoss, crew_id: crewId}),
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === "success") {
                            loadEmployeesData(); // перерисовать всех, чтобы сбросить лишние checkbox
                        } else {
                            console.error("Failed to assign crew boss");
                        }
                    })
                    .catch(error => console.error("Error assigning crew boss:", error));
            });

            // oneTd.prepend(bossRadio);

            crwbTd.appendChild(bossCheckbox);
            tr.appendChild(crwbTd);
            tr.appendChild(oneTd);
            tr.appendChild(twoTd);
            tr.appendChild(threeTd);
            tr.appendChild(fourTd);
            tr.appendChild(fiveTd);
            tr.appendChild(sixTd);
            tr.appendChild(sevenTd);
            tr.appendChild(eightTd);
            tr.appendChild(actionTd);

            tbody.appendChild(tr);
        });

        counter.textContent = count;
        counterForFFT1.textContent = fft1Count;
        counterForMSPA.textContent = mspaCount;
        counterForSaw.textContent = sawCount;

        if (count < 20) {
            counter.classList.add("red");
        } else {
            counter.classList.remove("red");
        }

        if (fft1Count < 3) {
            counterForFFT1.classList.add("red");
        } else {
            counterForFFT1.classList.remove("red");
        }

        if (mspaCount < 4) {
            counterForMSPA.classList.add("red");
        } else {
            counterForMSPA.classList.remove("red");
        }

        if (sawCount < 4) {
            counterForSaw.classList.add("red");
        } else {
            counterForSaw.classList.remove("red");
        }
    });
    // Применить сортировку по умолчанию после построения
    document.querySelectorAll(".crew-zone table").forEach(table => {
        let crewId = table.closest(".crew-zone").getAttribute("data-crew-id");
        let sort = localStorage.getItem(`crew_sort_${crewId}`);
        let order = localStorage.getItem(`crew_order_${crewId}`) || "asc";
        if (sort !== null) {
            sortCrewTable(table, parseInt(sort), order);
        } else {
            // даже если сортировки нет — всё равно поднимем boss наверх
            sortCrewTable(table, 0, "asc"); // сортировка по первой колонке как дефолт
        }
    });
    enableCrewZoneSorting();
    
    // Re-apply global search if active
    let globalSearchInput = document.getElementById("global-search-input");
    if (globalSearchInput && globalSearchInput.value.trim()) {
        globalEmployeeSearch();
    }
}


function applySearchFilters() {
    document.querySelectorAll(".table-search").forEach(input => {
        let query = input.value.toLowerCase();
        let tableWrapper = input.closest(".table-wrapper");

        tableWrapper.querySelectorAll("tbody tr").forEach(row => {
            let text = row.innerText.toLowerCase();
            row.style.display = text.includes(query) ? "" : "none";
        });
    });
}

// Global employee search with highlighting
function globalEmployeeSearch() {
    let searchInput = document.getElementById("global-search-input");
    if (!searchInput) return;

    let query = searchInput.value.trim();
    let resultsCount = document.getElementById("search-results-count");
    let totalMatches = 0;

    // Remove all previous highlights
    if (typeof Mark !== 'undefined') {
        // Remove from crew tables only (we don't search in employee tables)
        document.querySelectorAll(".crew-table tbody").forEach(tbody => {
            let marker = new Mark(tbody);
            marker.unmark();
        });
    }

    // Remove highlight classes from rows and make all visible (only in crew tables)
    document.querySelectorAll(".crew-table tbody tr").forEach(row => {
        row.classList.remove("search-match-highlight");
        // row.style.visibility = "visible";
        row.style.opacity = "1"; // Reset opacity when clearing search
    });

    // Get containers
    let tablesContainer = document.querySelector(".tables-container");
    let resizeGrip = document.querySelector(".resize-grip");
    let crewContainer = document.querySelector(".crew-container");

    if (query === "") {
        // Reset: show all rows and clear highlights
        if (resultsCount) resultsCount.textContent = "";
        
        // Show tables-container
        if (tablesContainer) {
            tablesContainer.style.display = "";
        }
        if (resizeGrip) {
            resizeGrip.style.display = "";
        }
        
        // Show all crew-zones, make all rows visible, and remove search-active class
        if (crewContainer) {
            document.querySelectorAll(".crew-zone").forEach(zone => {
                zone.style.display = "";
                zone.classList.remove("search-active");
                // Make all rows in this zone visible
                zone.querySelectorAll("tbody tr").forEach(row => {
                    // row.style.visibility = "visible";
                    row.style.opacity = "1"; // Reset opacity when clearing search
                });
            });
        }
        
        return;
    }

    // Hide tables-container when search is active
    if (tablesContainer) {
        tablesContainer.style.display = "none";
    }
    if (resizeGrip) {
        resizeGrip.style.display = "none";
    }

    // Add search-active class to reset transforms
    if (crewContainer) {
        document.querySelectorAll(".crew-zone").forEach(zone => {
            zone.classList.add("search-active");
        });
    }

    let queryLower = query.toLowerCase();
    let foundRows = [];

    // Search ONLY in crew tables (.crew-zone) - we don't search in .tables-container
    // Track which crew zones have matches
    let crewZonesWithMatches = new Set();
    
    document.querySelectorAll(".crew-table tbody tr").forEach(row => {
        let rowText = row.innerText.toLowerCase();
        let matches = rowText.includes(queryLower);
        
        if (matches) {
            // row.style.visibility = "visible";
            row.style.opacity = "1"; // Reset opacity for visible rows
            row.classList.add("search-match-highlight");
            foundRows.push(row);
            totalMatches++;

            // Track which crew zone this row belongs to
            let crewZone = row.closest(".crew-zone");
            if (crewZone) {
                crewZonesWithMatches.add(crewZone);
            }

            // Highlight matches in the entire row (all cells, not just name)
            if (typeof Mark !== 'undefined') {
                let marker = new Mark(row);
                marker.mark(query, {
                    element: 'mark',
                    className: 'employee-name-highlight',
                    separateWordSearch: false,
                    diacritics: false,
                    caseSensitive: false,
                    acrossElements: true // Allow highlighting across multiple cells/elements
                });
            }
        } else {
            // row.style.visibility = "hidden";
            row.style.opacity = "0.14"; // Alternative: use opacity instead of visibility
        }
    });

    // Hide crew zones that don't have any matches
    if (crewContainer) {
        document.querySelectorAll(".crew-zone").forEach(zone => {
            if (crewZonesWithMatches.has(zone)) {
                zone.style.display = "";
            } else {
                zone.style.display = "none";
            }
        });
    }

    // Update results count
    if (resultsCount) {
        if (totalMatches > 0) {
            resultsCount.textContent = `Found: ${totalMatches}`;
        } else {
            resultsCount.textContent = "No matches";
        }
    }

    // Scroll to first match if any
    if (foundRows.length > 0) {
        foundRows[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function removeEmployeeFromCrew(employeeId) {
    fetch("/admin/crews-management/remove-employee/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({employee_id: employeeId}),
    })
        .then(response => response.json())
        .then(data => {
            updateTables(data.employees, data.filter_counts);
            updateCrewZones(data.crews);
        })
        .catch(error => console.error("Error removing employee:", error));
}

function getFireRunForEmployee(employeeId, x, y) {
    const infoPopup = createInfoPopup();
    const content = infoPopup.querySelector(".popup-content");
    infoPopup.style.visibility = "hidden";
    infoPopup.style.display = "block";

    fetch("/admin/crews-management/firerun-employee/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        },
        body: JSON.stringify({employee_id: employeeId})
    })
        .then(res => res.json())
        .then(res => {
            if (res.status !== "ok") return;

            const fire_runs = res.data.fire_runs;
            const students = res.data.students;
            const info = res.data.info;
            let html = "";

            html += `<table class="info-table" style="margin-bottom: 15px;"><thead><tr>`;
            // info.forEach(([key]) => {
            //     html += `<th>${key}</th>`;
            // });
            html += `</tr></thead><tbody><tr>`;
            info.forEach(([_, date]) => {
                html += `<td>${date}</td>`;
            });
            html += `</tr></tbody></table>`;

            if (fire_runs.length === 0 && students.length === 0) {
                html = `<div style="padding: 5px 10px; font-style: italic;">No data available</div>`;
            } else {
                if (students.length > 0) {
                    html += `<table class="student-table" style="margin-bottom: 15px;"><thead><tr>`;
                    students.forEach(([course]) => {
                        html += `<th>${course.replace(":", "")}</th>`;
                    });
                    html += `</tr></thead><tbody><tr>`;
                    students.forEach(([_, date]) => {
                        html += `<td>${date}</td>`;
                    });
                    html += `</tr></tbody></table>`;
                }
                // if (students.length > 0) {
                //     html += `<table class="student-table" style="margin-bottom: 15px;"><thead><tr>`;
                //     html += `<!--<th>Course</th><th>Date</th>-->`;
                //     html += `</tr></thead><tbody>`;
                //     students.forEach(([course, date]) => {
                //         html += `<tr><td>${course}</td><td>${date}</td></tr>`;
                //     });
                //     html += `</tbody></table>`;
                // }

                if (fire_runs.length > 0) {
                    const headers = [
                        "Job title", "Incident date", "State", "Operational periods",
                        "Incident name", "Crew boss", "Eval hotline", "Hotline in remarks", "Ranking"
                    ];

                    const keys = [
                        "job_title", "start_date", "crew_fire_state", "operational_periods",
                        "crew_fire_incident_name", "crew_crew_name", "eval_hotline",
                        "hotline_in_remarks", "ranking"
                    ];

                    html += `<table class="fire-run-table"><thead><tr>`;
                    headers.forEach(text => html += `<th>${text}</th>`);
                    html += `</tr></thead><tbody>`;

                    fire_runs.forEach(row => {
                        html += "<tr>";
                        keys.forEach(key => {
                            html += `<td>${row[key] ?? ""}</td>`;
                        });
                        html += "</tr>";
                    });

                    html += "</tbody></table>";
                }
            }

            content.innerHTML = html;


            // const popupRect = infoPopup.getBoundingClientRect();
            // let left = x + 10 - popupRect.width; // чтобы правый край был на 10px правее курсора
            // // Подстраховка от выхода за края
            // if (left < 10) left = 10;

            let left = x - 25

            infoPopup.style.left = `${left}px`;
            infoPopup.style.top = `${y - 10}px`;
            infoPopup.style.visibility = "visible";
        });
}

function createInfoPopup() {
    document.querySelector("#fire-run-popup")?.remove();  // Удалить, если уже был

    const div = document.createElement("div");
    div.id = "fire-run-popup";
    div.style.position = "absolute"; // CHANGED: needed for left/top
    div.style.zIndex = "9999";       // CHANGED: keep on top

    // Close button
    const closeBtn = document.createElement("span");
    closeBtn.classList.add("close-cross");
    closeBtn.innerHTML = "&times;";
    closeBtn.addEventListener("click", () => div.remove());
    div.appendChild(closeBtn);

    // CHANGED: dedicated content container to avoid nuking the close button
    const content = document.createElement("div");
    content.className = "popup-content";
    content.style.padding = "10px 12px 12px 12px";
    div.appendChild(content);

    let hideTimeout = null;
    div.addEventListener("mouseleave", function () {
        div.style.opacity = "0.9";
        hideTimeout = setTimeout(() => {
            div.remove();
        }, 500);
    });
    div.addEventListener("mouseenter", function () {
        div.style.opacity = "1";
        clearTimeout(hideTimeout);
    });

    document.body.appendChild(div);
    return div;
}


function editEmployeeById(employeeId) {
    const url = `/admin/company/employees/${employeeId}/change/`;
    window.open(url, "_blank");
}

function updateSortIndicators(table, columnIndex, order) {
    table.querySelectorAll("th").forEach((th, i) => {
        th.classList.remove("sort-asc", "sort-desc");
        if (i === columnIndex) {
            th.classList.add(order === "asc" ? "sort-asc" : "sort-desc");
        }
    });
}

function updateSortIndicator(th, table) {
    let columnIndex = Array.from(th.parentNode.children).indexOf(th);
    let currentSort = table.getAttribute("data-sort");
    let currentOrder = table.getAttribute("data-order");

    th.classList.remove("sort-asc", "sort-desc");

    if (currentSort == columnIndex) {
        th.classList.add(currentOrder === "asc" ? "sort-asc" : "sort-desc");
    }
}

function sortHandler(event) {
    let th = event.target;
    let table = th.closest("table");
    let columnIndex = Array.from(th.parentNode.children).indexOf(th);
    let currentSort = table.getAttribute("data-sort");
    let currentOrder = table.getAttribute("data-order");
    let tableId = table.closest(".table-wrapper").getAttribute("data-filter-id");

    if (currentSort === columnIndex.toString()) {
        currentOrder = currentOrder === "asc" ? "desc" : "asc";
    } else {
        currentOrder = "asc";
    }

    table.setAttribute("data-sort", columnIndex);
    table.setAttribute("data-order", currentOrder);
    localStorage.setItem("sort_" + tableId, columnIndex);
    localStorage.setItem("order_" + tableId, currentOrder);

    sortTable(table, columnIndex, currentOrder);
    updateSortIndicators(table, columnIndex, currentOrder);
}

function enableSorting() {
    document.querySelectorAll(".table-wrapper table thead th").forEach(th => {
        th.removeEventListener("click", sortHandler);
        th.addEventListener("click", sortHandler);

        let table = th.closest("table");
        let columnIndex = Array.from(th.parentNode.children).indexOf(th);
        let tableId = table.closest(".table-wrapper").getAttribute("data-filter-id");

        let savedSort = localStorage.getItem("sort_" + tableId);
        let savedOrder = localStorage.getItem("order_" + tableId);

        if (savedSort !== null && savedOrder !== null && savedSort == columnIndex) {
            table.setAttribute("data-sort", savedSort);
            table.setAttribute("data-order", savedOrder);
            sortTable(table, parseInt(savedSort), savedOrder);
            updateSortIndicators(table, parseInt(savedSort), savedOrder);
        }
    });
}

function sortTable(table, columnIndex, order) {
    let tbody = table.querySelector("tbody");
    let rows = Array.from(tbody.querySelectorAll("tr"));

    rows.sort((rowA, rowB) => {
        let cellA = rowA.cells[columnIndex].textContent.trim();
        let cellB = rowB.cells[columnIndex].textContent.trim();

        if (!isNaN(cellA) && !isNaN(cellB)) {
            return order === "asc" ? Number(cellA) - Number(cellB) : Number(cellB) - Number(cellA);
        }
        return order === "asc" ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
    });

    tbody.innerHTML = "";
    rows.forEach(row => tbody.appendChild(row));
}

grp.jQuery(document).ready(function () {

    loadEmployeesData();

    document.querySelectorAll(".employee-filter").forEach(select => {
        select.addEventListener("change", loadEmployeesData);
    });


    let lastTop = 0;
    document.addEventListener("dragover", function (event) {
        let scrollSpeed = 40;

        if (event.clientY < 100) {
            window.scrollBy(0, -scrollSpeed);
        } else if (event.clientY > window.innerHeight - 100) {
            window.scrollBy(0, scrollSpeed);
        }

        let crewContainer = document.querySelector(".crew-container");
        let newTop = window.scrollY < crewContainer.offsetHeight ? 0 : window.scrollY;

        if (newTop !== lastTop) {
            lastTop = newTop;
            crewContainer.style.top = `${newTop}px`;
        }
    });


    document.querySelectorAll(".crew-zone").forEach(zone => {
        zone.addEventListener("dragover", function (event) {
            event.preventDefault();
        });

        zone.addEventListener("drop", function (event) {
            event.preventDefault();
            let employeeId = event.dataTransfer.getData("text/plain");
            let crewId = this.getAttribute("data-crew-id");

            fetch("/admin/crews-management/assign-employee/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({employee_id: employeeId, crew_id: crewId}),
            })
                .then(response => response.json())
                .then(data => {
                    updateTables(data.employees, data.filter_counts);
                    updateCrewZones(data.crews);
                })
                .catch(error => console.error("Error updating crew assignment:", error));
        });
    });

    document.querySelectorAll(".table-search").forEach(input => {
        input.addEventListener("input", applySearchFilters);
    });

    // Global employee search
    let globalSearchInput = document.getElementById("global-search-input");
    if (globalSearchInput) {
        globalSearchInput.addEventListener("input", globalEmployeeSearch);
        // Also trigger on Enter key
        globalSearchInput.addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                globalEmployeeSearch();
            }
        });
    }


    document.addEventListener("dragstart", function () {
        let crewContainer = document.querySelector(".crew-container");
        let scrollY = window.scrollY;

        if (scrollY < crewContainer.offsetHeight) return;

        // Сбрасываем transition
        crewContainer.style.transition = "none";
        crewContainer.style.top = `${crewContainer.offsetTop}px`;

        // Делаем небольшую задержку перед включением transition
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                crewContainer.style.transition = "top 0.3s ease-out";
                crewContainer.style.top = `${scrollY}px`;
            });
        });
    });

    document.addEventListener("dragend", function () {
        let crewContainer = document.querySelector(".crew-container");
        crewContainer.style.top = "0px"; // Скрываем обратно
    });

    document.querySelectorAll(".employee-filter").forEach(select => {
        select.addEventListener("change", function () {
            let filters = [];
            document.querySelectorAll(".employee-filter").forEach(sel => {
                filters.push(sel.value);
            });
            console.log(filters.join(",")); // Выводит строку "1,3,2,4"

            console.log(JSON.stringify(filters))

            fetch("/admin/saved-filters-order/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(filters)
            }).then(response => {
                if (response.ok) {
                    window.location.reload();
                }
            });
        });
    });

    // для глобавльной ордеринг колонок во всех таблицах с коммандами.
    let globalSortState = {
        column: null,
        order: "asc"
    };

    document.querySelectorAll("#global-sort-bar span").forEach(span => {
        span.addEventListener("click", () => {
            let column = parseInt(span.getAttribute("data-column"));

            if (globalSortState.column === column) {
                globalSortState.order = globalSortState.order === "asc" ? "desc" : "asc";
            } else {
                globalSortState.column = column;
                globalSortState.order = "asc";
            }

            // UI update
            document.querySelectorAll("#global-sort-bar span").forEach(s => s.classList.remove("active"));
            span.classList.add("active");

            // Применить сортировку ко всем crew зон
            document.querySelectorAll(".crew-zone table").forEach(table => {
                let crewId = table.closest(".crew-zone").getAttribute("data-crew-id");
                sortCrewTable(table, column, globalSortState.order);
                localStorage.setItem(`crew_sort_${crewId}`, column);
                localStorage.setItem(`crew_order_${crewId}`, globalSortState.order);

                // Обновить визуальные стрелки
                table.querySelectorAll("th").forEach((th, idx) => {
                    th.classList.remove("sort-asc", "sort-desc");
                    if (idx === column) {
                        th.classList.add(globalSortState.order === "asc" ? "sort-asc" : "sort-desc");
                    }
                });
            });
        });
    });

});
