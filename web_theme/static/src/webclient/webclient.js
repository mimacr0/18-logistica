/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { useService } from "@web/core/utils/hooks";
import { ThemeNavBar } from "./navbar/navbar";

export class WebClientTheme extends WebClient {
    static components = {
        ...WebClient.components,
        NavBar: ThemeNavBar,
    };
    setup() {
        super.setup();
        this.hm = useService("home_menu");
    }
    _loadDefaultApp() {
        return this.hm.toggle(true);
    }
}
