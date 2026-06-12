// Flash message fade out
document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
        setTimeout(() => {
            alert.classList.add("fade");
            setTimeout(() => alert.remove(), 500);
        }, 3000);
    });
});

// Confirm before delete action
const deleteButtons = document.querySelectorAll(".btn-delete");
deleteButtons.forEach((btn) => {
    btn.addEventListener("click", function (e) {
        if (!confirm("Are you sure you want to delete this item?")) {
            e.preventDefault();
        }
    });
});
