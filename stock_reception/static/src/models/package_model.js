/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";

// export default class StockQuantPackageModel extends BarcodeModel {
export default class StockQuantPackageModel {

    _getName() {
        return _t('Package');
    }

    setData(data) {
        this.formViewId = data.form_view_id
        this.info = data.info
    }

}
