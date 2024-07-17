# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_porcentaje_subsidio = fields.Float(related='pos_config_id.porcentaje_subsidio', readonly=False)
    pos_producto_factura_id = fields.Many2one('product.product', store=True, readonly=False)
