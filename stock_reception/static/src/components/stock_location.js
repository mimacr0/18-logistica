/** @odoo-module */

import { useService } from "@web/core/utils/hooks"

const { Component, useSubEnv } = owl;

export default class LocationComponent extends Component {

    setup(){
        this.rpc = useService('rpc');
        this.orm = useService('orm');
        const model = 'stock.location'
        useSubEnv({model})
        this.model = model
        this.locationList = []

        // onMounted(() => {
        //     bus.on('reload-locations', this, this.reloadLocations)
        // })

        // onWillUnmount(() => {
        //     bus.off('reload-locations', this, this.reloadLocations)
        // })

    }

    async reloadLocations() {
        const partnerId = document.querySelector('#form-partner-id')
        const cids = await this.orm.searchRead('contract.pro', [['partner_id', '=', parseInt(partnerId.value)]], ["location_id"])
        const lids = cids.length > 0 ? cids[0].location_id : []
        const data = await this.orm.searchRead('stock.location', [['id', 'in', lids]], ["name"])
        this.locationList = data
        this.render(true)
    }

}

LocationComponent.template = "stock_reception.LocationComponent"