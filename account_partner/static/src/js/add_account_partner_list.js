/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";

class ClientAccountListController extends ListController {
    setup() {
        super.setup();
    }

    clientAccount() {
        this.actionService.doAction("account_partner.action_add_account_partner_view");
    }
}

export const clientAccountListView = Object.assign({}, listView, {
    Controller: ClientAccountListController,
    buttonTemplate: "account_partner.ClientAccountListView.Buttons",
});

registry.category("views").add("account_partner_view_list_js", clientAccountListView);