// Modal management for Availability, Dispatching statuses, and Interactions
// Uses existing form fields, just hides them and shows in modal
document.addEventListener("DOMContentLoaded", function () {
    const modalBlocks = ["availability", "dispatching_statuses", "interactions"];

    // Generate modals dynamically from existing fields
    function generateModals() {
        modalBlocks.forEach(blockType => {
            // Map block types to their display names in DOM
            const blockNameMap = {
                "availability": "Availability",
                "dispatching_statuses": "Dispatching statuses",
                "interactions": "Interactions"
            };
            const blockName = blockNameMap[blockType] || blockType;
            // Use data attribute to avoid issues with special characters in group names
            const container = document.querySelector(`[data-group-name="${blockName}"] .hidden-fields-container`);
            if (!container) return;

            const fields = Array.from(container.querySelectorAll("input, select, textarea"));
            if (fields.length === 0) return;

            // Create modal if it doesn't exist
            let modal = document.getElementById(`modal-${blockType}`);
            if (!modal) {
                modal = createModal(blockType, fields);
                document.body.appendChild(modal);
            }
        });
    }

    // Create modal structure
    function createModal(blockType, fields) {
        const modal = document.createElement("div");
        modal.id = `modal-${blockType}`;
        modal.className = "modal";

        const modalContent = document.createElement("div");
        modalContent.className = "modal-content";
        modalContent.style.minWidth = "600px";
        modalContent.style.paddingTop = "50px";
        
        const title = document.createElement("h2");
        title.className = "h2-modal";
        title.textContent = `${blockType.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}`;

        const closeBtn = document.createElement("span");
        closeBtn.className = "close-modal";
        closeBtn.setAttribute("data-modal", `modal-${blockType}`);
        closeBtn.innerHTML = "&times;";

        const form = document.createElement("form");
        form.id = `form-${blockType}`;
        form.setAttribute("data-block-type", blockType);

        const modalBody = document.createElement("div");
        modalBody.className = "modal-body";

        // Create form fields in modal based on existing fields
        fields.forEach(originalField => {
            if (!originalField.name) return;

            const fieldWrapper = document.createElement("div");
            fieldWrapper.style.marginBottom = "15px";

            const label = document.createElement("label");
            label.style.display = "block";
            label.style.fontWeight = "bold";
            label.style.marginBottom = "5px";

            // Get field label from original field's parent label
            const originalLabel = originalField.closest("div").querySelector("label");
            label.textContent = originalLabel ? originalLabel.textContent.trim() : originalField.name;

            let modalField;

            if (originalField.type === "checkbox") {
                fieldWrapper.appendChild(label);
                const checkboxWrapper = document.createElement("label");
                checkboxWrapper.style.display = "flex";
                checkboxWrapper.style.alignItems = "center";
                
                modalField = document.createElement("input");
                modalField.type = "checkbox";
                modalField.name = `modal_${originalField.name}`;
                modalField.id = `modal-${originalField.id || originalField.name}`;
                modalField.setAttribute("data-original-field", originalField.name);
                if (originalField.checked) modalField.checked = true;
                
                checkboxWrapper.appendChild(modalField);
                const checkboxLabel = document.createElement("span");
                checkboxLabel.textContent = label.textContent;
                checkboxLabel.style.marginLeft = "5px";
                checkboxWrapper.appendChild(checkboxLabel);
                fieldWrapper.appendChild(checkboxWrapper);
            } else if (originalField.tagName === "SELECT") {
                fieldWrapper.appendChild(label);
                modalField = document.createElement("select");
                modalField.name = `modal_${originalField.name}`;
                modalField.id = `modal-${originalField.id || originalField.name}`;
                modalField.setAttribute("data-original-field", originalField.name);
                modalField.style.padding = "5px";

                // Copy options
                Array.from(originalField.options).forEach(option => {
                    const newOption = document.createElement("option");
                    newOption.value = option.value;
                    newOption.textContent = option.textContent;
                    if (option.selected) newOption.selected = true;
                    modalField.appendChild(newOption);
                });
                fieldWrapper.appendChild(modalField);
            } else if (originalField.tagName === "TEXTAREA") {
                fieldWrapper.appendChild(label);
                modalField = document.createElement("textarea");
                modalField.name = `modal_${originalField.name}`;
                modalField.id = `modal-${originalField.id || originalField.name}`;
                modalField.setAttribute("data-original-field", originalField.name);
                modalField.value = originalField.value || "";
                modalField.rows = 4;
                modalField.style.padding = "5px";
                fieldWrapper.appendChild(modalField);
            } else {
                fieldWrapper.appendChild(label);
                
                // Check if field name contains "notes" - use textarea instead of input
                const fieldName = originalField.name.toLowerCase();
                const labelText = label.textContent.toLowerCase();
                const isNotesField = fieldName.includes("notes") || labelText.includes("notes");
                
                if (isNotesField) {
                    modalField = document.createElement("textarea");
                    modalField.name = `modal_${originalField.name}`;
                    modalField.id = `modal-${originalField.id || originalField.name}`;
                    modalField.setAttribute("data-original-field", originalField.name);
                    modalField.value = originalField.value || "";
                    modalField.rows = 4;
                    modalField.style.padding = "5px";
                } else {
                    modalField = document.createElement("input");
                    modalField.type = originalField.type || "text";
                    modalField.name = `modal_${originalField.name}`;
                    modalField.id = `modal-${originalField.id || originalField.name}`;
                    modalField.setAttribute("data-original-field", originalField.name);
                    modalField.value = originalField.value || "";
                    modalField.style.padding = "5px";

                    // Copy classes for date/datetime widgets
                    if (originalField.classList.contains("vDateField")) {
                        modalField.classList.add("vDateField");
                    }
                    if (originalField.classList.contains("vDateTimeField")) {
                        modalField.classList.add("vDateTimeField");
                    }
                    if (originalField.step) {
                        modalField.step = originalField.step;
                    }
                }

                fieldWrapper.appendChild(modalField);
            }

            modalBody.appendChild(fieldWrapper);
        });

        const buttonWrapper = document.createElement("div");
        buttonWrapper.style.marginTop = "20px";
        buttonWrapper.style.textAlign = "right";

        const cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.className = "cancel-btn modal-content-button";
        cancelBtn.setAttribute("data-modal", `modal-${blockType}`);
        cancelBtn.textContent = "Cancel";
        
        const saveBtn = document.createElement("button");
        saveBtn.className = "modal-content-button";
        saveBtn.type = "submit";
        saveBtn.textContent = "Save";

        buttonWrapper.appendChild(cancelBtn);
        buttonWrapper.appendChild(saveBtn);

        form.appendChild(modalBody);
        form.appendChild(buttonWrapper);

        modalContent.appendChild(closeBtn);
        modalContent.appendChild(title);
        modalContent.appendChild(form);
        modal.appendChild(modalContent);

        return modal;
    }

    // Open modal function
    function openModal(blockType) {
        const modal = document.getElementById(`modal-${blockType}`);
        if (!modal) {
            generateModals();
            const newModal = document.getElementById(`modal-${blockType}`);
            if (newModal) {
                setupModalEvents(newModal, blockType);
                newModal.classList.add("open");
                initializeDateWidgets(newModal);
            }
            return;
        }

        // Reset modal fields from original fields
        const blockNameMap = {
            "availability": "Availability",
            "dispatching_statuses": "Dispatching statuses",
            "interactions": "Interactions"
        };
        const blockName = blockNameMap[blockType] || blockType;
        // Use data attribute to avoid issues with special characters in group names
        const container = document.querySelector(`[data-group-name="${blockName}"] .hidden-fields-container`);
        if (container) {
            const originalFields = Array.from(container.querySelectorAll("input, select, textarea"));
            originalFields.forEach(originalField => {
                if (!originalField.name) return;
                const modalField = modal.querySelector(`[data-original-field="${originalField.name}"]`);
                if (modalField) {
                    if (originalField.type === "checkbox") {
                        modalField.checked = originalField.checked;
                    } else if (originalField.tagName === "SELECT") {
                        modalField.value = originalField.value;
                    } else {
                        modalField.value = originalField.value || "";
                    }
                }
            });
        }

        modal.classList.add("open");
        initializeDateWidgets(modal);
    }

    // Close modal function
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove("open");
        }
    }

    // Copy values from modal to hidden form fields
    function copyModalToForm(blockType) {
        const modal = document.getElementById(`modal-${blockType}`);
        if (!modal) return;

        const blockNameMap = {
            "availability": "Availability",
            "dispatching_statuses": "Dispatching statuses",
            "interactions": "Interactions"
        };
        const blockName = blockNameMap[blockType] || blockType;
        // Use data attribute to avoid issues with special characters in group names
        const container = document.querySelector(`[data-group-name="${blockName}"] .hidden-fields-container`);
        if (!container) return;

        const modalFields = modal.querySelectorAll("[data-original-field]");
        modalFields.forEach(modalField => {
            const originalFieldName = modalField.getAttribute("data-original-field");
            const originalField = container.querySelector(`[name="${originalFieldName}"]`);
            if (originalField) {
                if (modalField.type === "checkbox") {
                    originalField.checked = modalField.checked;
                } else if (originalField.tagName === "SELECT") {
                    originalField.value = modalField.value;
                } else {
                    originalField.value = modalField.value || "";
                }
            }
        });
    }

    // Initialize date/datetime widgets
    function initializeDateWidgets(modal) {
        // Try multiple ways to access jQuery
        const jQuery = (typeof grp !== "undefined" && grp.jQuery) || 
                       (typeof window.jQuery !== "undefined" && window.jQuery) ||
                       (typeof $ !== "undefined" && $);
        
        if (!jQuery) {
            console.warn("jQuery not available for datepicker initialization");
            return;
        }

        setTimeout(function() {
            const dateFields = modal.querySelectorAll(".vDateField");
            dateFields.forEach(function(field) {
                if (!jQuery(field).hasClass("hasDatepicker")) {
                    jQuery(field).datepicker({
                        dateFormat: "mm/dd/yy"
                    });
                }
            });

            const datetimeFields = modal.querySelectorAll(".vDateTimeField");
            datetimeFields.forEach(function(field) {
                if (!jQuery(field).hasClass("hasDatepicker")) {
                    jQuery(field).datetimepicker({
                        dateFormat: "mm/dd/yy",
                        timeFormat: "HH:mm"
                    });
                }
            });
        }, 200);
    }

    // Setup modal events
    function setupModalEvents(modal, blockType) {
        const form = modal.querySelector("form");
        if (form) {
            form.addEventListener("submit", async function(e) {
                e.preventDefault();
                copyModalToForm(blockType);
                closeModal(`modal-${blockType}`);
                
                // Save parameters via AJAX and reload page
                await saveParametersAndReload();
            });
        }

        const closeBtn = modal.querySelector(".close-modal");
        if (closeBtn) {
            closeBtn.addEventListener("click", function() {
                closeModal(`modal-${blockType}`);
            });
        }

        const cancelBtn = modal.querySelector(".cancel-btn");
        if (cancelBtn) {
            cancelBtn.addEventListener("click", function() {
                closeModal(`modal-${blockType}`);
            });
        }

        // Close on outside click
        modal.addEventListener("click", function(e) {
            if (e.target === modal) {
                closeModal(`modal-${blockType}`);
            }
        });
    }

    // Setup add buttons
    document.querySelectorAll(".add-record-btn").forEach(btn => {
        btn.addEventListener("click", function() {
            const blockType = this.getAttribute("data-block-type");
            openModal(blockType);
        });
    });

    // Setup edit buttons on table rows
    // function setupEditButtons() {
    //     document.querySelectorAll(".table-history tbody tr").forEach(row => {
    //         if (row.getAttribute("data-record-id")) {
    //             row.style.cursor = "pointer";
    //             row.addEventListener("click", function() {
    //                 const container = this.closest(".block-history-container");
    //                 if (container) {
    //                     const blockTypeAttr = container.getAttribute("data-block-type");
    //                     if (blockTypeAttr && modalBlocks.includes(blockTypeAttr)) {
    //                         // For editing, we would need to fetch the record and populate fields
    //                         // For now, just open modal for new entry
    //                         // TODO: Implement edit functionality if needed
    //                         openModal(blockTypeAttr);
    //                     }
    //                 }
    //             });
    //         }
    //     });
    // }

    // Generate modals on load
    generateModals();

    // Setup events for generated modals
    modalBlocks.forEach(blockType => {
        const modal = document.getElementById(`modal-${blockType}`);
        if (modal) {
            setupModalEvents(modal, blockType);
        }
    });

    // Setup edit buttons
    setupEditButtons();

    // Re-setup edit buttons after table refresh
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === "childList") {
                setupEditButtons();
            }
        });
    });

    document.querySelectorAll(".block-history-container").forEach(container => {
        observer.observe(container, { childList: true, subtree: true });
    });

    // Save parameters via AJAX and reload page
    async function saveParametersAndReload() {
        const mainForm = document.getElementById("employees_form");
        if (!mainForm) {
            window.location.reload();
            return;
        }

        const paramContainers = document.querySelectorAll(".param-container");
        if (paramContainers.length === 0) {
            window.location.reload();
            return;
        }

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

        // If nothing changed, just reload
        if (Object.keys(payload).length === 1) {
            window.location.reload();
            return;
        }

        try {
            // Get CSRF token from form or cookie
            const csrfToken = mainForm.querySelector("[name=csrfmiddlewaretoken]")?.value || getCookie("csrftoken");
            
            const response = await fetch("/admin/employees/update-parameters/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error("Failed to save parameters");
            }

            // Reload page to show updated data
            window.location.reload();
        } catch (error) {
            console.error("Failed to save parameters:", error);
            alert("Failed to save parameters. Please try again.");
        }
    }

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
