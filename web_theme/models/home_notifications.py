# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from datetime import datetime
import json
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval


class HomeNotifications(models.Model):
    _name = 'home.notifications'
    _description = 'Home Screen Notifications'
    _order = 'sequence, id'

    name = fields.Char(string='Title', required=True, translate=True)
    show_title = fields.Boolean(string='Show Title', default=True)
    message_style = fields.Selection(
        selection=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
            ('success', 'Success')
        ],
        default='info',
        string='Message Style',
        required=True,
        help="Style of notification: info (blue), warning (yellow), danger (red), success (green)"
    )
    message = fields.Html(string='Message', sanitize=False, translate=True)
    sequence = fields.Integer(default=10, help="Determine the display order")
    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    active = fields.Boolean(default=True, string='Active')
    user_ids = fields.Many2many('res.users', string='Visible to Users',
                               help='If empty, the notification will be visible to all users')
    group_ids = fields.Many2many('res.groups', string='Visible to Groups',
                                help='If empty, the notification will be visible to all groups')
    dismiss_user_ids = fields.Many2many('res.users', 'home_notification_dismiss_users_rel',
                                     'notification_id', 'user_id',
                                     string='Dismissed by Users',
                                     help='Users who have dismissed this notification', copy=False)

    @api.model
    def get_active_notifications(self):
        """
        Get active notifications for the current user's home screen and
        update the custom_header_message parameter
        """
        current_datetime = fields.Datetime.now()
        domain = [
            ('start_date', '<=', current_datetime),
            ('end_date', '>=', current_datetime)
        ]

        # Get all active notifications within the date range
        notifications = self.search(domain, order='sequence, id')

        # Filter for user and group access
        filtered_notifications = self.env['home.notifications']
        for notification in notifications:
            # If specific users are set, check if current user is in the list
            if notification.user_ids and self.env.user.id not in notification.user_ids.ids:
                continue

            # If specific groups are set, check if user belongs to any of them
            if notification.group_ids and not any(group.id in self.env.user.groups_id.ids for group in notification.group_ids):
                continue

            # Skip if user has dismissed this notification
            if self.env.user.id in notification.dismiss_user_ids.ids:
                continue

            filtered_notifications += notification

        messages = []

        # Format the notifications as HTML content - avoid string concatenation
        if filtered_notifications:
            # Create a proper HTML structure using Markup to ensure it's not escaped
            messages = []
            for notification in filtered_notifications:
                messages.append({
                    'id': notification.id,
                    'name': notification.name,
                    'show_title': notification.show_title,
                    'message_style': notification.message_style or 'info',
                    'message': notification.message,
                    'start_date': notification.start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_date': notification.end_date.strftime('%Y-%m-%d %H:%M:%S')
                })

        return messages

    @api.model
    def dismiss_for_user(self, notification_id):
        """
        Dismiss a notification for the current user

        :param notification_id: ID of the notification to dismiss
        :return: True if successful
        """
        if not self.env.user or not self.env.user.id:
            return False

        notification = self.sudo().browse(notification_id)
        if not notification.exists():
            return False

        # Add current user to dismiss_user_ids using sudo to bypass potential access rights issues
        notification.sudo().write({
            'dismiss_user_ids': [(4, self.env.user.id)]
        })

        return True
