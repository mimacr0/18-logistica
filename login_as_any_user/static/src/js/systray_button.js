/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component } = owl;
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class UserSwitchWidget extends Component {
    setup() {
        super.setup();
        this.action = useService("action");
        // Eliminamos la línea que causa el error
        this.isAdmin = false;
        this._checkAdminRights();
    }

    async _checkAdminRights() {
        try {
            // Primero obtenemos la información de la sesión para conocer el ID del usuario actual
            const session = await rpc("/web/session/get_session_info", {});

            // Luego hacemos la llamada con el ID del usuario como primer argumento
            const result = await rpc("/web/dataset/call_kw/res.users/has_group", {
                model: "res.users",
                method: "has_group",
                args: [session.uid], // Pasamos el ID del usuario actual
                kwargs: {
                    group_ext_id: "base.group_system"
                }
            });

            this.isAdmin = result;
            this.render();
        } catch (error) {
            console.error("Error al verificar permisos de administrador:", error);
            this.isAdmin = false;
            this.render();
        }
    }

    async _onClick(){
        var result = await rpc("/switch/user", {});
            if (result == true) {
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: _t('Switch User'),
                    res_model: 'user.selection',
                    view_mode: 'form',
                    views: [
                        [false, 'form']
                    ],
                    target: 'new'
                })
            }else{
                rpc("/switch/admin", {}).then(function(){
                    location.reload();
                })
            }
    }
}
UserSwitchWidget.props = {};
UserSwitchWidget.template = "UserSwitchSystray";
const Systray = {
    Component: UserSwitchWidget
}
registry.category("systray").add("UserSwitchSystray", Systray)