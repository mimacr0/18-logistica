/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import BarcodePickingModel from "@stock_barcode/models/barcode_picking_model";
import { _t } from "@web/core/l10n/translation";

/**
 * Extend BarcodePickingModel to check for lines needing auto-serial before validation.
 * If lines need serials, skips the backorder dialog and lets the server handle the wizard first.
 */
patch(BarcodePickingModel.prototype, {
    /**
     * Check if there are lines that haven't been scanned/picked yet.
     * Returns true if all lines are picked or if there are no lines.
     */
    _hasUnpickedLines() {
        const lines = this.currentState.lines || [];
        for (const line of lines) {
            // Check if line has demand but is not picked
            if (!line.picked && line.product_uom_qty > 0) {
                return true;
            }
        }
        return false;
    },

    /**
     * Override validate to check for lines needing auto-serial.
     * If lines need serials, bypass the backorder dialog and let server show the wizard.
     */
    async validate() {
        // Basic validations from original method
        if (this.config.restrict_scan_dest_location == 'mandatory' &&
            !this.lastScanned.destLocation && this.selectedLine) {
            return this.notification(_t("Destination location must be scanned"), { type: "danger" });
        }
        if (this.config.lines_need_to_be_packed &&
            this.currentState.lines.some(line => this._lineNeedsToBePacked(line))) {
            return this.notification(_t("All products need to be packed"), { type: "danger" });
        }
        await this._setUser();
        
        // First save any scanned data to the database
        await this.save();
        
        // Check if there are lines that need auto-serial generation
        const needsWizard = await this._checkNeedsAutoSerialWizard();
        
        if (needsWizard) {
            // Skip backorder dialog - let server handle the serial wizard first
            console.log('[stock_barcode_auto_serial] Lines need auto-serial, skipping backorder dialog');
            return this._validateDirect();
        }
        
        // Check if there are unpicked lines - if so, show backorder dialog (don't auto-validate)
        if (this._hasUnpickedLines()) {
            console.log('[stock_barcode_auto_serial] Has unpicked lines, using normal validation flow');
        }
        
        // No lines need auto-serial, use normal validation flow
        return super.validate(...arguments);
    },

    /**
     * Validate directly without showing backorder dialog.
     * Used when lines need auto-serial - server will show wizard first.
     */
    async _validateDirect() {
        if (this.record.return_id) {
            this.validateContext = {...this.validateContext, picking_ids_not_to_backorder: this.resId};
        }
        if (this.shouldOpenSignatureModal) {
            this.openSignatureDialog(true);
            return;
        }
        const context = this.validateContext;
        context['barcode_trigger'] = true;
        const action = await this.orm.call(
            this.resModel,
            this.validateMethod,
            [[this.resId]],
            { context }
        );
        const options = { onClose: this._closeValidate.bind(this) };
        if (action && typeof action === 'object') {
            return this.action.doAction(action, options);
        }
    },

    /**
     * Check if there are lines that need auto-serial generation.
     * Returns true if wizard should be opened.
     */
    async _checkNeedsAutoSerialWizard() {
        try {
            const result = await this.orm.call(
                this.resModel,
                'check_needs_auto_serial',
                [[this.resId]]
            );
            return result.needs_wizard;
        } catch (error) {
            console.error('[stock_barcode_auto_serial] Error checking auto serial needs:', error);
            return false;
        }
    },
});
