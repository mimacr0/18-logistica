/** @odoo-module */

import { registry } from "@web/core/registry"
import { listView } from "@web/views/list/list_view"
import { ListController } from "@web/views/list/list_controller"
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

class AccountCarrierSelectListController extends ListController {
    setup() {
        super.setup();
        this.notificationService = useService("notification");
        this.actionService = useService("action");
    }

    selectCarriers() {
        if (this.nbSelected == 0) {
            this.notificationService.add(
                _t("No hay transportistas seleccionados"),
                { type: "danger" }
            )
            return
        }

        // Mostrar notificación de procesamiento
        this.notificationService.add(
            _t("Guardando selección..."),
            { type: "info" }
        )

        const ctx = Object.assign({}, this.props.context, {
            selected_ids: this.selectedRecords.map((record) => record.resId)
        })

        this.actionService.doAction('account_partner.server_action_account_carrier_select', {
            additionalContext: ctx,
            onClose: () => {
                // Mostrar notificación de éxito
                this.notificationService.add(
                    _t("Transportistas guardados correctamente"),
                    { type: "success" }
                )

                // Recargar la vista para mostrar los cambios
                this.model.root.load();
            }
        })
    }

    get selectedRecords() {
        return this.model.root.selection
    }
}

export const accountCarrierSelectListView = Object.assign({}, listView, {
    Controller: AccountCarrierSelectListController,
    buttonTemplate: "account_partner.AccountCarrierSelectListView.Buttons"
})

registry.category("views").add("account_carrier_select_list_view", accountCarrierSelectListView)