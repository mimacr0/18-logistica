/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { debounce } from "@web/core/utils/timing";

const MIN_SEARCH_LEN = 2;
/** Si el foco no está en el buscador, los caracteres del lector se acumulan; tras esta pausa se descarta el tampón (PDA / Bluetooth algo más lento). */
const SCAN_BUFFER_IDLE_MS = 600;

function scheduleDeskSearchAutofocus(focusFn) {
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

/** true = no capturar; solo controles dentro de la mesa (no el buscador Odoo fuera). */
function deskGlobalScanSkipForTarget(rootEl, searchEl, embeddedFormRoot, t) {
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

function normalizeToken(value) {
    return (value || "").trim().toLowerCase();
}

/**
 * Coincidencia total con el término buscado (nombre RMA, display_name, SKU, serie o IMEI).
 * @param {object} r registro rma.unit de searchRead
 * @param {string} term término ya recortado
 */
function recordExactMatch(r, term) {
    const t = normalizeToken(term);
    if (!t) {
        return false;
    }
    const fields = [r.name, r.display_name, r.account_sku, r.serial, r.imei];
    return fields.some((v) => normalizeToken(v) === t);
}

/**
 * @param {object} q fila devuelta por move_search_quants
 */
function quantExactMatchRaw(q, term) {
    const t = normalizeToken(term);
    if (!t) {
        return false;
    }
    const fields = [
        q.map_name,
        q.map_account_sku,
        q.map_ean13,
        q.map_fnsku,
        q.map_asin,
        q.map_template_name,
        q.location_barcode,
    ];
    return fields.some((v) => normalizeToken(v) === t);
}

const STATE_LABELS = {
    received: _t("Received"),
    review: _t("In review"),
    repair: _t("In repair"),
    stored: _t("Stored"),
    shipped: _t("Shipped"),
    stock: _t("Stock"),
};

const STATE_BADGE = {
    received: "text-bg-info",
    review: "text-bg-warning",
    repair: "text-bg-warning",
    stored: "text-bg-success",
    shipped: "text-bg-secondary",
    stock: "text-bg-secondary",
};

export class RmaUnitMoveDesk extends Component {
    static template = "rma_inventory.UnitMoveDesk";
    static props = ["*"];

    setup() {
        this.notification = useService("notification");
        this.searchInputRef = useRef("search-input");

        this.state = useState({
            searchHits: [],
            /** @type {object[]} */
            selected: [],
            /** Selector jerárquico bajo NV1/Stock (o raíces configuradas) */
            locRoot: null,
            /** Si hay varias raíces, se guardan aquí para «Subir un nivel» al listado inicial */
            /** @type {{ id: number, name: string, display_name: string, has_children: boolean, usage: string }[]} */
            locRootOptions: [],
            /** @type {{ id: number, name: string }[]} */
            locStack: [],
            /** @type {{ id: number, name: string, display_name: string, has_children: boolean, usage: string }[]} */
            locChildren: [],
            /** Ubicaciones internas con quants o unidades RMA que comparten mapa con las líneas */
            /** @type {{ id: number, name: string, display_name: string, complete_name: string, has_children: boolean, usage: string }[]} */
            locMapSuggestions: [],
            locLeafId: false,
            locLeafName: "",
            locLoading: false,
        });

        this.debounceSearch = debounce(() => this.searchFromInput(false), 400);

        this._deskScanBuffer = "";
        this._deskScanTimer = null;
        this._onGlobalKeydownCapture = (ev) => this.onGlobalScanKeydownCapture(ev);

        onMounted(() => {
            document.addEventListener("keydown", this._onGlobalKeydownCapture, true);
            scheduleDeskSearchAutofocus(() => this.focusSearchInput());
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", this._onGlobalKeydownCapture, true);
            if (this._deskScanTimer) {
                browser.clearTimeout(this._deskScanTimer);
                this._deskScanTimer = null;
            }
        });
    }

    focusSearchInput() {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                this.searchInputRef.el?.focus?.();
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
     * Captura global (fase capture): el lector envía teclas aunque el foco esté en un botón o en la vista.
     * No interfiere si el foco está en otro campo de formulario o en el propio buscador.
     */
    onGlobalScanKeydownCapture(ev) {
        if (!this.el?.isConnected) {
            return;
        }
        const el = this.searchInputRef.el;
        if (!el) {
            return;
        }
        if (deskGlobalScanSkipForTarget(this.el, el, null, ev.target)) {
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

    /**
     * Enter dispara búsqueda inmediata (lectores de código de barras suelen terminar con Enter).
     */
    onSearchKeydown(ev) {
        if (ev.key !== "Enter") {
            return;
        }
        ev.preventDefault();
        this.debounceSearch.cancel();
        this.clearDeskScanBuffer();
        this.searchFromInput(true);
    }

    formatHit(r) {
        const st = r.state || "";
        return {
            kind: "rma",
            rowKey: `rma-${r.id}`,
            id: r.id,
            name: r.display_name || r.name || `#${r.id}`,
            sku: r.account_sku || "",
            state: st,
            stateLabel: STATE_LABELS[st] || st,
            locationLabel: r.location_id ? r.location_id[1] : "",
        };
    }

    formatQuantHit(q) {
        const avail = Number(q.available_qty) || 0;
        const locBc = q.location_barcode || "";
        const locHuman = q.location_id ? q.location_id[1] : q.location_name || "";
        return {
            kind: "quant",
            rowKey: `quant-${q.id}`,
            id: q.id,
            name: q.product_display_name || `#${q.id}`,
            sku: q.product_default_code || "",
            state: "stock",
            stateLabel: STATE_LABELS.stock,
            locationLabel: locBc || locHuman,
            locationBarcode: locBc,
            lotLabel: q.lot_name || "",
            clientMapSku: q.map_account_sku || "",
            qtyMax: avail,
            qty: avail,
        };
    }

    isSelected(rowKey) {
        return this.state.selected.some((s) => s.rowKey === rowKey);
    }

    resetLocationPicker() {
        this.state.locRoot = null;
        this.state.locRootOptions = [];
        this.state.locStack = [];
        this.state.locChildren = [];
        this.state.locMapSuggestions = [];
        this.state.locLeafId = false;
        this.state.locLeafName = "";
        this.state.locLoading = false;
    }

    async loadMapSuggestions() {
        const rma_unit_ids = [];
        const quant_ids = [];
        for (const s of this.state.selected) {
            if (s.kind === "rma") {
                rma_unit_ids.push(s.id);
            } else if (s.kind === "quant") {
                quant_ids.push(s.id);
            }
        }
        if (!rma_unit_ids.length && !quant_ids.length) {
            this.state.locMapSuggestions = [];
            return;
        }
        try {
            this.state.locMapSuggestions = await rpc("/rma_inventory/desk/move/suggest_map_locations", {
                rma_unit_ids,
                quant_ids,
            });
        } catch {
            this.state.locMapSuggestions = [];
        }
    }

    async _initLocationTree() {
        try {
            const roots = await rpc("/rma_inventory/desk/move/root_locations", {});
            if (!roots.length) {
                return;
            }
            if (roots.length === 1) {
                const root = roots[0];
                this.state.locRoot = root;
                this.state.locStack = [{ id: root.id, name: root.display_name }];
                const kids = await this.loadLocationChildren(root.id);
                this.state.locChildren = kids;
                if (!kids.length && root.usage === "internal") {
                    this.state.locLeafId = root.id;
                    this.state.locLeafName = root.display_name;
                }
            } else {
                this.state.locRootOptions = roots;
                this.state.locRoot = {
                    complete_name: _t("Multiple root locations configured — choose a location below"),
                    multi: true,
                };
                this.state.locStack = [];
                this.state.locChildren = roots;
            }
        } catch {
            /* RPC error ya mostrado */
        }
    }

    async initLocationPicker() {
        this.state.locLoading = true;
        this.resetLocationPicker();
        try {
            await Promise.all([this._initLocationTree(), this.loadMapSuggestions()]);
        } finally {
            this.state.locLoading = false;
        }
    }

    /**
     * @returns {boolean} true si se añadió la fila (no estaba ya seleccionada)
     */
    addHit(line) {
        if (this.isSelected(line.rowKey)) {
            return false;
        }
        const first = !this.state.selected.length;
        const row =
            line.kind === "quant"
                ? { ...line, qty: line.qtyMax }
                : { ...line };
        this.state.selected = [...this.state.selected, row];
        this.state.searchHits = [];
        if (this.searchInputRef.el) {
            this.searchInputRef.el.value = "";
        }
        if (first) {
            this.initLocationPicker();
        } else {
            this.loadMapSuggestions();
        }
        return true;
    }

    removeSelected(rowKey) {
        this.state.selected = this.state.selected.filter((s) => s.rowKey !== rowKey);
        if (!this.state.selected.length) {
            this.resetLocationPicker();
        } else {
            this.loadMapSuggestions();
        }
    }

    clearSearchHits() {
        this.state.searchHits = [];
    }

    onQuantQtyInput(rowKey, ev) {
        const idx = this.state.selected.findIndex((s) => s.rowKey === rowKey);
        if (idx < 0 || this.state.selected[idx].kind !== "quant") {
            return;
        }
        const row = this.state.selected[idx];
        let v = parseFloat(String(ev.target.value).replace(",", "."));
        if (Number.isNaN(v)) {
            v = row.qtyMax;
        }
        v = Math.min(row.qtyMax, Math.max(0, v));
        if (v <= 0 && row.qtyMax > 0) {
            v = row.qtyMax;
        }
        const next = [...this.state.selected];
        next[idx] = { ...row, qty: v };
        this.state.selected = next;
    }

    async searchFromInput(warnIfShort) {
        try {
        const term = (this.searchInputRef.el?.value || "").trim();
        if (term.length < MIN_SEARCH_LEN) {
            this.clearSearchHits();
            if (warnIfShort) {
                this.notification.add(
                    _t("Enter at least 2 characters (RMA, client map, location barcode…)."),
                    { type: "warning" },
                );
            }
            return;
        }
        if (this.state.selected.length) {
            try {
                const locRes = await rpc("/rma_inventory/desk/move/resolve_location_barcode", {
                    term,
                });
                if (locRes.status === "ok" && locRes.location) {
                    const loc = locRes.location;
                    this.pickSuggestedLocation(loc);
                    this.clearSearchHits();
                    if (this.searchInputRef.el) {
                        this.searchInputRef.el.value = "";
                    }
                    this.notification.add(
                        _t("Destination set to: %s", loc.display_name || loc.name),
                        { type: "success" },
                    );
                    return;
                }
                if (locRes.status === "ambiguous") {
                    this.notification.add(
                        _t(
                            "Several internal locations share this barcode. Choose the destination from the list or tree."
                        ),
                        { type: "warning" },
                    );
                    return;
                }
            } catch {
                /* continuar con búsqueda de unidades / quants */
            }
        }
        let records;
        let quants;
        try {
            [records, quants] = await Promise.all([
                rpc("/rma_inventory/desk/move/search_units", { term }),
                rpc("/rma_inventory/desk/move/search_quants", { term }),
            ]);
        } catch {
            return;
        }
        const total = records.length + quants.length;
        if (!total) {
            this.clearSearchHits();
            this.notification.add(
                _t("No RMA units or internal stock found that matches (client map or location barcode)."),
                { type: "warning" },
            );
            return;
        }
        if (total === 1) {
            const line = records.length ? this.formatHit(records[0]) : this.formatQuantHit(quants[0]);
            const added = this.addHit(line);
            this.notification.add(
                added ? _t("Line added (single result).") : _t("Line already in the list."),
                { type: added ? "success" : "info" },
            );
            return;
        }
        const exactHits = [];
        for (const r of records) {
            if (recordExactMatch(r, term)) {
                exactHits.push(this.formatHit(r));
            }
        }
        for (const q of quants) {
            if (quantExactMatchRaw(q, term)) {
                exactHits.push(this.formatQuantHit(q));
            }
        }
        if (exactHits.length === 1) {
            const added = this.addHit(exactHits[0]);
            this.notification.add(
                added ? _t("Line added (exact match).") : _t("Line already in the list."),
                { type: added ? "success" : "info" },
            );
            return;
        }
        const merged = [...records.map((r) => this.formatHit(r)), ...quants.map((q) => this.formatQuantHit(q))];
        this.state.searchHits = merged;
        } finally {
            this.focusSearchInput();
        }
    }

    searchUnits() {
        return this.searchFromInput(true);
    }

    async loadLocationChildren(parentId) {
        return rpc("/rma_inventory/desk/move/location_children", { parent_id: parentId });
    }

    suggestionLocationClass(locId) {
        const base = "btn py-3 text-wrap ";
        return base + (this.state.locLeafId === locId ? "btn-success" : "btn-outline-success");
    }

    pickSuggestedLocation(loc) {
        if (loc.usage !== "internal") {
            this.notification.add(
                _t("The destination must be an internal storage location."),
                { type: "warning" },
            );
            return;
        }
        this.state.locLeafId = loc.id;
        this.state.locLeafName = loc.display_name || loc.name;
        this.state.locChildren = [];
        this.state.locStack = [];
    }

    async onLocationPick(loc) {
        this.state.locLoading = true;
        try {
            const kids = await this.loadLocationChildren(loc.id);
            if (kids.length) {
                this.state.locStack = [
                    ...this.state.locStack,
                    { id: loc.id, name: loc.display_name || loc.name },
                ];
                this.state.locLeafId = false;
                this.state.locLeafName = "";
                this.state.locChildren = kids;
            } else {
                if (loc.usage !== "internal") {
                    this.notification.add(
                        _t(
                            "This location is not an internal storage location. Continue down the tree or go up and choose another branch."
                        ),
                        { type: "warning" },
                    );
                    return;
                }
                this.state.locLeafId = loc.id;
                this.state.locLeafName = loc.display_name || loc.name;
                this.state.locChildren = [];
            }
        } finally {
            this.state.locLoading = false;
        }
    }

    async locationGoUp() {
        if (this.state.locLeafId) {
            this.state.locLeafId = false;
            this.state.locLeafName = "";
            if (!this.state.locStack.length && this.state.locRootOptions.length > 1) {
                this.state.locChildren = this.state.locRootOptions;
                return;
            }
            if (!this.state.locStack.length && this.state.locRoot && !this.state.locRoot.multi) {
                this.state.locLoading = true;
                try {
                    this.state.locChildren = await this.loadLocationChildren(this.state.locRoot.id);
                } finally {
                    this.state.locLoading = false;
                }
                return;
            }
            if (!this.state.locStack.length) {
                return;
            }
            const parentId = this.state.locStack[this.state.locStack.length - 1].id;
            this.state.locLoading = true;
            try {
                this.state.locChildren = await this.loadLocationChildren(parentId);
            } finally {
                this.state.locLoading = false;
            }
            return;
        }
        if (
            this.state.locStack.length === 1 &&
            this.state.locRootOptions.length > 1
        ) {
            this.state.locStack = [];
            this.state.locChildren = this.state.locRootOptions;
            return;
        }
        if (this.state.locStack.length <= 1) {
            return;
        }
        this.state.locStack = this.state.locStack.slice(0, -1);
        const pid = this.state.locStack[this.state.locStack.length - 1].id;
        this.state.locLoading = true;
        try {
            this.state.locChildren = await this.loadLocationChildren(pid);
        } finally {
            this.state.locLoading = false;
        }
    }

    get canLocationGoUp() {
        if (this.state.locLeafId) {
            return true;
        }
        if (this.state.locStack.length > 1) {
            return true;
        }
        return this.state.locStack.length === 1 && this.state.locRootOptions.length > 1;
    }

    async confirmDestination() {
        if (!this.state.locLeafId || !this.state.selected.length) {
            return;
        }
        const rma_unit_ids = [];
        const quant_lines = [];
        for (const s of this.state.selected) {
            if (s.kind === "quant") {
                quant_lines.push({ quant_id: s.id, quantity: s.qty });
            } else {
                rma_unit_ids.push(s.id);
            }
        }
        this.state.locLoading = true;
        try {
            await rpc("/rma_inventory/desk/move/apply_destination", {
                location_id: this.state.locLeafId,
                rma_unit_ids,
                quant_lines,
            });
            this.notification.add(
                _t("Movement applied to %s.", this.state.locLeafName),
                { type: "success" },
            );
            this.state.selected = [];
            this.resetLocationPicker();
        } catch {
            /* error RPC */
        } finally {
            this.state.locLoading = false;
            this.focusSearchInput();
        }
    }

    stateBadgeClass(state) {
        return STATE_BADGE[state] || "text-bg-secondary";
    }

    get title() {
        return this.props.action?.name || _t("Move stock (workstation)");
    }

    exit() {
        this.env.config?.historyBack?.();
    }
}

registry.category("actions").add("rma_inventory.UnitMoveDesk", RmaUnitMoveDesk);
