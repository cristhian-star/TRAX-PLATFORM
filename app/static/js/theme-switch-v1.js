(function () {
    const STORAGE_KEY = "trax-theme";
    const root = document.documentElement;
    const switchButton = document.querySelector("[data-theme-switch]");

    const getStoredTheme = () => {
        try {
            return localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light";
        } catch (error) {
            return "light";
        }
    };

    const persistTheme = (theme) => {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (error) {
            // localStorage can be unavailable in strict browser modes.
        }
    };

    const applyTheme = (theme) => {
        root.classList.remove("theme-light", "theme-dark");
        root.classList.add(`theme-${theme}`);

        if (!switchButton) {
            return;
        }

        const isDark = theme === "dark";
        switchButton.setAttribute("aria-pressed", String(isDark));
        switchButton.setAttribute("aria-label", isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro");

        const label = switchButton.querySelector(".theme-switch__label");
        if (label) {
            label.textContent = isDark ? "Oscuro" : "Claro";
        }
    };

    applyTheme(getStoredTheme());

    if (switchButton) {
        switchButton.addEventListener("click", () => {
            const nextTheme = root.classList.contains("theme-dark") ? "light" : "dark";
            applyTheme(nextTheme);
            persistTheme(nextTheme);
        });
    }
})();
