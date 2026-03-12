/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.RmaLabelPortalForm = publicWidget.Widget.extend({
    selector: '.js_rma_label_portal_form',
    events: {
        'click #add_product_row': '_onAddProductRow',
        'click .remove_product_row': '_onRemoveProductRow',
        'click #add_sender_address_btn': '_onAddSenderAddress',
        'click #btn_save_new_sender': '_onSaveNewSender',
    },

    /**
     * @override
     */
    start: function () {
        this._productRowTemplate = this.$el.find('.product_row').first().clone();
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onAddProductRow: function (ev) {
        var $newRow = this._productRowTemplate.clone();
        $newRow.find('input').val(1);
        this.$el.find('#rma_products_table tbody').append($newRow);
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onRemoveProductRow: function (ev) {
        var $row = $(ev.currentTarget).closest('.product_row');
        if (this.$el.find('.product_row').length > 1) {
            $row.remove();
        } else {
            alert("At least one product is required.");
        }
    },

    /**
     * @private
     */
    _onAddSenderAddress: function () {
        this.$('#modal_add_sender').modal('show');
    },

    /**
     * @private
     */
    _onSaveNewSender: function () {
        var self = this;
        var vals = {
            'name': this.$('#new_sender_name').val(),
            'street': this.$('#new_sender_street').val(),
            'city': this.$('#new_sender_city').val(),
            'zip': this.$('#new_sender_zip').val(),
            'country_id': this.$('#new_sender_country_id').val(),
            'phone': this.$('#new_sender_phone').val(),
        };

        if (!vals.name) {
            alert("Name is required");
            return;
        }

        this.rpc('/my/rma_labels/add_sender', vals).then(function (result) {
            if (result && result.id) {
                // Add to select and select it
                var $select = self.$('#sender_id_select');
                var $option = $('<option>', {
                    value: result.id,
                    text: result.name,
                    selected: true
                });
                $select.append($option);
                
                // Close modal
                self.$('#modal_add_sender').modal('hide');
                // Clear form
                self.$('#form_add_sender')[0].reset();
            }
        });
    },
});

export default publicWidget.registry.RmaLabelPortalForm;
