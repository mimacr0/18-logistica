/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { HomeNotifications } from "./home_notifications";

import { Component, xml, useState } from "@odoo/owl";

export class SubscriptionManager {
    constructor(env, { orm, notification }) {
        this.env = env;
        this.orm = orm;
        this.notification = notification;

        // Get notifications from session
        this.homeNotifications = Array.isArray(session.home_notifications) ? session.home_notifications : [];

        // Check if we have notifications
        this.hasNotifications = this.homeNotifications.length > 0;

        // Log for debugging purposes
        console.log("Notifications info:", {
            hasNotifications: this.hasNotifications,
            homeNotifications: this.homeNotifications,
        });
    }
}

class NotificationsBlockUI extends Component {
    static props = {};

    static template = xml`
        <t t-if="false">
            <!-- We've moved all notification functionality to the home menu component -->
        </t>`;
    static components = { HomeNotifications };
    setup() {
        this.subscription = useState(useService("theme_subscription"));
    }
}

function start(env, { orm, notification }) {
    const subscriptionManager = new SubscriptionManager(env, { orm, notification });
    return subscriptionManager;
}

registry.category("services").add("theme_subscription", { start });
registry.category("main_components").add("NotificationsBlockUI", {
    Component: NotificationsBlockUI,
    props: {},
});
