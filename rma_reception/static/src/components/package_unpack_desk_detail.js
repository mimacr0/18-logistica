/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

/**
 * Vista embebida en la mesa Unpack: resumen del bulto y productos declarados.
 * El desempaquetado (checklist → RMA o quants) es siempre para el paquete completo.
 */
export class RmaPackageUnpackDeskDetail extends Component {
    static template = "rma_reception.PackageUnpackDeskDetail";
    static props = ["*"];

    setup() {
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            data: null,
            busyUnpack: false,
            selectedUnpackCheckIds: [],
        });

        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.loading = true;
        this.state.data = null;
        try {
            const row = await rpc("/rma_reception/desk/unpack_package_detail", {
                package_id: this.props.packageId,
            });
            this.state.data = row && row.id ? row : null;
            const checks = (row && row.check_lines) || [];
            this.state.selectedUnpackCheckIds = checks.filter((c) => c.failed).map((c) => c.id);
        } finally {
            this.state.loading = false;
        }
    }

    get labelName() {
        return _t("Package");
    }
    get labelProductMap() {
        return _t("Account product map");
    }
    get labelType() {
        return _t("Type");
    }
    get labelWeight() {
        return _t("Shipping weight");
    }
    get labelLocation() {
        return _t("Current location");
    }
    get labelDeclared() {
        return _t("Declared products (account map)");
    }
    get labelQtyDeclared() {
        return _t("Declared qty");
    }
    get labelQtyReceived() {
        return _t("Received qty");
    }
    get labelProductLocation() {
        return _t("Product location");
    }
    get labelUnpackRma() {
        return _t("Unpack package (RMA)");
    }
    get labelUnpackQuant() {
        return _t("Unpack package (stock)");
    }
    get labelDone() {
        return _t("Unpacked");
    }
    get labelNoLines() {
        return _t("No declared lines on this package.");
    }
    get labelNothingLeftToUnpack() {
        return _t("Nothing left to unpack for this package.");
    }
    get labelReceptionUnpackChecks() {
        return _t("Reception unpack checks");
    }
    get labelReceptionUnpackChecksHelp() {
        return _t(
            "Mark any item that is an incident. Unpack will still complete and the package will be flagged."
        );
    }

    toggleUnpackCheck(lineId) {
        const cur = [...this.state.selectedUnpackCheckIds];
        const idx = cur.indexOf(lineId);
        if (idx >= 0) {
            cur.splice(idx, 1);
        } else {
            cur.push(lineId);
        }
        this.state.selectedUnpackCheckIds = cur;
    }

    unpackMethodForPackage() {
        const t = this.state.data?.type;
        if (t === "return") {
            return "action_unpack_rma";
        }
        if (t === "new") {
            return "action_unpack_quant";
        }
        return null;
    }

    get unpackButtonLabel() {
        const t = this.state.data?.type;
        if (t === "return") {
            return this.labelUnpackRma;
        }
        if (t === "new") {
            return this.labelUnpackQuant;
        }
        return "";
    }

    async onUnpackPackage() {
        const method = this.unpackMethodForPackage();
        if (!method || this.state.busyUnpack || !this.state.data?.can_unpack) {
            return;
        }
        this.state.busyUnpack = true;
        try {
            const action = await rpc("/rma_reception/desk/package_call", {
                method,
                package_id: this.props.packageId,
                desk_unpack_incident_line_ids: this.state.selectedUnpackCheckIds,
            });
            if (action && action.type) {
                await this.actionService.doAction(action, {
                    onClose: () => this.loadData(),
                });
            }
        } catch (e) {
            this.notification.add(e.message || String(e), { type: "danger" });
        } finally {
            this.state.busyUnpack = false;
        }
    }
}
