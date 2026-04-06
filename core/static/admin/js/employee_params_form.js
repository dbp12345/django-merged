let clickedButton = null;

grp.jQuery(document).ready(function () {
    // Сохраняем оригинальные значения (включая checkbox)
    document.querySelectorAll(".param-container").forEach(div => {
        div.querySelectorAll("input, select, textarea").forEach(input => {
            if (input.name) {
                if (input.type === "checkbox") {
                    input.dataset.original = input.checked.toString();  // "true"/"false"
                } else {
                    input.dataset.original = input.value;
                }
            }
        });
    });

    // Отлавливаем нажатую кнопку submit
    grp.jQuery("#employees_form input[type=submit]").on("click", function () {
        clickedButton = this;
    });

    grp.jQuery("#employees_form").on("submit", async function (e) {
        const form = this;

        const paramContainers = document.querySelectorAll(".param-container");
        if (paramContainers.length === 0) return;

        e.preventDefault();

        const inputs = [];
        paramContainers.forEach(div => {
            div.querySelectorAll("input, select, textarea").forEach(input => {
                if (input.type !== "file" && !input.name.startsWith("delete_")) {
                    inputs.push(input);
                }
            });
        });

        const payload = {
            employee_id: document.getElementById("employee-id")?.value,
        };

        inputs.forEach(input => {
            if (!input.name) return;

            if (input.type === "checkbox") {
                const original = input.dataset.original === "true";
                if (input.checked !== original) {
                    payload[input.name] = input.checked ? "True" : "False";
                }
            } else {
                if (input.value !== input.dataset.original) {
                    payload[input.name] = input.value;
                }
            }
        });

        // ничего не изменено — отправляем форму как есть
        if (Object.keys(payload).length === 1) {
            if (clickedButton && clickedButton.name) {
                const tempBtn = document.createElement("input");
                tempBtn.type = "hidden";
                tempBtn.name = clickedButton.name;
                tempBtn.value = clickedButton.value;
                form.appendChild(tempBtn);
            }
            form.submit();
            return;
        }

        try {
            const response = await fetch("/admin/employees/update-parameters/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": form.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("Failed to save paramForm");

            // если была нажата конкретная кнопка — создаём клон и отправляем с ней
            if (clickedButton && clickedButton.name) {
                const tempBtn = document.createElement("input");
                tempBtn.type = "hidden";
                tempBtn.name = clickedButton.name;
                tempBtn.value = clickedButton.value;
                form.appendChild(tempBtn);
            }

            form.submit();
        } catch (error) {
            console.error("Failed to save employee-parameters-form:", error);
            alert("Failed to save Properties.");
        }
    });
});
