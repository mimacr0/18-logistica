/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import BarcodeModel from "@stock_barcode/models/barcode_model";

/**
 * Patch BarcodeModel to prevent grouping serial-tracked products.
 * 
 * This ensures that products with tracking='serial' are displayed 
 * one by one in the barcode interface, as each unit has a unique serial number.
 */
patch(BarcodeModel.prototype, {
    lineCannotBeGrouped(line) {
        // Don't try to group a line who is not tracked, is serial tracked, or is already grouped.
        // Serial tracked products should always be shown 1 by 1 (each unit has unique serial)
        return line.product_id.tracking === 'none' || line.product_id.tracking === 'serial' || line.lines;
    }
});
