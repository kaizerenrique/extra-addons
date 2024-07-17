# -*- coding: utf-8 -*-
from odoo import models, fields

class IAsistenteFiscal(models.Model):
    _name = 'iasistente.fiscal'
    _description = 'Interfaz Asistente Fiscal Super Spooler'

    nombre_empesa =fields.Char('Empresa', required=True, index=False)
    carpeta_facturas = fields.Char('Carpeta', required=False, index=False)
    notas = fields.Text('Notas internas')
