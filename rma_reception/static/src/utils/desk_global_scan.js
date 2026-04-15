/** @odoo-module **/

import { browser } from "@web/core/browser/browser";

/**
 * Foco en el input de búsqueda tras montar la mesa: Odoo a veces deja el foco en el buscador global;
 * varios intentos ganan a ese refocus.
 */
export function scheduleDeskSearchAutofocus(focusFn) {
    const run = () => focusFn();
    if (typeof globalThis.queueMicrotask === "function") {
        globalThis.queueMicrotask(run);
    } else {
        Promise.resolve().then(run);
    }
    browser.setTimeout(run, 0);
    browser.setTimeout(run, 120);
    browser.setTimeout(run, 350);
}

/**
 * Si devuelve true, no capturar el keydown del lector.
 * Solo se ignoran teclas cuando el objetivo es un control de formulario DENTRO de la mesa
 * (o dentro de `embeddedFormRoot`). Los inputs fuera de la mesa (p. ej. buscador Odoo) no bloquean.
 */
export function deskGlobalScanSkipForTarget(rootEl, searchEl, embeddedFormRoot, t) {
    if (!rootEl || !t || !(t instanceof Node)) {
        return true;
    }
    if (searchEl && t === searchEl) {
        return true;
    }
    const isForm =
        t instanceof HTMLInputElement ||
        t instanceof HTMLTextAreaElement ||
        t instanceof HTMLSelectElement ||
        (t instanceof HTMLElement && t.isContentEditable);
    if (!isForm) {
        return false;
    }
    if (embeddedFormRoot && embeddedFormRoot.contains(t)) {
        return true;
    }
    return rootEl.contains(t);
}
