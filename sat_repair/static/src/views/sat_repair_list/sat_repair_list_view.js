/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { RmaRepairListDashboardPipeline } from "./sat_repair_list_dashboard_pipeline";

export class RmaRepairListRenderer extends ListRenderer {
    static template = "sat_repair.RmaRepairListRenderer";
}

RmaRepairListRenderer.components = {
    ...ListRenderer.components,
    RmaRepairListDashboardPipeline,
};

export const RmaRepairListView = {
    ...listView,
    Renderer: RmaRepairListRenderer,
};

registry.category("views").add("sat_repair_list_dashboard", RmaRepairListView);
