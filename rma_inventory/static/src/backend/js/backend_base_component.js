/** @odoo-module */
import { onMounted, useRef, useState} from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    setup() {
        super.setup()
        this._search_def = this.createDeferred();
        })
    },
    return deferred;
},
    async fetch_data() {
        this.orm = useService("orm")
        if (result.primary_accent !== false){
            document.documentElement.style.setProperty("--primary-accent",result.primary_accent)
        }
        if (result.appbar_color !== false){
            document.documentElement.style.setProperty("--app-bar-accent",result.appbar_color)
        }
    },
})
