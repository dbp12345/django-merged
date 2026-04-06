document.addEventListener("DOMContentLoaded", function () {
    const empId = document.getElementById("employee-id")?.value;
    const empEmail = document.getElementById("employee-email")?.value;
    // Временно отключу, пока не до этой задачи
    // const fireRunGroup = document.querySelector("#fire_run_entries-group");
    // if (fireRunGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a href="/admin/exhibit/get/docx?id='+empId+'" class="fire_run_button_run">Exhibit-N.docx</a>';
    //     customDiv.style.margin = "0 10px";
    //     // fireRunGroup.parentNode.insertBefore(customDiv, fireRunGroup.nextSibling);
    //     fireRunGroup.appendChild(customDiv);  // 👈 вставляем внутрь, в самый конец
    // }

    const fireRunGroup = document.querySelector("#fire_run_entries-group");
    if (fireRunGroup) {
        const customDiv = document.createElement("div");
        customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/firerun/?employee__id__exact='+empId+'">See all FireRun</a>';
        customDiv.style.margin = "0 10px";
        fireRunGroup.appendChild(customDiv);
    }

    const studentGroup = document.querySelector("#student_entries-group");
    if (studentGroup) {
        const customDiv = document.createElement("div");
        customDiv.innerHTML = '<a href="/admin/students/get/pdf?id='+empId+'" class="students_button_run">' +
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="36" height="36" viewBox="0 0 256 256" xml:space="preserve">\n' +
            '<g style="stroke: none; stroke-width: 0; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: none; fill-rule: nonzero; opacity: 1;" transform="translate(1.4065934065934016 1.4065934065934016) scale(2.81 2.81)">\n' +
            '\t<path d="M 10.952 43.558 c 0 1.097 0.923 1.987 2.061 1.987 h 39.572 c 1.138 0 2.061 -0.89 2.061 -1.987 V 24.683 c 0 -1.097 -0.923 -1.987 -2.061 -1.987 H 13.013 c -1.138 0 -2.061 0.89 -2.061 1.987 V 43.558 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(234,84,64); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 21.723 36.268 h -4.412 c -0.549 0 -0.994 -0.445 -0.994 -0.994 V 27.96 c 0 -0.549 0.445 -0.994 0.994 -0.994 h 4.412 c 1.71 0 3.101 1.391 3.101 3.101 v 3.1 C 24.824 34.877 23.432 36.268 21.723 36.268 z M 18.305 34.279 h 3.418 c 0.613 0 1.112 -0.499 1.112 -1.112 v -3.1 c 0 -0.613 -0.499 -1.112 -1.112 -1.112 h -3.418 V 34.279 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(255,255,255); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 17.311 41.276 c -0.549 0 -0.994 -0.445 -0.994 -0.994 v -5.008 c 0 -0.549 0.445 -0.994 0.994 -0.994 s 0.994 0.445 0.994 0.994 v 5.008 C 18.305 40.831 17.86 41.276 17.311 41.276 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(255,255,255); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 33.861 41.276 h -4.195 c -0.549 0 -0.994 -0.445 -0.994 -0.994 V 27.96 c 0 -0.549 0.445 -0.994 0.994 -0.994 h 4.195 c 1.829 0 3.318 1.488 3.318 3.318 v 7.675 C 37.179 39.788 35.691 41.276 33.861 41.276 z M 30.66 39.287 h 3.201 c 0.733 0 1.329 -0.596 1.329 -1.329 v -7.675 c 0 -0.733 -0.596 -1.329 -1.329 -1.329 H 30.66 V 39.287 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(255,255,255); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 42.246 41.276 c -0.549 0 -0.994 -0.445 -0.994 -0.994 V 27.96 c 0 -0.549 0.445 -0.994 0.994 -0.994 s 0.994 0.445 0.994 0.994 v 12.321 C 43.241 40.831 42.796 41.276 42.246 41.276 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(255,255,255); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 48.764 28.955 h -6.518 c -0.549 0 -0.994 -0.445 -0.994 -0.994 c 0 -0.549 0.445 -0.994 0.994 -0.994 h 6.518 c 0.55 0 0.994 0.445 0.994 0.994 C 49.759 28.51 49.314 28.955 48.764 28.955 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(255,255,255); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 46.515 35.115 h -4.269 c -0.549 0 -0.994 -0.445 -0.994 -0.994 s 0.445 -0.994 0.994 -0.994 h 4.269 c 0.55 0 0.994 0.445 0.994 0.994 S 47.065 35.115 46.515 35.115 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(255,255,255); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 59.376 76.292 h -4.574 V 59.988 c 0 -0.745 -0.582 -1.349 -1.3 -1.349 H 41.15 c -0.718 0 -1.3 0.604 -1.3 1.349 v 16.304 h -4.574 c -0.869 0 -1.304 1.051 -0.69 1.665 l 11.551 11.551 c 0.657 0.657 1.721 0.657 2.378 0 l 11.551 -11.551 C 60.68 77.342 60.245 76.292 59.376 76.292 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(234,84,64); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 77.295 19.578 H 63.561 c -2.255 0 -4.09 -1.835 -4.09 -4.091 V 1.755 c 0 -0.824 0.668 -1.492 1.492 -1.492 c 0.824 0 1.492 0.668 1.492 1.492 v 13.732 c 0 0.61 0.496 1.107 1.106 1.107 h 13.734 c 0.824 0 1.492 0.668 1.492 1.492 C 78.787 18.91 78.119 19.578 77.295 19.578 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(124,124,124); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 31.769 84.395 H 19.947 c -2.395 0 -4.344 -1.949 -4.344 -4.344 V 50.575 c 0 -0.824 0.668 -1.492 1.492 -1.492 c 0.824 0 1.492 0.668 1.492 1.492 v 29.477 c 0 0.751 0.61 1.361 1.361 1.361 h 11.822 c 0.824 0 1.492 0.668 1.492 1.492 C 33.261 83.727 32.593 84.395 31.769 84.395 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(124,124,124); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '\t<path d="M 74.705 84.395 H 62.568 c -0.824 0 -1.492 -0.668 -1.492 -1.492 c 0 -0.824 0.668 -1.492 1.492 -1.492 h 12.138 c 0.75 0 1.36 -0.61 1.36 -1.361 V 19.267 c 0 -0.364 -0.142 -0.706 -0.398 -0.962 L 60.744 3.382 c -0.257 -0.256 -0.599 -0.398 -0.962 -0.398 H 19.947 c -0.75 0 -1.361 0.61 -1.361 1.361 v 13.323 c 0 0.824 -0.668 1.492 -1.492 1.492 c -0.824 0 -1.492 -0.668 -1.492 -1.492 V 4.344 C 15.603 1.949 17.552 0 19.947 0 h 39.834 c 1.16 0 2.25 0.452 3.072 1.272 l 14.923 14.924 c 0.821 0.82 1.272 1.911 1.272 3.072 v 60.784 C 79.048 82.446 77.1 84.395 74.705 84.395 z" style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-linejoin: miter; stroke-miterlimit: 10; fill: rgb(124,124,124); fill-rule: nonzero; opacity: 1;" transform=" matrix(1 0 0 1 0 0) " stroke-linecap="round"/>\n' +
            '</g>\n' +
            '</svg>' +
            '</a>';
        customDiv.style.marginTop = "10px";
        // fireRunGroup.parentNode.insertBefore(customDiv, studentGroup.nextSibling);
        studentGroup.appendChild(customDiv);
    }

    // const dlGroup = document.querySelector("#driver_license_parameters-group");
    // if (dlGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/identificationdocuments/?q='+empEmail+'&type__exact=DL">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     dlGroup.appendChild(customDiv);
    // }
    //
    // const passportGroup = document.querySelector("#passport_parameters-group");
    // if (passportGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/identificationdocuments/?q='+empEmail+'&type__exact=PASSPORT">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     passportGroup.appendChild(customDiv);
    // }
    //
    // const ssnGroup = document.querySelector("#ssn_parameters-group");
    // if (ssnGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/identificationdocuments/?q='+empEmail+'&type__exact=SSN">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     ssnGroup.appendChild(customDiv);
    // }
    //
    // const medicalGroup = document.querySelector("#medical_card_parameters-group");
    // if (medicalGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/identificationdocuments/?q='+empEmail+'&type__exact=MEDICAL_CARD">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     medicalGroup.appendChild(customDiv);
    // }
    //
    // const availabilityGroup = document.querySelector("#availability_parameters-group");
    // if (availabilityGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/availability/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     availabilityGroup.appendChild(customDiv);
    // }
    //
    // const dispatchingstatusesGroup = document.querySelector("#dispatching_statuses_parameters-group");
    // if (dispatchingstatusesGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/dispatchingstatus/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     dispatchingstatusesGroup.appendChild(customDiv);
    // }
    //
    // const drugtestparametersGroup = document.querySelector("#drug_test_parameters-group");
    // if (drugtestparametersGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/drugtest/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     drugtestparametersGroup.appendChild(customDiv);
    // }
    //
    // const employmentpacketGroup = document.querySelector("#employment_packet_parameters-group");
    // if (employmentpacketGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/employmentpacket/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     employmentpacketGroup.appendChild(customDiv);
    // }
    //
    // const interactionGroup = document.querySelector("#interaction_parameters-group");
    // if (interactionGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/interaction/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     interactionGroup.appendChild(customDiv);
    // }
    //
    // const iqccardGroup = document.querySelector("#iqc_card_parameters-group");
    // if (iqccardGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/iqccard/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     iqccardGroup.appendChild(customDiv);
    // }
    //
    // const manifestGroup = document.querySelector("#manifest_parameters-group");
    // if (manifestGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/companymanifest/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     manifestGroup.appendChild(customDiv);
    // }
    //
    // const mspaGroup = document.querySelector("#mspa_parameters-group");
    // if (mspaGroup) {
    //     const customDiv = document.createElement("div");
    //     customDiv.innerHTML = '<a target="_blank" rel="noreferrer noopener" href="/admin/company/mspa/?q='+empEmail+'">History</a>';
    //     customDiv.style.margin = "0 10px";
    //     mspaGroup.appendChild(customDiv);
    // }


});

