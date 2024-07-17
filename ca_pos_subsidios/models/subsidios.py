import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class Subsidios(models.Model):
    _name = "subsidios"
    _description = "Subsidios de compras"

    fecha =  fields.Date(string="Fecha")
    empresa_id = fields.Many2one('res.partner',string="Empresa subsidiaria")
    empleado_id = fields.Many2one('res.partner',string="Empleado subsidiado")
    orden_id= fields.Many2one('pos.order',string="Orden ID")
    sale_orden_id= fields.Many2one('sale.order',string="Orden venta ID")
    porcentaje_subsidiado = fields.Float(string = "Porcentaje subsidiado", store=True)#, readonly=True)
    #El total solo de este subsidio, o sea el monto del subsidio
    monto_subsidiado=fields.Float(string = "Monto subsidiado", store=True)#, readonly=True)

    @api.model
    def get_count_subsidios_por_cliente_fecha(self, cliente_id, fecha):
        return self.env['subsidios'].search_count([("empleado_id", "=", cliente_id), ('fecha', '=', fecha )] )