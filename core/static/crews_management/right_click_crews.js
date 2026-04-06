grp.jQuery(document).ready(function () {

    const wrapper = document.getElementById("custom-context-wrapper");
    const menu = wrapper.querySelector("#custom-context-menu");
    const paramSelect = wrapper.querySelector("#context-param-select");
    let currentTarget = null;

    document.addEventListener("contextmenu", function (e) {
        const target = e.target.closest(".target");
        if (target) {
            e.preventDefault();
            currentTarget = target;

            // Убрать подсветку со всех предыдущих
            document.querySelectorAll(".target.highlighted").forEach(el => el.classList.remove("highlighted"));

            // Подсветить текущий
            target.classList.add("highlighted");

            // 🟡 РЕСЕТ селекта
            paramSelect.selectedIndex = 0;

            // Просто показываем уже готовое меню
            wrapper.style.top = `${e.pageY}px`;
            wrapper.style.left = `${e.pageX}px`;
            wrapper.style.display = "block";
        } else {
            wrapper.style.display = "none";
        }
    });

    document.addEventListener("click", function (e) {
        if (wrapper.contains(e.target)) return;  // Клик внутри враппера — не закрывать

        document.querySelectorAll(".target.highlighted").forEach(el => el.classList.remove("highlighted"));
        wrapper.style.display = "none";
    });

    menu.addEventListener("click", function (e) {
        if (e.target.tagName === "LI") {
            const elem = e.target;
            const crewId = elem.dataset.crewId;
            const employeeId = currentTarget.dataset.employeeId;

            // Подсветить текущий
            currentTarget.classList.add("highlighted-process");

            if (!crewId) {
                // 🟥 Удалить из crew
                wrapper.style.display = "none";
                fetch("/admin/crews-management/remove-employee/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({employee_id: employeeId})
                }).then(res => {
                    if (res.ok) loadEmployeesData();
                });
            } else {
                // 🟩 Добавить в выбранную crew
                wrapper.style.display = "none";
                fetch("/admin/crews-management/assign-employee/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        employee_id: employeeId,
                        crew_id: crewId
                    })
                }).then(res => {
                    if (res.ok) loadEmployeesData();
                });
            }
        }
    });

    // 🔄 обработчик для select нового параметра
    paramSelect.addEventListener("change", function () {
        const value = this.value;
        const employeeId = currentTarget.dataset.employeeId;

        if (!value || !employeeId) return;

        wrapper.style.display = "none";
        fetch("/admin/employee/employee-param-change/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                employee_id: employeeId,
                status: value,
                param_name: "Dispatch Call Status",
            })
        }).then(res => {
            if (res.ok) loadEmployeesData();
        });
    });

    // скрытие по уходу курсора
    let hideTimeout = null;
    wrapper.addEventListener("mouseleave", function () {
        hideTimeout = setTimeout(() => {
            wrapper.style.display = "none";
            // Убрать подсветку со всех предыдущих
            document.querySelectorAll(".target.highlighted").forEach(el => el.classList.remove("highlighted"));
        }, 1000); // N мс задержки
    });
    wrapper.addEventListener("mouseenter", function () {
        clearTimeout(hideTimeout);
    });
});
