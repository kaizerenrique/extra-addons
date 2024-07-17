# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import OR


class PosConfig(models.Model):
    _inherit = 'pos.config'

    porcentaje_subsidio = fields.Float(string='Porcentaje de subsidio', help='Porcentaje de subsidio', default=80.0)
    producto_factura_id = fields.Many2one('product.product', string="Producto a facturar", help='Producto a facturar a la empresa')

    def _get_special_products(self):
        res = super()._get_special_products()
        return res | self.env['pos.config'].search([]).mapped('producto_factura_id')

    #def _get_available_product_domain(self):
    #    domain = super()._get_available_product_domain()
    #    return OR([domain, [('id', '=', self.producto_factura_id.id)]])