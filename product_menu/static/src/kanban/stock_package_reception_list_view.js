/** @odoo-module */

import { registry } from "@web/core/registry"
import { kanbanView } from "@web/views/kanban/kanban_view"
import { KanbanController } from "@web/views/kanban/kanban_controller"

class ProductProductCreateKanbanController extends KanbanController {
    addProduct() {
        this.actionService.doAction('product_menu.action_add_products_wizard')
    }
}

export const productMenuKanbanView = Object.assign({}, kanbanView, {
    Controller: ProductProductCreateKanbanController,
    buttonTemplate: "product_menu.ProductMenuKanbanView.Buttons"
})

registry.category("views").add("product_menu_kanban_view", productMenuKanbanView)
