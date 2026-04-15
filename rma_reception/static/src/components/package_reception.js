/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { View } from "@web/views/view";
import { useBus, useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { debounce } from "@web/core/utils/timing";
import { deskGlobalScanSkipForTarget, scheduleDeskSearchAutofocus } from "../utils/desk_global_scan";
import { RmaReceptionPackageSearchLine } from "./package_search_line";

const PACKAGE_STATE_LABELS = {
    draft: _t("Waiting Package"),
    received: _t("Received"),
    opened: _t("Opened & Inspected"),
    done: _t("Empty / Done"),
};

const MIN_SEARCH_LEN = 2;
/** Tampón global del lector: tras esta pausa sin teclas se descarta (PDA / Bluetooth). */
const SCAN_BUFFER_IDLE_MS = 600;

/** Mesa de puerta: solo bultos en espera (borrador); vista wizard `form_desk` con Confirmar. */
export class RmaPackageReception extends Component {
    static template = "rma_reception.PackageReception";
    static components = { View, RmaReceptionPackageSearchLine };
    static props = ["*"];

    setup() {
        this.notification = useService("notification");
        this.searchInputRef = useRef("search-input");
        this.wizardFormViewId = false;

        this.state = useState({
            searchCandidates: [],
            /** @type {false | 'search_multi' | 'door'} */
            candidateListSource: false,
            wizardPackageId: false,
            wizardMountKey: 0,
        });

        this.debounceSearch = debounce(() => this.searchFromInput(false), 450);

        this._deskScanBuffer = "";
        this._deskScanTimer = null;
        this._onGlobalKeydownCapture = (ev) => this.onGlobalScanKeydownCapture(ev);

        onWillStart(async () => {
            this.wizardFormViewId = await rpc("/rma_reception/desk/reception_wizard_form_view_id", {});
        });

        onMounted(() => {
            document.addEventListener("keydown", this._onGlobalKeydownCapture, true);
            scheduleDeskSearchAutofocus(() => this.focusSearchInput());
        });

        onWillUnmount(() => {
            document.removeEventListener("keydown", this._onGlobalKeydownCapture, true);
            this.clearDeskScanBuffer();
        });

        useBus(this.env.bus, "rma_reception_package_reception:clear_search", () => {
            this.resetDeskSearch();
        });
    }

    focusSearchInput() {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.searchInputRef.el?.focus?.({ preventScroll: true });
            });
        });
    }

    clearDeskScanBuffer() {
        this._deskScanBuffer = "";
        if (this._deskScanTimer) {
            browser.clearTimeout(this._deskScanTimer);
            this._deskScanTimer = null;
        }
    }

    /**
     * Captura global (fase capture), misma idea que la mesa «Mover stock».
     */
    onGlobalScanKeydownCapture(ev) {
        if (!this.el?.isConnected) {
            return;
        }
        const el = this.searchInputRef.el;
        if (!el) {
            return;
        }
        const wizardBody = this.el.querySelector(".o_rma_reception_wizard_body");
        if (deskGlobalScanSkipForTarget(this.el, el, wizardBody, ev.target)) {
            return;
        }
        if (ev.key === "Escape") {
            this.clearDeskScanBuffer();
            return;
        }
        if (ev.key === "Enter") {
            const buf = this._deskScanBuffer.trim();
            this.clearDeskScanBuffer();
            if (buf.length < MIN_SEARCH_LEN) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            el.value = buf;
            this.debounceSearch.cancel();
            this.searchFromInput(true);
            this.focusSearchInput();
            return;
        }
        if (ev.key.length === 1 && !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
            this._deskScanBuffer += ev.key;
            if (this._deskScanTimer) {
                browser.clearTimeout(this._deskScanTimer);
            }
            this._deskScanTimer = browser.setTimeout(() => {
                this._deskScanBuffer = "";
                this._deskScanTimer = null;
            }, SCAN_BUFFER_IDLE_MS);
            ev.preventDefault();
            ev.stopPropagation();
        }
    }

    /** Enter en el buscador: búsqueda inmediata (lectores suelen terminar con Enter). */
    onSearchKeydown(ev) {
        if (ev.key !== "Enter") {
            return;
        }
        ev.preventDefault();
        this.debounceSearch.cancel();
        this.clearDeskScanBuffer();
        this.searchFromInput(true);
    }

    /**
     * Tras confirmar en desk: vacía el campo de búsqueda, la lista de coincidencias y oculta el wizard.
     * Los datos del asistente embebido se descartan (nuevo bulto = nuevo wizard al volver a buscar).
     */
    resetDeskSearch() {
        this.clearDeskScanBuffer();
        const el = this.searchInputRef.el;
        if (el) {
            el.value = "";
        }
        this.clearSearchResults();
        if (this.el) {
            this.el.scrollTop = 0;
        }
    }

    formatLine(r) {
        const base = PACKAGE_STATE_LABELS[r.package_state] || r.package_state || "";
        const hasIn = !!r.package_has_incident;
        const package_state_label = hasIn
            ? base
                ? `${base} · ${_t("Incident")}`
                : _t("Incident")
            : base;
        return {
            id: r.id,
            name: r.name || "",
            customer_reference: r.customer_reference || "",
            package_state: r.package_state,
            package_has_incident: hasIn,
            package_state_label,
            carrier_label: r.carrier_id ? r.carrier_id[1] : "",
            sender_label: r.sender_id ? r.sender_id[1] : "",
            type: r.type,
        };
    }

    clearSearchResults() {
        this.state.searchCandidates = [];
        this.state.candidateListSource = false;
        this.state.wizardPackageId = false;
        this.state.wizardMountKey++;
    }

    /**
     * @param {boolean} warnIfShort - true al pulsar "Buscar"; aviso si el término es corto
     */
    async searchFromInput(warnIfShort) {
        const term = (this.searchInputRef.el?.value || "").trim();
        if (term.length < MIN_SEARCH_LEN) {
            this.clearSearchResults();
            if (warnIfShort) {
                this.notification.add(
                    _t("Enter at least 2 characters (transport reference, package name or tracking number)."),
                    { type: "warning" },
                );
            }
            return;
        }
        const records = await rpc("/rma_reception/desk/packages_search", {
            mode: "reception",
            term,
        });
        if (!records.length) {
            this.clearSearchResults();
            this.notification.add(_t("No packages waiting (draft) that match that criterion."), {
                type: "warning",
            });
            return;
        }
        if (records.length === 1) {
            this.state.searchCandidates = [];
            this.state.candidateListSource = false;
            this.openWizardForPackage(records[0].id);
            return;
        }
        this.state.wizardPackageId = false;
        this.state.wizardMountKey++;
        this.state.candidateListSource = "search_multi";
        this.state.searchCandidates = records.map((r) => this.formatLine(r));
    }

    searchPackages() {
        return this.searchFromInput(true);
    }

    openWizardForPackage(packageId) {
        this.state.wizardPackageId = packageId;
        this.state.searchCandidates = [];
        this.state.candidateListSource = false;
        this.state.wizardMountKey++;
    }

    selectCandidate = (line) => {
        this.openWizardForPackage(line.id);
    };

    getWizardViewProps() {
        const ctx = { ...(this.props.action?.context || {}) };
        delete ctx.package_reception_desk_mode;
        ctx.package_reception_desk = true;
        if (this.state.wizardPackageId) {
            ctx.default_package_id = this.state.wizardPackageId;
        }
        return {
            resModel: "rma.reception.package.wizard",
            type: "form",
            viewId: this.wizardFormViewId,
            resId: false,
            context: ctx,
            domain: [],
            groupBy: [],
            orderBy: [],
            display: { controlPanel: false, mode: "edit" },
        };
    }

    get title() {
        return this.props.action?.name || _t("Workstation: Reception");
    }

    get info() {
        return {
            icon: "search",
            message: _t(
                "Only packages waiting (draft). Search by transport reference, name or tracking number."
            ),
            class: "text-body",
        };
    }

    get wizardSectionTitle() {
        return _t("Package reception");
    }

    get wizardSectionSubtitle() {
        return _t("Complete the data and confirm to register the reception.");
    }

    get findReceptionLabel() {
        return _t("List: waiting for reception");
    }

    get searchPlaceholder() {
        return _t("Transport reference, package name, tracking number…");
    }

    get searchButtonLabel() {
        return _t("Search");
    }

    get searchHint() {
        return _t(
            "Minimum 2 characters. Only packages waiting (draft). One result opens the assistant; several, list to choose. You can scan with a reader without clicking in the field (does not apply if you write inside the assistant)."
        );
    }

    get multiMatchHint() {
        return _t("Several packages match. Choose one to load the assistant:");
    }

    get doorListHint() {
        return _t("Packages waiting for reception (draft). Choose one to load the assistant:");
    }

    get packageListHint() {
        return this.state.candidateListSource === "door" ? this.doorListHint : this.multiMatchHint;
    }

    get showPackageCandidateList() {
        const n = this.state.searchCandidates.length;
        if (!n || !this.state.candidateListSource) {
            return false;
        }
        if (this.state.candidateListSource === "door") {
            return true;
        }
        return n > 1;
    }

    get canShowWizardEmbed() {
        return !!(this.state.wizardPackageId && this.wizardFormViewId);
    }

    /** Oculta el botón de lista de pendientes mientras el asistente del bulto está visible. */
    get showPendingReceptionListButton() {
        return !this.canShowWizardEmbed;
    }

    async openDoorReceptionList() {
        const records = await rpc("/rma_reception/desk/packages_door_list", { mode: "reception" });
        if (!records.length) {
            this.notification.add(
                _t("No packages waiting for reception (draft)."),
                { type: "info" },
            );
            this.state.candidateListSource = false;
            this.state.searchCandidates = [];
            return;
        }
        this.state.wizardPackageId = false;
        this.state.wizardMountKey++;
        this.state.candidateListSource = "door";
        this.state.searchCandidates = records.map((r) => this.formatLine(r));
    }

    exit() {
        this.env.config?.historyBack?.();
    }
}

registry.category("actions").add("rma_reception.PackageReception", RmaPackageReception);

/**
 * Mesa de recepción: vacía buscador, lista y wizard embebido.
 * - Solo desk (params.desk): sin siguiente acción (tras Confirmar).
 * - Con params.next: encadenar (p. ej. cierre del modal tras unpack exitoso en esa mesa).
 * - Sin desk: cierre estándar (formularios fuera de la mesa).
 */
registry.category("actions").add("rma_reception.clear_desk_search", async (env, action) => {
    env.bus.trigger("rma_reception_package_reception:clear_search");
    if (action.params?.next) {
        return action.params.next;
    }
    if (action.params?.desk) {
        return;
    }
    return { type: "ir.actions.act_window_close" };
});
