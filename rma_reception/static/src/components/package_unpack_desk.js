/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { debounce } from "@web/core/utils/timing";
import { deskGlobalScanSkipForTarget, scheduleDeskSearchAutofocus } from "../utils/desk_global_scan";
import { RmaReceptionPackageSearchLine } from "./package_search_line";
import { RmaPackageUnpackDeskDetail } from "./package_unpack_desk_detail";

const PACKAGE_STATE_LABELS = {
    draft: _t("Waiting Package"),
    received: _t("Received"),
    opened: _t("Opened & Inspected"),
    done: _t("Empty / Done"),
};

const RMA_UNIT_STATE_LABELS = {
    received: _t("Received"),
    review: _t("In review"),
    repair: _t("In repair"),
    stored: _t("Stored"),
    shipped: _t("Shipped"),
};

const UNIT_MOVE_METHODS = {
    review: "action_rma_to_review",
    repair: "action_rma_to_repair",
    scrap: "action_rma_to_scrap",
};

const MIN_SEARCH_LEN = 2;
const SCAN_BUFFER_IDLE_MS = 600;

/** Solo bultos en estado Recibido; sin reinicio global tras desempaquetar (flujo distinto a la mesa de recepción). */
export class RmaPackageUnpackDesk extends Component {
    static template = "rma_reception.PackageUnpackDesk";
    static components = { RmaReceptionPackageSearchLine, RmaPackageUnpackDeskDetail };
    static props = ["*"];

