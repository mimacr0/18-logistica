import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { getFieldDomain } from "@web/model/relational_model/utils";
import { useSpecialData } from "@web/views/fields/relational_utils";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class ResponsiveSelectorField extends Component {
    static template = "widget_responsive_selector.ResponsiveSelectorField";
    static props = {
        ...standardFieldProps,
        domain: { type: [Array, Function], optional: true },
        icons: { type: String, optional: true }, // Format: "key1:icon1,key2:icon2"
        colors: { type: String, optional: true }, // Format: "key1:color1,key2:color2"
    };

    setup() {
        this.type = this.props.record.fields[this.props.name].type;
        if (this.type === "many2one") {
            this.specialData = useSpecialData((orm, props) => {
                const domain = getFieldDomain(props.record, props.name, props.domain);
                const { relation } = props.record.fields[props.name];
                return orm.call(relation, "name_search", ["", domain]);
            });
        }
        
        this.iconMap = {};
        if (this.props.icons) {
            for (const item of this.props.icons.split(',')) {
                const [key, icon] = item.split(':');
                this.iconMap[key] = icon;
            }
        }

        this.colorMap = {};
        if (this.props.colors) {
            for (const item of this.props.colors.split(',')) {
                const [key, color] = item.split(':');
                this.colorMap[key] = color;
            }
        }
    }

    get options() {
        switch (this.type) {
            case "many2one":
                return (this.specialData.data || []).map(opt => ({
                    value: opt[0],
                    label: opt[1],
                    icon: this.iconMap[opt[0]] || 'fa-circle-o',
                    color: this.colorMap[opt[0]] || ''
                }));
            case "selection":
                return this.props.record.fields[this.props.name].selection.map(opt => ({
                    value: opt[0],
                    label: opt[1],
                    icon: this.iconMap[opt[0]] || 'fa-circle-o',
                    color: this.colorMap[opt[0]] || ''
                }));
            default:
                return [];
        }
    }

    get value() {
        const rawValue = this.props.record.data[this.props.name];
        return this.type === "many2one" && rawValue ? rawValue[0] : rawValue;
    }

    /**
     * @param {string | number | false} value
     */
    onChange(value) {
        if (value === this.value) {
            const { required } = this.props.record.fields[this.props.name];
            if (!required) {
                this.props.record.update({ [this.props.name]: false });
            }
            return;
        }

        switch (this.type) {
            case "many2one":
                const option = this.specialData.data.find((o) => o[0] === value);
                this.props.record.update({ [this.props.name]: option || false });
                break;
            case "selection":
                this.props.record.update({ [this.props.name]: value });
                break;
        }
    }
}

export const responsiveSelectorField = {
    component: ResponsiveSelectorField,
    displayName: _t("Responsive Selector"),
    supportedTypes: ["many2one", "selection"],
    supportedOptions: [
        {
            label: "Icons Mapping",
            name: "icons",
            type: "string",
        },
        {
            label: "Colors Mapping",
            name: "colors",
            type: "string",
        }
    ],
    isEmpty: (record, fieldName) => record.data[fieldName] === false,
    extractProps: (fieldInfo, dynamicInfo) => ({
        domain: dynamicInfo.domain,
        icons: fieldInfo.options.icons,
        colors: fieldInfo.options.colors,
    }),
};

registry.category("fields").add("responsive_selection", responsiveSelectorField);
