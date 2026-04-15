/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

/** Tarjetas de filtro rápido (iconos + colores por estado). */
const QUICK_FILTER_ITEMS = [
    { key: "all", label: _t("Todas"), icon: "fa-th-large", color: "#92400e" },
    { key: "draft", label: _t("Borrador"), icon: "fa-file-text-o", color: "#0ea5e9" },
    { key: "confirmed", label: _t("En curso"), icon: "fa-cogs", color: "#f59e0b" },
    { key: "done", label: _t("Reparada"), icon: "fa-check-circle", color: "#22c55e" },
    { key: "cancel", label: _t("Cancelada"), icon: "fa-times-circle", color: "#ef4444" },
];

export class RmaRepairListDashboardPipeline extends Component {
    static template = "sat_repair.RmaRepairListDashboardPipeline";
    static props = {};

    setup() {
        this.state = useState({ currentFilter: null });
    }

    get quickFilterItems() {
        return QUICK_FILTER_ITEMS;
    }

    stateCardButtonStyle(item) {
        if (!this.isActive(item.key)) {
            return "";
        }
        const c = item.color;
        return `border-color: ${c} !important; background-color: ${c}14;`;
    }

    stateCardIconStyle(item) {
        return this.isActive(item.key)
            ? `color: ${item.color} !important;`
            : "color: #6c757d;";
    }

    stateCardLabelStyle(item) {
        return this.isActive(item.key) ? `color: ${item.color} !important;` : "";
    }

    setFilter(filterKey) {
        const sm = this.env.searchModel;
        if (!sm) {
            return;
        }
        if (filterKey === "all") {
            sm.clearQuery();
            this.state.currentFilter = null;
            return;
        }
        if (this.state.currentFilter === filterKey) {
            sm.clearQuery();
            this.state.currentFilter = null;
            return;
        }
        const domain = [["state", "=", filterKey]];
        const item = QUICK_FILTER_ITEMS.find((i) => i.key === filterKey);
        sm.clearQuery();
        sm.createNewFilters([
            {
                description: item ? item.label : filterKey,
                domain: JSON.stringify(domain),
            },
        ]);
        this.state.currentFilter = filterKey;
    }

    isActive(filterKey) {
        if (filterKey === "all") {
            return this.state.currentFilter === null;
        }
        return this.state.currentFilter === filterKey;
    }
}