    setup() {
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.searchInputRef = useRef("search-input");

        this.state = useState({
            searchCandidates: [],
            candidateListSource: false,
            wizardPackageId: false,
            wizardMountKey: 0,
            /** Tras desempaquetar OK en esta mesa: siguiente paso para las unidades RMA del bulto */
            postUnpackPackageId: false,
            postUnpackLabel: "",
            /** Bloquea la sección “enviar todos” */
            postUnpackBusyAll: false,
            /** Líneas: { id, lineLabel, sku, stateLabel } */
            postUnpackUnits: [],
            /** Quants en el bulto: { id, lineLabel, qty, lotLabel, locationLabel } */
            postUnpackQuants: [],
            /** ids de fila con RPC en curso */
            postUnpackBusyIds: {},
            postUnpackBusyQuantIds: {},
            /** null = aún no cargado; contadores mesa unpack (mismos dominios que las listas) */
            pendingPackageCount: null,
            incidentPackageCount: null,
        });

        this.debounceSearch = debounce(() => this.searchFromInput(false), 450);

        this._deskScanBuffer = "";
        this._deskScanTimer = null;
        this._onGlobalKeydownCapture = (ev) => this.onGlobalScanKeydownCapture(ev);

        onWillStart(() => this.refreshUnpackDeskCounts());

        onMounted(() => {
            document.addEventListener("keydown", this._onGlobalKeydownCapture, true);
            scheduleDeskSearchAutofocus(() => this.focusSearchInput());
        });

        onWillUnmount(() => {
            document.removeEventListener("keydown", this._onGlobalKeydownCapture, true);
            this.clearDeskScanBuffer();
        });

        useBus(this.env.bus, "rma_reception_package_unpack_desk:post_unpack", async (ev) => {
            const packageId = ev.detail?.packageId;
            if (!packageId) {
                return;
            }
            this.state.wizardPackageId = false;
            this.state.wizardMountKey++;
            this.state.postUnpackBusyIds = {};
            this.state.postUnpackBusyQuantIds = {};
            this.clearPostUnpackPanel();
            await this.loadPostUnpackAfterUnpack(packageId);
            await this.refreshUnpackDeskCounts();
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

    onGlobalScanKeydownCapture(ev) {
        if (!this.el?.isConnected) {
            return;
        }
        const el = this.searchInputRef.el;
        if (!el) {
            return;
        }
        const packageEmbed = this.el.querySelector(".o_rma_desk_unpack_package_embed");
        if (deskGlobalScanSkipForTarget(this.el, el, packageEmbed, ev.target)) {
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

    onSearchKeydown(ev) {
        if (ev.key !== "Enter") {
            return;
        }
        ev.preventDefault();
        this.debounceSearch.cancel();
        this.clearDeskScanBuffer();
        this.searchFromInput(true);
    }

    async refreshUnpackDeskCounts() {
        try {
            const res = await rpc("/rma_reception/desk/packages_unpack_desk_counts", {});
            this.state.pendingPackageCount =
                typeof res?.pending === "number" ? res.pending : 0;
            this.state.incidentPackageCount =
                typeof res?.incident === "number" ? res.incident : 0;
        } catch {
            this.state.pendingPackageCount = 0;
            this.state.incidentPackageCount = 0;
        }
    }

    async loadPostUnpackAfterUnpack(packageId) {
        await this.loadPostUnpackUnits(packageId);
        await this.loadPostUnpackQuants(packageId);
        if (!this.state.postUnpackUnits.length && !this.state.postUnpackQuants.length) {
            this.notification.add(
                _t("There is nothing to triage or store in this package."),
                { type: "info" },
            );
            this.clearPostUnpackPanel();
            return;
        }
        this.state.postUnpackPackageId = packageId;
        await this.loadPostUnpackLabel(packageId);
    }

    async refreshPostUnpackPanel() {
        const pid = this.state.postUnpackPackageId;
        if (!pid) {
            return;
        }
        await this.loadPostUnpackAfterUnpack(pid);
    }

    async loadPostUnpackLabel(packageId) {
        const row = await rpc("/rma_reception/desk/post_unpack_package_label", { package_id: packageId });
        this.state.postUnpackLabel = row?.display_name || row?.name || "";
    }

    async loadPostUnpackUnits(packageId) {
        const units = await rpc("/rma_reception/desk/post_unpack_units", { package_id: packageId });
        this.state.postUnpackUnits = units.map((u) => ({
            id: u.id,
            lineLabel: u.display_name || u.name || `#${u.id}`,
            sku: u.account_sku || "",
            stateLabel: RMA_UNIT_STATE_LABELS[u.state] || u.state,
        }));
    }

    async loadPostUnpackQuants(packageId) {
        const quants = await rpc("/rma_reception/desk/post_unpack_quants", { package_id: packageId });
        this.state.postUnpackQuants = quants.map((q) => ({
            id: q.id,
            lineLabel: q.product_id ? q.product_id[1] : `#${q.id}`,
            qty: q.quantity,
            lotLabel: q.lot_id ? q.lot_id[1] : "",
            locationLabel: q.location_id ? q.location_id[1] : "",
        }));
    }

    clearPostUnpackPanel() {
        this.state.postUnpackPackageId = false;
        this.state.postUnpackLabel = "";
        this.state.postUnpackBusyAll = false;
        this.state.postUnpackUnits = [];
        this.state.postUnpackQuants = [];
        this.state.postUnpackBusyIds = {};
        this.state.postUnpackBusyQuantIds = {};
    }

    isPostUnpackRowDisabled(unitId) {
        return !!(this.state.postUnpackBusyAll || this.state.postUnpackBusyIds[unitId]);
    }

    isPostUnpackQuantRowDisabled(quantId) {
        return !!(this.state.postUnpackBusyAll || this.state.postUnpackBusyQuantIds[quantId]);
    }

    get postUnpackAnyRowBusy() {
        return (
            Object.keys(this.state.postUnpackBusyIds).length > 0 ||
            Object.keys(this.state.postUnpackBusyQuantIds).length > 0
        );
    }

    successMessageForKind(kind, plural) {
        if (plural) {
            return kind === "review"
                ? _t("All listed units moved to review.")
                : kind === "repair"
                  ? _t("All listed units moved to repair.")
                  : _t("All listed units moved to scrap.");
        }
        return kind === "review"
            ? _t("Unit moved to review.")
            : kind === "repair"
              ? _t("Unit moved to repair.")
              : _t("Unit moved to scrap.");
    }

    /**
     * @param {'review'|'repair'|'storage'|'scrap'} kind
     */
    async onPostUnpackMoveOne(unitId, kind) {
        if (this.state.postUnpackBusyAll || this.state.postUnpackBusyIds[unitId]) {
            return;
        }
        const pid = this.state.postUnpackPackageId;
        if (kind === "storage") {
            if (!pid) {
                return;
            }
            this.state.postUnpackBusyIds = { ...this.state.postUnpackBusyIds, [unitId]: true };
            try {
                const action = await rpc("/rma_reception/desk/package_call", {
                    method: "action_unpack_desk_open_store_wizard_rma",
                    package_id: pid,
                    desk_store_rma_unit_ids: [unitId],
                });
                await this.actionService.doAction(action, {
                    onClose: () => this.refreshPostUnpackPanel(),
                });
            } finally {
                const next = { ...this.state.postUnpackBusyIds };
                delete next[unitId];
                this.state.postUnpackBusyIds = next;
            }
            return;
        }
        const method = UNIT_MOVE_METHODS[kind];
        this.state.postUnpackBusyIds = { ...this.state.postUnpackBusyIds, [unitId]: true };
        try {
            await rpc("/rma_reception/desk/rma_unit_call", { method, unit_ids: [unitId] });
            this.notification.add(this.successMessageForKind(kind, false), { type: "success" });
            this.state.postUnpackUnits = this.state.postUnpackUnits.filter((u) => u.id !== unitId);
            if (!this.state.postUnpackUnits.length && !this.state.postUnpackQuants.length) {
                this.clearPostUnpackPanel();
            }
        } finally {
            const next = { ...this.state.postUnpackBusyIds };
            delete next[unitId];
            this.state.postUnpackBusyIds = next;
        }
    }

    async onPostUnpackQuantStoreOne(quantId) {
        if (this.state.postUnpackBusyAll || this.state.postUnpackBusyQuantIds[quantId]) {
            return;
        }
        const pid = this.state.postUnpackPackageId;
        if (!pid) {
            return;
        }
        this.state.postUnpackBusyQuantIds = { ...this.state.postUnpackBusyQuantIds, [quantId]: true };
        try {
            const action = await rpc("/rma_reception/desk/package_call", {
                method: "action_unpack_desk_open_store_wizard_quants",
                package_id: pid,
                desk_store_quant_ids: [quantId],
            });
            await this.actionService.doAction(action, {
                onClose: () => this.refreshPostUnpackPanel(),
            });
        } finally {
            const next = { ...this.state.postUnpackBusyQuantIds };
            delete next[quantId];
            this.state.postUnpackBusyQuantIds = next;
        }
    }

    /**
     * @param {'review'|'repair'|'storage'|'scrap'} kind
     */
    async onPostUnpackMoveAll(kind) {
        const pid = this.state.postUnpackPackageId;
        if (!pid || this.state.postUnpackBusyAll || this.postUnpackAnyRowBusy) {
            return;
        }
        if (kind === "storage") {
            this.state.postUnpackBusyAll = true;
            try {
                const action = await rpc("/rma_reception/desk/package_call", {
                    method: "action_unpack_desk_move_to_storage",
                    package_id: pid,
                });
                await this.actionService.doAction(action, {
                    onClose: () => this.refreshPostUnpackPanel(),
                });
            } finally {
                this.state.postUnpackBusyAll = false;
            }
            return;
        }
        const methodByKind = {
            review: "action_unpack_desk_move_to_review",
            repair: "action_unpack_desk_move_to_repair",
            scrap: "action_unpack_desk_move_to_scrap",
        };
        const method = methodByKind[kind];
        this.state.postUnpackBusyAll = true;
        try {
            await rpc("/rma_reception/desk/package_call", { method, package_id: pid });
            this.notification.add(this.successMessageForKind(kind, true), { type: "success" });
            await this.refreshPostUnpackPanel();
        } finally {
            this.state.postUnpackBusyAll = false;
        }
    }

    async postUnpackAllQuantStorage() {
        const pid = this.state.postUnpackPackageId;
        if (!pid || this.state.postUnpackBusyAll || this.postUnpackAnyRowBusy) {
            return;
        }
        this.state.postUnpackBusyAll = true;
        try {
            const action = await rpc("/rma_reception/desk/package_call", {
                method: "action_unpack_desk_open_store_wizard_quants",
                package_id: pid,
            });
            await this.actionService.doAction(action, {
                onClose: () => this.refreshPostUnpackPanel(),
            });
        } finally {
            this.state.postUnpackBusyAll = false;
        }
    }

    postUnpackAllReview = () => this.onPostUnpackMoveAll("review");
    postUnpackAllRepair = () => this.onPostUnpackMoveAll("repair");
    postUnpackAllStorage = () => this.onPostUnpackMoveAll("storage");
    postUnpackAllScrap = () => this.onPostUnpackMoveAll("scrap");

    get postUnpackTitle() {
        return _t("Package unpacked");
    }

    get postUnpackSubtitle() {
        return _t(
            "Unidades RMA: revisión, reparación y chatarra usan ubicaciones fijas; almacenaje abre un asistente para elegir una ubicación interna por unidad. Quants: use Almacenar por fila o almacene todos y ajuste la ubicación en cada línea del asistente."
        );
    }

    get labelColumnUnit() {
        return _t("RMA unit.");
    }

    get labelColumnState() {
        return _t("State.");
    }

    get labelColumnActions() {
        return _t("Destination.");
    }

    get labelSendAllTitle() {
        return _t("Send all.");
    }

    get labelSendAllHint() {
        return _t("Applies to every unit still in “Received” on this package (including any not shown if the list is stale).");
    }

    get labelSendAllReview() {
        return _t("Send all — review.");
    }

    get labelSendAllRepair() {
        return _t("Send all — repair.");
    }

    get labelSendAllStorage() {
        return _t("Send all — storage (choose locations)");
    }

    get labelQuantsSection() {
        return _t("Quants in the package");
    }

    get labelColumnQty() {
        return _t("Qty.");
    }

    get labelColumnLot() {
        return _t("Lot");
    }

    get labelColumnLocation() {
        return _t("Current location");
    }

    get labelQuantStore() {
        return _t("Store");
    }

    get labelSendAllQuantStorage() {
        return _t("Store all quants — choose locations");
    }

    get labelSendAllScrap() {
        return _t("Send all — scrap");
    }

    get labelMoveReview() {
        return _t("Review");
    }

    get labelMoveRepair() {
        return _t("Repair");
    }

    get labelMoveStorage() {
        return _t("Storage");
    }

    get labelMoveScrap() {
        return _t("Scrap");
    }

    get labelDismissPostUnpack() {
        return _t("Dismiss — search another package");
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

    async searchFromInput(warnIfShort) {
        const term = (this.searchInputRef.el?.value || "").trim();
        if (term.length < MIN_SEARCH_LEN) {
            this.clearSearchResults();
            if (warnIfShort) {
                this.notification.add(
                    _t("Write at least 2 characters (transport reference, package name or tracking)."),
                    { type: "warning" },
                );
            }
            return;
        }
        const records = await rpc("/rma_reception/desk/packages_search", {
            mode: "unpack",
            term,
        });
        if (!records.length) {
            this.clearSearchResults();
            this.notification.add(_t("No received packages that match that criterion."), { type: "warning" });
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
        this.clearPostUnpackPanel();
        this.state.wizardPackageId = packageId;
        this.state.searchCandidates = [];
        this.state.candidateListSource = false;
        this.state.wizardMountKey++;
    }

    selectCandidate = (line) => {
        this.openWizardForPackage(line.id);
    };

    get title() {
        return this.props.action?.name || _t("Workstation: Unpack Packages");
    }

    get info() {
        return {
            icon: "cube",
            message: _t(
                "Packages in Received state. Search or open the list to unpack. After the checklist the screen does not restart to continue the flow (p. ej. movimientos)."
            ),
            class: "text-body",
        };
    }

    get wizardSectionTitle() {
        return _t("Package summary");
    }

    get listButtonLabel() {
        return _t("Packages List: pending to unpack");
    }

    get incidentListButtonLabel() {
        return _t("Packages in incident state");
    }

    get searchPlaceholder() {
        return _t("Reference, package name, tracking…");
    }

    get searchButtonLabel() {
        return _t("Buscar");
    }

    get searchHint() {
        return _t(
            "Minimum 2 characters. Only received packages. One result opens the form; several, list to choose. You can scan with a reader without focusing the field (not while typing in the package form)."
        );
    }

    get multiMatchHint() {
        return _t("Several packages match. Choose one to open the form:");
    }

    get doorListHint() {
        return _t("Packages in Received state ready to unpack. Choose one to open the form:");
    }

    get incidentDoorListHint() {
        return _t("Packages in Incident state. Choose one to open the summary:");
    }

    get packageListHint() {
        if (this.state.candidateListSource === "door") {
            return this.doorListHint;
        }
        if (this.state.candidateListSource === "door_incident") {
            return this.incidentDoorListHint;
        }
        return this.multiMatchHint;
    }

    get showPackageCandidateList() {
        const n = this.state.searchCandidates.length;
        if (!n || !this.state.candidateListSource) {
            return false;
        }
        if (this.state.candidateListSource === "door" || this.state.candidateListSource === "door_incident") {
            return true;
        }
        return n > 1;
    }

    get canShowWizardEmbed() {
        return !!(this.state.wizardPackageId && !this.state.postUnpackPackageId);
    }

    get showPostUnpackActions() {
        return !!(
            this.state.postUnpackPackageId &&
            (this.state.postUnpackUnits.length || this.state.postUnpackQuants.length)
        );
    }

    async openPendingList() {
        await this.refreshUnpackDeskCounts();
        const records = await rpc("/rma_reception/desk/packages_door_list", { mode: "unpack" });
        if (!records.length) {
            this.notification.add(_t("No packages in Received state pending to unpack."), {
                type: "info",
            });
            this.state.candidateListSource = false;
            this.state.searchCandidates = [];
            return;
        }
        this.clearPostUnpackPanel();
        this.state.wizardPackageId = false;
        this.state.wizardMountKey++;
        this.state.candidateListSource = "door";
        this.state.searchCandidates = records.map((r) => this.formatLine(r));
    }

    async openIncidentList() {
        await this.refreshUnpackDeskCounts();
        const records = await rpc("/rma_reception/desk/packages_door_list", {
            mode: "unpack",
            list_kind: "incident",
        });
        if (!records.length) {
            this.notification.add(_t("No packages in Incident state."), {
                type: "info",
            });
            this.state.candidateListSource = false;
            this.state.searchCandidates = [];
            return;
        }
        this.clearPostUnpackPanel();
        this.state.wizardPackageId = false;
        this.state.wizardMountKey++;
        this.state.candidateListSource = "door_incident";
        this.state.searchCandidates = records.map((r) => this.formatLine(r));
    }

    exit() {
        this.env.config?.historyBack?.();
    }
}

registry.category("actions").add("rma_reception.PackageUnpackDesk", RmaPackageUnpackDesk);

/**
 * Tras desempaquetar OK en la mesa unpack: notifica al componente y cierra el modal del checklist.
 */
registry.category("actions").add("rma_reception.unpack_desk_post_unpack", async (env, action) => {
    const packageId = action.params?.package_id;
    if (packageId) {
        env.bus.trigger("rma_reception_package_unpack_desk:post_unpack", { packageId });
    }
    return { type: "ir.actions.act_window_close" };
});
