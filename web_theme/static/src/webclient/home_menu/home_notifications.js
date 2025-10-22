/** @odoo-module **/

import { Transition } from "@web/core/transition";
import { Component, useState, markup } from "@odoo/owl";
import { session } from "@web/session";
import { rpc } from "@web/core/network/rpc";

/**
 * Home Notifications
 *
 * Component representing the notification banner located on top of the home menu.
 * Its purpose is to display notifications for the user.
 * @extends Component
 */
export class HomeNotifications extends Component {
    static template = "HomeNotificationsPanel";
    static props = {};
    static components = { Transition };

    setup() {
        this.notifications = session.home_notifications.map(notification => ({
            ...notification,
            message: markup(notification.message),
            message_style: notification.message_style || 'info'
        })) || [];

        this.state = useState({
            notifications: this.notifications || []
        });
    }

    hasNotifications() {
        return Array.isArray(this.state.notifications) && this.state.notifications.length > 0;
    }

    /**
     * Dismiss a notification for the current user
     * @param {number} notificationId - The ID of the notification to dismiss
     */
    async dismissNotification(notificationId) {
        // Use direct RPC call with our custom server method
        const result = await rpc("/web/dataset/call_kw/home.notifications/dismiss_for_user", {
            model: "home.notifications",
            method: "dismiss_for_user",
            args: [notificationId],
            kwargs: {}
        });

        if (result) window.location.reload();
    }
}