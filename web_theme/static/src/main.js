/** @odoo-module **/

import { startWebClient } from "@web/start";
import { WebClientTheme } from "./webclient/webclient";
import "./webclient/color_scheme/apply_color_scheme";

/**
 * This file starts the theme webclient. In the manifest, it replaces
 * the standard webclient.
 * (WebClientTheme instead of WebClient)
 */

if ("serviceWorker" in navigator) {
    navigator.serviceWorker
        .register("/web/service-worker.js", { scope: "/web" })
        .catch((error) => {
            console.error("Service worker registration failed:", error);
        });
}

startWebClient(WebClientTheme);
