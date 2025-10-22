/** @odoo-module */

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";

/**
 * Remove "My Odoo.com account" menu item from the user menu
 */
registry.category("user_menuitems").remove("odoo_account");