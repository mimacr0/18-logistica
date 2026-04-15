/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BadgeSelectionField, badgeSelectionField } from "@web/views/fields/badge_selection/badge_selection_field";

patch(BadgeSelectionField.prototype, {
    getOptionClass(optionValue) {
        const colors = this.props.colors || {};
        let baseClass = colors[optionValue];
        if (!baseClass || typeof baseClass !== 'string') {
            baseClass = "btn-secondary";
        }

        if (this.value === optionValue) {
            // Transition outline to solid for active state
            if (baseClass.includes('btn-outline-')) {
                baseClass = baseClass.replace('btn-outline-', 'btn-');
            }
            return baseClass + " active-badge-selected";
        }
        return baseClass;
    }
});

Object.assign(BadgeSelectionField.props, {
    colors: { type: Object, optional: true },
});

const originalExtractProps = badgeSelectionField.extractProps;
badgeSelectionField.extractProps = (fieldInfo, dynamicInfo) => {
    const props = originalExtractProps(fieldInfo, dynamicInfo);
    props.colors = fieldInfo.options.colors || {};
    return props;
};
