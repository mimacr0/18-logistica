/** @odoo-module */

import StockQuantPackageModel from '@stock_reception/models/package_model';
import { registry } from "@web/core/registry"
import { View } from "@web/views/view"
import { useService } from "@web/core/utils/hooks"
import { _t } from "@web/core/l10n/translation"
import LocationComponent from '@stock_reception/components/stock_location';
import { rpc } from "@web/core/network/rpc";

const { Component, onWillStart, useSubEnv } = owl;

export class ReceivePackage extends Component {
    setup() {
        // Acceso a servicios
        this.rpc =rpc;
        this.orm = useService('orm');
        this.notification = useService('notification');

        // Configuración de propiedades
        this.props.model = this.props.action.context.model;
        this.props.id = this.props.action.context.wizard_id;

        // Crear una instancia del modelo
        this.stockModel = new StockQuantPackageModel(this.props, { rpc: this.rpc, orm: this.orm });

        // Usar un entorno de subcomponentes
        useSubEnv({ model: this.stockModel });

        // Comportamiento de desplazamiento
        this._scrollBehavior = 'smooth';

        // Inicializar datos
        this.modelData = {};
        
        // Cargar datos al inicio
        onWillStart(async () => {
            try {
                const modelData = await this.rpc('/stock/reception/get/model/data', {
                    model: this.props.model,
                    res_id: this.props.id || false
                });
                this.modelData = modelData;
            } catch (error) {
                console.error("Error al cargar datos:", error);
            }
        });
    }

    // Otros métodos y renderizado del componente

    addPackageImages() {
        const imgInput = document.querySelector('#reception-package-images')
        imgInput.click()
    }

    async saveFormView(record) {

        this.notification.add(
            _t('Reception Confirmed'),
            {
                title: 'Success',
                type: 'success'
            }
        )

    }

    get info() {
        if(this.props.model == 'receive.package.wizard') return {
            icon: 'archive',
            message: _t('Package reception')
        }

        return this.env.model.info || {}
    }

    async exit(ev) {
        this.env.config.historyBack()
        if(this.MainBar) this.MainBar.classList.remove('o_hidden')
    }

}

ReceivePackage.template = "stock_reception.ReceivePackage"
ReceivePackage.components = {
    View,
    LocationComponent
}

registry.category("actions").add("stock_reception.ReceivePackage", ReceivePackage)