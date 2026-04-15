/** @odoo-module **/

import { Component, onMounted, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { _t } from "@web/core/l10n/translation";

/** Scripts UMD servidos como estáticos (no empaquetados) para window.JsBarcode y window.jspdf. */
const RMA_LABEL_VENDOR_SCRIPTS = [
    "/rma_label/static/src/js/vendor/jsbarcode.all.min.js",
    "/rma_label/static/src/js/vendor/jspdf.umd.min.js",
];

let vendorsLoadPromise = null;

/**
 * @returns {Promise<void>}
 */
export function ensureRmaLabelVendorScripts() {
    if (typeof window.JsBarcode === "function" && typeof window.jspdf?.jsPDF === "function") {
        return Promise.resolve();
    }
    if (!vendorsLoadPromise) {
        vendorsLoadPromise = (async () => {
            for (const url of RMA_LABEL_VENDOR_SCRIPTS) {
                await loadJS(url);
            }
        })().catch((e) => {
            vendorsLoadPromise = null;
            throw e;
        });
    }
    return vendorsLoadPromise;
}

/** 30 × 20 mm @ ~96 dpi (misma idea que el PDF de nombre RMA). */
const MM = 96 / 25.4;
const LABEL_W = Math.round(30 * MM);
const LABEL_H = Math.round(20 * MM);

/** Píxeles reales = lógicos × escala (PDF / pantalla nítidos; ~96×4 ≈ 384 dpi efectivos). */
const LABEL_EXPORT_SCALE = 4;

/** Tamaño de página PDF = etiqueta física (mm). */
const PDF_PAGE_MM = [30, 20];

/**
 * Etiqueta compacta: nombre RMA + SKU/serie + Code128.
 * Misma cadena de código de barras que el informe QWeb (nombre RMA).
 */
export async function drawRmaUnitLabelToCanvas(canvas, data) {
    await ensureRmaLabelVendorScripts();
    const S = LABEL_EXPORT_SCALE;
    const ctx = canvas.getContext("2d");
    const { name, account_sku, serial } = data;
    const code = (name || "").trim() || "RMA";
    const padX = 4;

    canvas.width = LABEL_W * S;
    canvas.height = LABEL_H * S;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(S, S);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, LABEL_W, LABEL_H);
    const topY = 8;

    ctx.fillStyle = "#0f172a";
    ctx.font = `700 ${Math.max(9, Math.floor(LABEL_H * 0.14))}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText(code, padX, topY);

    const meta = [account_sku, serial].filter(Boolean).join(" · ");
    if (meta) {
        ctx.fillStyle = "#475569";
        ctx.font = `500 ${Math.max(6, Math.floor(LABEL_H * 0.09))}px sans-serif`;
        const maxW = LABEL_W - padX - 4;
        let line = meta;
        while (line.length > 2 && ctx.measureText(line).width > maxW) {
            line = `${line.slice(0, -2)}…`;
        }
        ctx.fillText(line, padX, topY + Math.floor(LABEL_H * 0.2));
    }

    const barcodeY = Math.floor(LABEL_H * 0.42);
    const barcodeH = Math.max(18, Math.floor(LABEL_H * 0.32));
    const barcodeW = LABEL_W - padX - 4;

    try {
        const bc = document.createElement("canvas");
        window.JsBarcode(bc, code, {
            format: "CODE128",
            width: Math.max(1, (1.2 * S) / 2),
            height: Math.max(1, Math.round(barcodeH * S)),
            displayValue: false,
            margin: 0,
        });
        ctx.drawImage(bc, padX, barcodeY, barcodeW, barcodeH);
    } catch (e) {
        console.error(e);
        ctx.fillStyle = "#dc3545";
        ctx.font = "7px sans-serif";
        ctx.fillText("Barcode", padX, barcodeY);
    }
}

export class RmaUnitLabelCanvas extends Component {
    static template = "rma_label.RmaUnitLabelCanvas";
    static props = { ...standardActionServiceProps };
    static displayName = _t("RMA unit label");

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.canvasRef = useRef("label-canvas");
        this.state = useState({ loading: true, error: "", labelName: "" });

        onMounted(async () => {
            const id =
                this.props.action?.params?.rma_unit_id ||
                this.props.action?.context?.active_id;
            if (!id) {
                this.state.loading = false;
                this.state.error = _t("Missing RMA unit.");
                return;
            }
            try {
                const rows = await this.orm.read(
                    "rma.unit",
                    [id],
                    ["name", "display_name", "account_sku", "serial"],
                );
                const row = rows[0];
                if (!row) {
                    this.state.error = _t("RMA unit not found.");
                    return;
                }
                this.state.labelName = (row.name || "").trim() || "RMA";
                const canvas = this.canvasRef.el;
                if (canvas) {
                    await drawRmaUnitLabelToCanvas(canvas, row);
                }
            } catch (e) {
                console.error(e);
                this.state.error = _t("Could not load the RMA unit.");
            } finally {
                this.state.loading = false;
            }
        });
    }

    get dialogTitle() {
        const a = this.props.action;
        return a?.display_name || a?.name || _t("RMA unit label");
    }

    onPrint() {
        window.print();
    }

    /**
     * Misma idea que barcode_locations/labels.js (generatePDF): canvas → JPEG → jsPDF.
     * Página 30×20 mm (no 100×60 de ubicaciones).
     */
    async onDownloadPdf() {
        const canvas = this.canvasRef.el;
        if (!canvas || this.state.loading || this.state.error) {
            return;
        }
        try {
            await ensureRmaLabelVendorScripts();
        } catch (e) {
            console.error(e);
            this.notification.add(_t("Could not load PDF libraries."), { type: "danger" });
            return;
        }
        const jspdf = window.jspdf;
        if (!jspdf?.jsPDF) {
            this.notification.add(_t("PDF library is not available."), { type: "danger" });
            return;
        }
        try {
            const { jsPDF } = jspdf;
            const [wMm, hMm] = PDF_PAGE_MM;
            // portrait con ancho > alto hace que jsPDF invierta a ~20×30; landscape = 30 mm ancho × 20 mm alto
            const pdf = new jsPDF({ orientation: "landscape", unit: "mm", format: [wMm, hMm] });
            const imgData = canvas.toDataURL("image/png");
            pdf.addImage(imgData, "PNG", 0, 0, wMm, hMm);
            const safe = (this.state.labelName || "RMA").replace(/[^a-zA-Z0-9._-]+/g, "_");
            pdf.save(`RMA-${safe}-${Date.now()}.pdf`);
            this.notification.add(_t("PDF downloaded"), { type: "success" });
        } catch (e) {
            console.error(e);
            this.notification.add(_t("Could not generate PDF."), { type: "danger" });
        }
    }

    onClose() {
        this.action.doAction({ type: "ir.actions.act_window_close" });
    }
}

registry.category("actions").add("rma_label.RmaUnitLabelCanvas", RmaUnitLabelCanvas);
