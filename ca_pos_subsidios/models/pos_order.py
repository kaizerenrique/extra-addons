# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial
from itertools import groupby

import psycopg2
import pytz
import re

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    es_subsidiada = fields.Boolean(string="Es subsidiada", default=False, help="Indica si la orden fue o no subsidiada" )


    '''
    DEVOLUCIONES
    Proceso de creacion
    1. Crear la orden en POS (automatico)
    2. Crear la orden de venta, si aplica (pos.order -> _process_order)
    3. Crear registro en Subsidios, si aplica (pos.order -> _process_order)
    4. Crear la factura de empleado (automático)

    Reversion
    1. Devolucion. Reversa factura y orden (automático)
    2. Cancelar la orden de venta, si existe (en principio se asumirá que no ha sido facturada)
    3. Eliminar o anular el subsidio, si existe

    #"order".account_move es la devolucion
    #"order".account_move.reversed_entry_id la factura original que se esta anulando
    #"order".account_move.reversed_entry_id.pos_order es la orden (del POS) que generó la factura original
    #Como revertir
    #1. 


    '''
    @api.model
    def _process_order(self, order, draft, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param dict order: dictionary representing the order.
        :param bool draft: Indicate that the pos_order is not validated yet.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: id of created/updated pos.order
        :rtype: int
        """
        order = order['data']
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['pos_session_id'] = self._get_valid_session(order).id

        if order.get('partner_id'):
            partner_id = self.env['res.partner'].browse(order['partner_id'])
            if not partner_id.exists():
                order.update({
                    "partner_id": False,
                    "to_invoice": False,
                })
        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))
        else:
            pos_order = existing_order
            pos_order.lines.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        pos_order._link_combo_items(order)
        pos_order = pos_order.with_company(pos_order.company_id)
        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)

        _logger.info("(Spooler)-----------  _process_order  -----------------" )
        _logger.info(  self.is_refunded)
        _logger.info(  pos_order)
        _logger.info(  order)
        _logger.info(  order["amount_paid"])
        _logger.info(  pos_order.amount_paid)
        _logger.info(  pos_order.account_move)
        _logger.info(  pos_order.account_move.reversed_entry_id)
        #_logger.info(  pos_order.account_move.reversed_entry_id.pos_order)


        if pos_order.amount_paid > 0:
            self.procesar_subsidio(pos_order)

        return pos_order._process_saved_order(draft)

    def _process_saved_order(self, draft):
        _logger.info("(Spooler)-----------  _process_saved_order  -----------------" )
        _logger.info(  self.is_refunded)
        res_id = super()._process_saved_order(draft)
        if self.amount_paid < 0:
            rev_mov = self.account_move.reversed_entry_id
            if rev_mov and rev_mov.pos_order_ids[0].es_subsidiada:
                self.revertir_subsidio(rev_mov.pos_order_ids[0])
        _logger.info(  "-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
        _logger.info(  self.amount_paid)
        _logger.info(  self.account_move)
        _logger.info(  self.account_move.reversed_entry_id)
        #_logger.info(  self.account_move.reversed_entry_id.pos_order)

        _logger.info("(Spooler)+++++++++++  _process_saved_order  +++++++++++++++++" )

        return res_id

    def procesar_subsidio(self, order):
        #partner = self.env['res.partner'].search([("id", "=", self.partner_id.id)] )
        partner = order.partner_id
        subsidiaria = order.partner_id.subsidiaria_partner_id

        _logger.info("-----------  procesar_subsidio  -----------------" )
        _logger.info( subsidiaria )

        if (subsidiaria):
            es_subsidiaria = subsidiaria.es_subsidiaria
            subsidio_activo = subsidiaria.subsidio_activo
            _logger.info( es_subsidiaria )
            _logger.info( subsidio_activo )
    
            if es_subsidiaria and subsidio_activo:
                subsi_por_fecha = order.env['subsidios'].search_count([("empleado_id", "=", order.partner_id.id), ('fecha', '=', order.date_order )] )
                porc_subsidio = subsidiaria.porcentaje_subsidio
                prod_facturar = subsidiaria.producto_factura_subsi_id

                _logger.info( subsi_por_fecha )

                if subsi_por_fecha < subsidiaria.max_subsidios_dia:
                    monto_factura = order.total_subsidio(order.lines) * porc_subsidio / 100.0
                    beneficiario = "CI: " + partner.vat if partner.vat else ""
                    beneficiario = prod_facturar.name + ' | ' + partner.name + ' | ' + beneficiario + ' | ' + str(order.date_order)
                    so = order.env['sale.order'].create({
                        'partner_id': subsidiaria.id,
                        'date_order': order.date_order,
                        'state': 'draft',
                        'order_line': [(0, 0, {
                            'name': beneficiario, #prod_facturar.name + ' ' + self.partner_id.name + ' ', 
                            'product_id': prod_facturar.id, 
                            'product_uom_qty': 1, 
                            'price_unit': monto_factura})],
                         })
                    so.action_confirm()

                    order.env['subsidios'].create({
                        'fecha': order.date_order,
                        'empresa_id': subsidiaria.id,
                        'empleado_id': order.partner_id.id,
                        'orden_id': order.id,
                        'porcentaje_subsidiado': porc_subsidio,
                        'monto_subsidiado': monto_factura,
                        'sale_orden_id': so.id,
                         })

                    order.write({'es_subsidiada': True })

                    return so

        return

    def revertir_subsidio(self, order):
        #_action_cancel
        reg_sub = self.env['subsidios'].search([("orden_id", "=", order.id)], limit=1)
        sale_order = request.env['sale.order'].sudo().search([('id', '=', reg_sub.sale_orden_id.id)], limit=1)
        if (sale_order):
            sale_order._action_cancel()
        reg_sub.unlink()
        return

    @api.model
    def get_total_subsidio(self, cliente_id, lines):
        total_subs = 0.0
        partner = request.env['res.partner'].sudo().search([('id', '=', cliente_id['id'])], limit=1)

        for line in lines:
            categ = request.env['product.product'].sudo().search([('id', '=', line[2]['product_id'])], limit=1).categ_id
            if (categ in partner.categorias_permitidas_ids):
                _logger.info("-----------  GET ITEM ITEM ITEM SUBSIDIO GET_total_subsidio  -----------------" )
                _logger.info( line[2]['price_subtotal'] )
                #if self.amount_paid > 0:
                total_subs+= line[2]['price_subtotal']
                #elif self.amount_paid < 0:
                #   total_subs-= line[2]['price_subtotal']
            _logger.info("-  -  -  -  - GET  ITEM ITEM ITEM SUBSIDIO GET total_subsidio  -  -  -  -  -  -  -" )
        return total_subs 

    #self.get_total_subsidio(subsidiaria, self.lines) * porc_subsidio / 100.0
    @api.model
    def total_subsidio(self, lines):
        total_subs = 0.0
        for line in lines:
            if (line.product_id.categ_id in self.partner_id.subsidiaria_partner_id.categorias_permitidas_ids):
                _logger.info("-----------  ITEM ITEM ITEM SUBSIDIO total_subsidio  -----------------" )
                _logger.info( line.price_subtotal )
                #if self.amount_paid > 0:
                total_subs+= line.price_subtotal
                #elif self.amount_paid < 0:
                #    total_subs-= line.price_subtotal
            _logger.info("-  -  -  -  -  ITEM ITEM ITEM SUBSIDIO total_subsidio  -  -  -  -  -  -  -" )

        return total_subs
