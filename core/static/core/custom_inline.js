// document.addEventListener("DOMContentLoaded", function() {
//     const headers = document.querySelectorAll('.inline-related h2');
//     headers.forEach(header => {
//         header.style.cursor = 'pointer';
//         header.addEventListener('mousedown', (event) => {
//             event.preventDefault();
//             const formset = header.nextElementSibling;
//             console.log(formset);
//             formset.style.display = formset.style.display === 'none' ? 'table' : 'none';
//         });
//     });
// });

document.addEventListener("DOMContentLoaded", function() {
    const headers = document.querySelectorAll('.inline-heading');
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        const fieldset = header.parentElement;

        fieldset.classList.add('collapsible');
        fieldset.style.height = fieldset.scrollHeight + 30 + 'px';

        header.addEventListener('mousedown', (event) => {
            event.preventDefault();
            if (fieldset.style.height === '40px' || fieldset.style.height === '') {
                fieldset.style.height = fieldset.scrollHeight + 'px';
            } else {
                fieldset.style.height = '40px';
            }
        });
    });
});

// document.addEventListener("DOMContentLoaded", function() {
//     const headers = document.querySelectorAll('.inline-heading');
//     headers.forEach(header => {
//         header.style.cursor = 'pointer';
//         const fieldset = header.parentElement;
//         fieldset.classList.add('collapsible');
//
//         fieldset.style.height = fieldset.scrollHeight + 'px';
//
//         header.addEventListener('mousedown', (event) => {
//             event.preventDefault();
//             if (fieldset.style.height === '40px') {
//                 fieldset.style.height = fieldset.scrollHeight + 'px';
//             } else {
//                 fieldset.style.height = '40px';
//             }
//         });
//     });
// });

