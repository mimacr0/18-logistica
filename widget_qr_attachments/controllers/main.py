# -*- coding: utf-8 -*-
import base64
import json
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessDenied
from werkzeug.exceptions import NotFound


class QRUploadController(http.Controller):

    def _get_record_sudo(self, model, res_id, token=None):
        """Validate access and return the record with sudo.
        Access is granted if:
        - The user is an authenticated internal user, OR
        - A valid access_token is provided (via qr.access.token model)
        """
        record = request.env[model].sudo().browse(res_id)
        if not record.exists():
            raise NotFound()

        # If user is authenticated and internal, allow access without token
        uid = request.env.uid
        user = request.env['res.users'].sudo().browse(uid)
        if user and user.has_group('base.group_user'):
            return record

        # For public users, require a valid token
        if not token:
            raise AccessDenied(_("Access token is required."))
        is_valid = request.env['qr.access.token'].sudo().validate_token(model, res_id, token)
        if not is_valid:
            raise AccessDenied(_("Invalid access token."))
        return record

    def _link_attachment_to_record(self, record, attachment):
        """Auto-link an attachment to any Many2many ir.attachment fields on the record."""
        try:
            model_fields = record._fields
            for field_name, field in model_fields.items():
                if (field.type == 'many2many'
                        and field.comodel_name == 'ir.attachment'):
                    record.sudo().write({
                        field_name: [(4, attachment.id)]
                    })
        except Exception:
            pass  # Non-critical: attachment is still linked via res_model/res_id

    @http.route('/qr_upload/<string:model>/<int:res_id>', type='http', auth='public', website=False, sitemap=False)
    def qr_upload_page(self, model, res_id, token=None, **kwargs):
        """Renders the mobile upload interface (public with token)."""
        try:
            record = self._get_record_sudo(model, res_id, token)
        except (AccessDenied, NotFound):
            return request.not_found()

        values = {
            'model': model,
            'res_id': res_id,
            'record_name': record.display_name,
            'token': token or '',
        }
        return request.render('widget_qr_attachments.upload_mobile_template', values)

    @http.route('/qr_upload/get_attachments', type='json', auth='public', csrf=False)
    def get_attachments(self, model, res_id, token=None):
        """Returns a list of attachments for the record."""
        self._get_record_sudo(model, res_id, token)

        attachments = request.env['ir.attachment'].sudo().search_read([
            ('res_model', '=', model),
            ('res_id', '=', res_id),
        ], ['id', 'name', 'mimetype', 'checksum'])

        for attachment in attachments:
            attachment['url'] = f'/web/content/{attachment["id"]}'
            if attachment['mimetype'].startswith('image/'):
                attachment['is_image'] = True
                attachment['thumbnail_url'] = f'/web/image/{attachment["id"]}/100x100'
            else:
                attachment['is_image'] = False

        return attachments

    @http.route('/qr_upload/upload_file', type='json', auth='public', csrf=False)
    def upload_file(self, model, res_id, name, content, mimetype, token=None):
        """Uploads a file and attaches it to the record."""
        record = self._get_record_sudo(model, res_id, token)

        try:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': name,
                'type': 'binary',
                'datas': content,
                'res_model': model,
                'res_id': res_id,
                'mimetype': mimetype,
                'public': True,
            })
            # Auto-link to Many2many ir.attachment fields on the record
            self._link_attachment_to_record(record, attachment)
            return {
                'id': attachment.id,
                'name': attachment.name,
                'success': True
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/qr_upload/delete_attachment', type='json', auth='public', csrf=False)
    def delete_attachment(self, attachment_id, token=None, model=None, res_id=None):
        """Deletes an attachment."""
        if model and res_id:
            self._get_record_sudo(model, res_id, token)

        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        if attachment.exists():
            # Verify the attachment belongs to the validated record
            if model and res_id:
                if attachment.res_model != model or attachment.res_id != res_id:
                    raise AccessDenied(_("Attachment does not belong to this record."))
            attachment.unlink()
            return {'success': True}
        return {'success': False, 'error': 'Attachment not found'}
