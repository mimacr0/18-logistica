/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class BarcodeLocationsListController extends ListController {
    setup() {
        super.setup();
    }

    onOpenBarcodeLocations() {
        window.open("/stock/barcode/locations/main", "_blank");
    }
}

export const barcodeLocationsListView = {
    ...listView,
    Controller: BarcodeLocationsListController,
    buttonTemplate: "barcode_locations.ListView.Buttons",
};

registry.category("views").add("barcode_locations_list", barcodeLocationsListView);
