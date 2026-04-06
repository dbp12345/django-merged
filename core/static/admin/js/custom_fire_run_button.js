document.addEventListener("DOMContentLoaded", function () {
    const empId = document.getElementById("employee-id")?.value;
    const fireRunGroup = document.querySelector("#fire_run_entries-group");
    if (fireRunGroup) {
        const customDiv = document.createElement("div");
        customDiv.innerHTML = '<a href="/admin/exhibit/get/docx?id='+empId+'" class="fire_run_button_run">Exhibit-N.docx</a>';
        customDiv.style.marginTop = "10px";
        // fireRunGroup.parentNode.insertBefore(customDiv, fireRunGroup.nextSibling);
        fireRunGroup.appendChild(customDiv);  // 👈 вставляем внутрь, в самый конец
    }
});
