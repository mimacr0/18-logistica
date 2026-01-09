# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect


class SsoController(http.Controller):

    @http.route('/sso/verify', type='http', auth='public', csrf=False)
    def sso_verify(self, credential=None):
        res = True
        msg = ''
        # Buscar empleado por barcode
        employee = request.env['hr.employee'].sudo().search([
            ('barcode', '=', credential)
        ], limit=1)
        if not employee:
            res = False
            msg = 'Empleado no encontrado'
        elif not employee.user_id:
            res = False
            msg = 'Usuario no configurado'

        return json.dumps({'success': res, 'error': msg})

    @http.route('/sso/login', type='http', auth='public', csrf=False)
    def sso_login(self, token=None, domain=None):
        if not token:
            return "Token requerido"

        # Buscar empleado por barcode/token
        employee = request.env['hr.employee'].sudo().search([
            ('barcode', '=', token)
        ], limit=1)
        if not employee or not employee.user_id:
            return "Usuario no existe en este Odoo"

        user = employee.user_id

        # LOGIN MANUAL (Odoo 18)
        request.session.uid = user.id
        request.session.login = user.login
        request.session.session_token = user._compute_session_token(
            request.session.sid
        )

        # ⭐ GUARDAR QUE INGRESÓ POR SSO
        request.session.sso_login = True
        request.session.sso_employee_id = employee.id
        request.session.origin_domain = domain

        # Action de Ausencias
        action = request.env.ref(
            'hr_holidays.hr_leave_action_new_request'
        ).sudo()

        # Redirección
        return redirect(
            f"/web#action={action.id}"
        )

    @http.route('/sso/is_sso_session', type='json', auth='user')
    def is_sso_session(self):
        """
        Verifica si la sesión actual fue iniciada por SSO.
        Llamado desde JavaScript.
        
        Returns:
            dict: {is_sso: bool, employee_id: int or None}
        """
        return {
            'is_sso': getattr(request.session, 'sso_login', False),
            'employee_id': getattr(request.session, 'sso_employee_id', None)
        }

    @http.route('/sso/get_action', type='json', auth='user')
    def get_sso_action(self):
        """
        Obtiene la acción a ejecutar para usuarios SSO.
        
        Returns:
            dict: Acción de Odoo para redirigir
        """
        # Verificar si es sesión SSO
        if not getattr(request.session, 'sso_login', False):
            return {'is_sso': False, 'action': None}

        base_url =  getattr(request.session, 'origin_domain', False)
        return {
            'type': 'ir.actions.act_url',
            'url': f"{base_url}/web",
            'target': 'self'
        }