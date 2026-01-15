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
        this._ssoAction = null;  // Cache de la acción SSO

        // Pre-cargar info SSO al inicio
        this._preloadSsoInfo();
    },

    /**
     * Pre-carga la info SSO y configura los interceptores cuando esté lista
     */
    async _preloadSsoInfo() {
        try {
            await this._checkIsSsoSession();
            if (this._isSsoSession?.is_sso) {
                this._ssoAction = await this._getSsoAction();
                console.log("SSO preloaded:", this._ssoAction);

                if (this.ui.isSmall) {
                    // MÓVIL: interceptar solo el botón "All Apps" dentro del sidebar
                    this._setupAllAppsButtonInterceptor();
                } else {
                    // DESKTOP: interceptar el botón de apps del navbar
                    this._setupDesktopAppsMenuInterceptor();
                }
            }
        } catch (error) {
            console.error("Error preloading SSO:", error);
        }
    },

    /**
     * MÓVIL: Configura interceptor para el botón "All Apps" dentro del sidebar
     * Usa event delegation para capturar clicks en elementos dinámicos
     */
    _setupAllAppsButtonInterceptor() {
        // Event listener delegado en el body (capture phase)
        document.body.addEventListener('click', (ev) => {
            // Verificar si el click fue en el botón "All Apps" dentro del sidebar
            const allAppsBtn = ev.target.closest('.o_sidebar_topbar a.btn-primary, .o_sidebar_topbar .btn-primary');

            if (allAppsBtn && this._isSsoSession?.is_sso && this._ssoAction?.url) {
                console.log("SSO Móvil: Click en 'All Apps' interceptado, redirigiendo...");
                ev.preventDefault();
                ev.stopPropagation();
                ev.stopImmediatePropagation();

                // Cerrar el sidebar antes de redirigir
                this._closeAppMenuSidebar();

                // Redirigir
                window.location.href = this._ssoAction.url;
                return false;
            }
        }, true); // Capture phase

        console.log("Móvil: All Apps button interceptor configured");
    },

    /**
     * DESKTOP: Configura interceptor para el botón de apps en el navbar
     */
    _setupDesktopAppsMenuInterceptor() {
        setTimeout(() => {
            // El botón de apps en desktop tiene el icono oi-apps y está en o_navbar_apps_menu
            // const appsMenuBtn = document.querySelector('.o_navbar_apps_menu button, .o_navbar_apps_menu .dropdown-toggle');
            const appsMenuBtn = document.querySelector('.o_menu_toggle');

            if (appsMenuBtn && !appsMenuBtn.dataset.ssoIntercepted) {
                appsMenuBtn.dataset.ssoIntercepted = 'true';

                appsMenuBtn.addEventListener('click', (ev) => {
                    if (this._isSsoSession?.is_sso && this._ssoAction?.url) {
                        console.log("SSO Desktop: Click en menú de apps interceptado, redirigiendo...");
                        ev.preventDefault();
                        ev.stopPropagation();
                        ev.stopImmediatePropagation();
                        window.location.href = this._ssoAction.url;
                        return false;
                    }
                }, true); // Capture phase

                console.log("Desktop: Apps menu interceptor configured");
            }
        }, 200);
    },

    onAllAppsBtnClick() {
        console.log("onAllAppsBtnClick");

        // Verificación SÍNCRONA - si es SSO, redirigir sin abrir menú
        if (this._isSsoSession?.is_sso && this._ssoAction?.url) {
            console.log("SSO: Redirigiendo desde onAllAppsBtnClick...");
            this._closeAppMenuSidebar();
            window.location.href = this._ssoAction.url;
            return;  // NO llamar a super
        }

        // Si no es SSO, comportamiento normal
        super.onAllAppsBtnClick();
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

