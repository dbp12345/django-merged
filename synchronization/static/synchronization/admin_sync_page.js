document.addEventListener('DOMContentLoaded', () => {
    /*For admin django*/
    // const form = document.querySelector("#sync_form");
    // if (form) {
    //     const table = form.querySelector("table");
    //     if (table) {
    //         table.addEventListener("change", (event) => {
    //             if (event.target.type === "checkbox") {
    //                 const tr = event.target.closest("tr");
    //                 const checkboxes = tr.querySelectorAll('input[type="checkbox"]');
    //                 for (const checkbox of checkboxes) {
    //                     if (checkbox !== event.target) {
    //                         checkbox.checked = false;
    //                     }
    //                 }
    //             }
    //         });
    //     }
    // }


    /*For grappelli*/
    const form_grp = document.querySelector("#sync_parameters-group");
    if (form_grp) {
        form_grp.addEventListener("change", (event) => {
            if (event.target.type === "checkbox") {
                const grp_tr = event.target.closest(".grp-tr");
                if (!grp_tr) return;
                const checkboxes = grp_tr.querySelectorAll('input[type="checkbox"]');
                for (const checkbox of checkboxes) {
                    if (checkbox !== event.target) {
                        checkbox.checked = false;
                    }
                }
            }
        });
    }

});
