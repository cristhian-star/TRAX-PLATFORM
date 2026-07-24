(function () {
    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-trax-alert-dismiss]");
        if (!button) {
            return;
        }

        var alert = button.closest(".trax-alert");
        if (!alert) {
            return;
        }

        alert.hidden = true;
    });
})();
