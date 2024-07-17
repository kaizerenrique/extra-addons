# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def _loader_params_res_partner(self):
        vals = super()._loader_params_res_partner()
        vals['search_params']['fields'] += ['es_subsidiaria', 'subsidiaria_partner_id', 'porcentaje_subsidio','producto_factura_id','subsidio_activo']
        return vals