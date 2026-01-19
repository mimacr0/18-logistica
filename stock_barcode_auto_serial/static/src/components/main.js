/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MainComponent from "@stock_barcode/components/main";

/**
 * Extend MainComponent to add printBarcodes method.
 */
patch(MainComponent.prototype, {
    /**
     * Print lot/serial labels for the current picking.
     * Opens the lot label layout wizard directly.
     */
    async printLotBarcodes(ev) {
        ev.stopPropagation();
        const model = this.env.model;
        if (model.resModel === 'stock.picking' && model.resId) {
            await this.actionMutex.exec(async () => {
                const action = await this.orm.call(
                    'stock.picking',
                    'action_print_lot_labels',
                    [[model.resId]]
                );
                if (action) {
                    await this.action.doAction(action);
                }
            });
        }
    },
});
