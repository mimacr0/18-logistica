/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";

class AccountProductMapListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    productMapCreate() {
        this.actionService.doAction("rma_base.action_rma_add_product_map_wizard");
    }
}

export const accountProductMapListView = {
    ...listView,
    Controller: AccountProductMapListController,
    buttonTemplate: "rma_base.AccountProductMapListView.Buttons",
};

registry.category("views").add("account_product_map_list_view", accountProductMapListView);
