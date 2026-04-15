/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

const PACKAGE_STATE_BADGE = {
    draft: "text-bg-secondary",
    received: "text-bg-info",
    opened: "text-bg-primary",
    done: "text-bg-success",
};

export class RmaReceptionPackageSearchLine extends Component {
    static template = "rma_reception.PackageSearchLine";
    static props = {
        line: Object,
        onSelect: Function,
        isSelected: { type: Boolean, optional: true },
    };

    get openLabel() {
        return _t("Abrir");
    }

    get stateBadgeClass() {
        if (this.props.line.package_has_incident) {
            return "text-bg-warning";
        }
        return PACKAGE_STATE_BADGE[this.props.line.package_state] || "text-bg-secondary";
    }

    onOpen() {
        this.props.onSelect(this.props.line);
    }
}
