import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class QRWidget extends Component {
    static template = "widget_qr_attachments.QRWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            qrUrl: "",
            urlConfigured: false,
        });

        onWillStart(async () => {
            await this._updateQRUrl();
        });

        // Re-fetch token when record reloads (e.g. after regenerate)
        onWillUpdateProps(async (nextProps) => {
            await this._updateQRUrl();
        });
    }

    async _updateQRUrl() {
        const record = this.props.record;
        if (!record.resId) {
            this.state.qrUrl = "";
            this.state.urlConfigured = false;
            return;
        }

        let baseUrl = "";
        
        try {
            const externalUrl = await this.orm.call('ir.config_parameter', 'get_param', ['widget_qr_attachments.qr_external_base_url']);
            if (externalUrl && externalUrl.trim() !== "") {
                baseUrl = externalUrl.trim().replace(/\/$/, "");
                this.state.urlConfigured = true;
            } else {
                this.state.urlConfigured = false;
                this.state.qrUrl = "";
                return;
            }
        } catch (e) {
            console.error("Error fetching QR external URL", e);
            this.state.urlConfigured = false;
            return;
        }

        // Get or create the access token via qr.access.token model
        let accessToken = "";
        try {
            accessToken = await this.orm.call('qr.access.token', 'get_or_create_token', [record.resModel, record.resId]);
        } catch (e) {
            console.warn("Could not get access token for QR", e);
        }

        const uploadUrl = `${baseUrl}/qr_upload/${record.resModel}/${record.resId}?token=${accessToken}`;
        
        this.state.qrUrl = `/report/barcode/?barcode_type=QR&value=${encodeURIComponent(uploadUrl)}&width=200&height=200`;
        this.state.fullUploadUrl = uploadUrl;
    }

    openUploadUI() {
        window.open(this.state.fullUploadUrl, '_blank');
    }
}

export const qrWidget = {
    component: QRWidget,
    supportedTypes: ["char", "text", "integer"],
};

registry.category("fields").add("qr_attachments", qrWidget);
