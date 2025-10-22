/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";
import { registry } from "@web/core/registry";

/**
 * Service to apply color scheme to the root element on page load
 */
export const applyColorSchemeService = {
    dependencies: [],
    start() {
        const applyScheme = () => {
            const scheme = cookie.get("color_scheme") || "light";
            if (scheme === "dark") {
                document.documentElement.classList.add("o_dark_mode");

                // Apply dark mode to home menu explicitly if present
                const homeMenu = document.querySelector(".o_home_menu_background");
                if (homeMenu) {
                    homeMenu.classList.add("o_dark_mode");
                }
            } else {
                document.documentElement.classList.remove("o_dark_mode");

                // Remove dark mode from home menu explicitly if present
                const homeMenu = document.querySelector(".o_home_menu_background");
                if (homeMenu) {
                    homeMenu.classList.remove("o_dark_mode");
                }
            }
        };

        // Apply on initial load and after DOM updates
        browser.addEventListener("DOMContentLoaded", applyScheme);
        browser.addEventListener("load", applyScheme);

        // Apply immediately
        applyScheme();

        return {};
    },
};

registry.category("services").add("apply_color_scheme", applyColorSchemeService);