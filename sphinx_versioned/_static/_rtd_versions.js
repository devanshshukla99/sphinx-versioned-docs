window.addEventListener("DOMContentLoaded", (event) => {
    let versionsElement = document.getElementsByClassName("rst-versions")
    Array.from(versionsElement).forEach(element => {
        element.addEventListener("click", (e) => {
            e.currentTarget.classList.toggle("shift-up")
        })
    });
});
