(function () {
    function togglePassword(button) {
        var targetId = button.getAttribute("aria-controls");
        var input = targetId ? document.getElementById(targetId) : null;
        if (!input) {
            return;
        }

        var isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        button.textContent = isPassword ? "Ocultar" : "Mostrar";
        button.setAttribute("aria-label", isPassword ? "Ocultar contrasena" : "Mostrar contrasena");
    }

    function passwordScore(value) {
        var score = 0;
        if (value.length >= 8) score += 1;
        if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score += 1;
        if (/\d/.test(value)) score += 1;
        if (/[^A-Za-z0-9]/.test(value)) score += 1;
        return score;
    }

    function updateStrength(input) {
        var container = document.getElementById("register-password-strength");
        if (!container) {
            return;
        }

        var bar = container.querySelector("span");
        var label = container.querySelector("small");
        var score = passwordScore(input.value || "");
        var width = ["0%", "28%", "52%", "76%", "100%"][score];
        var text = ["Fortaleza pendiente", "Débil", "Aceptable", "Buena", "Fuerte"][score];
        var color = ["var(--trax-ds-warning)", "var(--trax-ds-danger)", "var(--trax-ds-warning)", "var(--trax-ds-info)", "var(--trax-ds-success)"][score];

        bar.style.setProperty("--auth-strength-width", width);
        bar.style.setProperty("--auth-strength-color", color);
        label.textContent = text;
    }

    function updateRoleCopy() {
        var copy = document.querySelector("[data-role-copy]");
        var selected = document.querySelector("[data-role-option]:checked");
        if (!copy || !selected) {
            return;
        }

        copy.textContent = selected.value === "PROFESIONAL"
            ? "Creá tu cuenta profesional y después completá rubro, cobertura, verificación y portfolio."
            : "Creá tu cuenta para publicar solicitudes, comparar profesionales y operar con más orden.";
    }

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-password-toggle]");
        if (button) {
            togglePassword(button);
        }
    });

    document.querySelectorAll("[data-password-strength]").forEach(function (input) {
        updateStrength(input);
        input.addEventListener("input", function () {
            updateStrength(input);
        });
    });

    document.querySelectorAll("[data-role-option]").forEach(function (input) {
        input.addEventListener("change", updateRoleCopy);
    });
    updateRoleCopy();

    document.querySelectorAll("[data-auth-form]").forEach(function (form) {
        form.addEventListener("submit", function () {
            var button = form.querySelector("[data-auth-submit]");
            if (!button || button.disabled) {
                return;
            }

            button.classList.add("is-loading");
            button.disabled = true;
        });
    });
})();
