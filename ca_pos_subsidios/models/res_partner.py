from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"
    #_sql_constraints = [('porcentaje_valido', 'CHECK(porcentaje_subsidio >= 0  AND  porcentaje_subsidio <= 100)', "El subsidio debe estar entre 0 y 100%")]

    es_subsidiaria = fields.Boolean(string="Es subsidiaria?", help="Indica si la empresa subsidia a trabajadores" )
    subsidiaria_partner_id = fields.Many2one(
        'res.partner',
        string="Subsidiaria",
        help='Empresa subsidiaria',
        domain=['&', ('es_subsidiaria', '=', True), ('is_company', '=', True)],
        store=True,
        ondelete='restrict')
    porcentaje_subsidio = fields.Float(string="Porcentaje", default=80, help="Porcentaje de subsidio")
    subsidio_activo = fields.Boolean(string="Activa?", default=True, help="Activa/desactiva el subsidio" )
    max_subsidios_dia = fields.Integer(string="Subsidios diarios", default=1,help="Cantidad maxima de subsidios diarios por persona")
    producto_factura_id = fields.Many2one('product.product', string="Producto Subsidio", help='Producto para descuento en el Punto de Venta')
    producto_factura_subsi_id = fields.Many2one('product.product', string="Producto a facturar", help='Producto a facturar a la empresa subsidiaria')
    categorias_permitidas_ids = fields.Many2many('product.category', string="Categorias permitidas", help='Categorias de producto que puede subsidiarse')

    @api.constrains('porcentaje_valido')
    def _validate_porcentaje_valido(self):
        if (self.porcentaje_subsidio < 0) or (self.porcentaje_subsidio > 100):
            raise ValidationError("El subsidio debe estar entre 0 y 100%")

    @api.model
    def get_max_subsidios(self, id):
        partner_temp = self.env['res.partner'].search([("id", "=", id)] )

        return partner_temp.max_subsidios_dia if partner_temp else 0
