grp.jQuery(document).ready(function () {
    const preview = document.querySelector("#employees_form .img-click");
    const documentField = document.querySelector("#employees_form .document");
    if (preview && documentField) {
        preview.addEventListener("click", function () {
            documentField.classList.toggle("open");
        });
    }
});
