/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.rpc = rpc;
        this.action = useService("action");
        this.ui = useService("ui");
        
        // Cache para saber si es sesión SSO (evita llamadas repetidas)
        this._isSsoSession = null;
        this._setupHomeMenuInterceptor();
    },

    /**
     * Configura interceptor para el botón de home menu
     */
    _setupHomeMenuInterceptor() {
        // Usar setTimeout para asegurar que el DOM está listo
        setTimeout(() => {
            const menuToggle = document.querySelector('.o_menu_toggle');
            if (menuToggle) {
                menuToggle.addEventListener('click', async (ev) => {
                    console.log(menuToggle)
                    const isMobile = this.ui.isSmall;
                    if (!isMobile){
                        const handled = await this._handleSsoRedirect();
                        if (handled) {
                            ev.preventDefault();
                            ev.stopPropagation();
                        }
                    }
                }, true); // Capture phase para interceptar primero
            }
        }, 500);
    },

    onAllAppsBtnClick() {
        console.log("onAllAppsBtnClick")
        super.onAllAppsBtnClick();
        const isMobile = this.ui.isSmall;
        if (isMobile){
            this._handleSsoRedirect();
        }
        this._closeAppMenuSidebar();
    },

     /**
     * Intercepta el menú de inicio en móvil (sidebar)
     */
    // async _openAppMenuSidebar() {
    //     console.log("_openAppMenuSidebar")
    //     const handled = await this._handleSsoRedirect();
    //     if (handled) return;
    //     super._openAppMenuSidebar(...arguments);
    // },

    /**
     * Intercepta cuando el usuario hace clic en un menú del dropdown (desktop)
     */
    // async onNavBarDropdownItemSelection(menu) {
    //      console.log("onNavBarDropdownItemSelection")
    //     const handled = await this._handleSsoRedirect();
    //     if (handled) return;
    //     super.onNavBarDropdownItemSelection(menu);
    // },

    /**
     * Intercepta clic en submenús
     */
    // async _onMenuClicked(menu) {
    //      console.log("_onMenuClicked")
    //     const handled = await this._handleSsoRedirect();
    //     if (handled) return;
    //     super._onMenuClicked(menu);
    // },

     /**
     * Maneja la redirección SSO si aplica
     */
    async _handleSsoRedirect() {
        const ssoCheck = await this._checkIsSsoSession();

        if (ssoCheck.is_sso) {
            const ssoAction = await this._getSsoAction();
            console.log(ssoAction)
            if (ssoAction && ssoAction.type === 'ir.actions.act_url') {
                await this.action.doAction(ssoAction);
                return true;
            }
        }
        return false;
    },

    /**
     * Verifica si la sesión actual fue iniciada por SSO
     * 
     * @returns {Object} {is_sso: bool, employee_id: int or null}
     */
    async _checkIsSsoSession() {
        // Usar cache si ya se verificó
        if (this._isSsoSession !== null) {
            return this._isSsoSession;
        }
        
        try {
            const result = await this.rpc("/sso/is_sso_session", {});
            this._isSsoSession = result || { is_sso: false, employee_id: null };
            return this._isSsoSession;
        } catch (error) {
            console.error("Error checking SSO session:", error);
            return { is_sso: false, employee_id: null };
        }
    },

    /**
     * Obtiene la acción a ejecutar para usuarios SSO
     * 
     * @returns {Object} {is_sso: bool, action: Object or null}
     */
    async _getSsoAction() {
        try {
            const result = await this.rpc("/sso/get_action", {});
            return result || { is_sso: false, action: null };
        } catch (error) {
            console.error("Error getting SSO action:", error);
            return { is_sso: false, action: null };
        }
    },
});

