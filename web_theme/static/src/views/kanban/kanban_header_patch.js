/* @odoo-module */

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { KanbanHeader } from "@web/views/kanban/kanban_header";
// Removed import of PromoteStudioAutomationDialog
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";

patch(KanbanHeader.prototype, {
    /**
     * @override
     */
    get permissions() {
        const permissions = super.permissions;
        Object.defineProperty(permissions, "canEditAutomations", {
            get: () => user.isAdmin,
            configurable: true,
        });
        return permissions;
    },

    async openAutomations() {
        if (typeof this._openAutomations === "function") {
            // this is the case if base_automation is installed
            return this._openAutomations();
        } else {
            // Removed PromoteStudioAutomationDialog - functionality has been removed
            return;
        }
    },
});

registry.category("kanban_header_config_items").add(
    "open_automations",
    {
        label: _t("Automations"),
        method: "openAutomations",
        isVisible: ({ permissions }) => permissions.canEditAutomations,
        class: "o_column_automations",
    },
    { sequence: 25, force: true }
);
