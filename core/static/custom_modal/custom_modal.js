function showModal(src) {
    let modal = document.getElementById("imgModal");
    if (!modal) {
        modal = document.createElement("div");
        modal.id = "imgModal";
        modal.innerHTML = `
            <span id="imgModalClose">&times;</span>
            <img id="imgModalContent">
        `;
        document.body.appendChild(modal);
        document.getElementById("imgModalClose").onclick = () => closeModal();
        modal.onclick = e => {
            if (e.target === modal) closeModal();
        };
    }

    document.getElementById("imgModalContent").src = src;
    modal.style.display = "block";
}

function closeModal() {
    const modal = document.getElementById("imgModal");
    if (modal) modal.style.display = "none";
}
