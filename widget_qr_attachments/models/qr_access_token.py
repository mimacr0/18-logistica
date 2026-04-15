# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api


class QrAccessToken(models.Model):
    _name = 'qr.access.token'
    _description = 'QR Upload Access Token'
    _rec_name = 'token'

    model_name = fields.Char(string='Model', required=True, index=True)
    res_id = fields.Integer(string='Record ID', required=True, index=True)
    token = fields.Char(string='Token', required=True, default=lambda self: str(uuid.uuid4()), readonly=True)

    _sql_constraints = [
        ('model_res_id_uniq', 'unique(model_name, res_id)', 'Only one token per record is allowed.'),
    ]

    @api.model
    def get_or_create_token(self, model_name, res_id):
        """Get existing token or create a new one for the given model/record.
        This is called by the QR widget to generate the upload URL."""
        existing = self.sudo().search([
            ('model_name', '=', model_name),
            ('res_id', '=', res_id),
        ], limit=1)
        if existing:
            return existing.token
        new_token = self.sudo().create({
            'model_name': model_name,
            'res_id': res_id,
        })
        return new_token.token

    @api.model
    def validate_token(self, model_name, res_id, token):
        """Validate a token for the given model/record.
        Returns True if valid, raises AccessDenied otherwise."""
        if not token:
            return False
        existing = self.sudo().search([
            ('model_name', '=', model_name),
            ('res_id', '=', res_id),
            ('token', '=', token),
        ], limit=1)
        return bool(existing)

    @api.model
    def regenerate_token(self, model_name, res_id):
        """Delete the existing token and create a new one.
        Returns the new token string.
        Usage: self.env['qr.access.token'].regenerate_token('my.model', record_id)
        """
        existing = self.sudo().search([
            ('model_name', '=', model_name),
            ('res_id', '=', res_id),
        ], limit=1)
        if existing:
            existing.unlink()
        new_token = self.sudo().create({
            'model_name': model_name,
            'res_id': res_id,
        })
        return new_token.token
