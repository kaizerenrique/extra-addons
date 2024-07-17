# -*- coding: utf-8 -*-

from odoo import fields, models, api
import json
import re
from csv import DictReader
import os

import logging
_logger = logging.getLogger(__name__)


#Constantes de nombres internos de formas de pago spooler
SP_EFECTIVO = 'efectivo'
SP_EFECTIVO_USD = 'efectivo_usd'
SP_EFECTIVO_EURO = 'efectivo_euro'
SP_BANCO = 'cheques'
SP_TARJETA_DEBITO = 'tarj_debito'
SP_TARJETA_CREDITO = 'tarj_credito'
SP_TRANSFERENCIA_BS = 'trans_bs'
SP_TRANSFERENCIA_USD = 'trans_usd'
SP_TRANSFERENCIA_EURO = 'trans_euro'
SP_ZELLE = 'zelle'
SP_PAGO_MOVIL = 'pago_movil'
SP_CREDITO = 'credito'
POR_IVA = 0.16
FACTOR_IVA = 1.16

class FormasPagoSpooler(models.Model):
    _name = 'formaspago.spooler'
    _description = 'Relacion de formas de pago Spooler y Odoo'

    fp_spooler =fields.Char('fp_spooler', required=True, index=False)
    fp_odoo =fields.Char('fp_odoo', required=True, index=False)


def extraer_documento(invoi):
    if invoi.move_type != 'out_invoice' and invoi.move_type != 'out_refund':
        dfc = {}
    else:
        ditems, descuento = crear_items(invoi) #Obtiene los items de la factura (lines)
        pitems = extraer_pagos(invoi)            #Obtiene los pagos
        #list_fpx = cargar_formas_pago(invoi)          #Carga la relacion de formas de pago spooler->Odoo

        #Elimina caracteres especiales del numero de factura y solo toma los digitos finales
        #Es posible que se repitan numeros el siguiente año. Puede resolverse concatenando año + numero
        numerosf = re.findall(r'\d+', invoi.name )
        numfactura = numerosf[len( numerosf ) -1 ]

        #Obtiene el documento para casos de devoluciones/NC
        referencia = generar_referencia(invoi)

        dfc = crear_campos(invoi, numfactura, ditems, pitems, referencia)

        #Temporal por problemas con las formas de pago de las NC
        if (invoi.move_type == 'out_refund'):
            dfc['banco'] = {'monto': invoi.amount_total}

    return dfc


def crear_items(invoi):
    pos = 0
    ditems = {}
    descuento = 0.0
    for item_fact in invoi.invoice_line_ids:
        ditems[pos] = {
            'descripcion': item_fact.product_id.description_sale if item_fact.product_id.description_sale else item_fact.product_id.name, 
            'codigoprod': item_fact.product_id.product_tmpl_id.id,
            'cantidad': item_fact.quantity, 
            'iva': item_fact.tax_ids[0].amount if item_fact.tax_ids else 0.0, 
            'precio':  item_fact.price_subtotal/item_fact.quantity if item_fact.quantity != 0 else 0.0, 
            'descuento': item_fact.discount }

        #Asegura que si la cantidad es cero(0.0), el renglon completo tenga todo en cero. Remueve calculos erroneos
        if (ditems[pos]['cantidad'] == 0.0):
            ditems[pos]['descuento'] = ditems[pos]['iva'] = ditems[pos]['precio'] = 0.0

        descuento = descuento + item_fact.discount * (item_fact.price_unit * item_fact.quantity)/100
        pos += 1

    return ditems, descuento


def extraer_pagos(invoi):
    pitems = {}

    #NOTA: los pagos de las NC no se estan tomando, por eso todos se ponen en Banco, por ahora
    #      ver extraer_documento al final
    #Solucions posibles:
    # - account.move -> payment_ids     --  one2many a account.payment, con move_id
    # - account.move -> pos_payment_ids --  one2many a pos.payment, con account_move_id
    #Obtiene los items de pagos. Considera el origen y tipo de documento: desde POS o Facturacion, Factura o NC
    #
    #Pruebas. Resultado: no hay info clara
    '''
    payments = invoi['pos_payment_ids'].search([]) 
    _logger.info("(Spooler)-----------  extraer_pagos  -----------------" )
    _logger.info( payments )
    for payment in payments:
        _logger.info( payment )
        _logger.info( payment.name )

    _logger.info("(Spooler)-----------  ++++++++++++++  -----------------" )

    payments = invoi['payment_ids'].search([]) 
    _logger.info( payments )
    for payment in payments:
        _logger.info( payment )
        _logger.info( payment.name )
        _logger.info( payment.payment_method_id )
        _logger.info( payment.journal_id )

    _logger.info("(Spooler)-----------  extraer_pagos  -----------------" )
    '''

    currency_rate = invoi.env['res.currency'].search([('name', '=', 'VEF')], limit=1).rate
    if (invoi.move_type == 'out_invoice' or invoi.move_type == 'out_refund'):
        if (len(invoi.pos_order_ids) > 0) and (invoi.move_type != 'out_refund'):   #Factura originada en el POS no-devolucion
            for item_pago in invoi.pos_order_ids[0].payment_ids:
                clave = item_pago.payment_method_id.display_name
                if clave in pitems:
                    pitems[clave]["monto"] += item_pago.amount
                else:
                    pitems[clave] = {'monto': item_pago.amount }
        elif (invoi.move_type != 'out_refund') and invoi.invoice_payments_widget: #Factura originada por backend/Facturacion
            if type (invoi.invoice_payments_widget) is dict:
                midata = invoi.invoice_payments_widget
            else:
                midata = json.loads(invoi.invoice_payments_widget)

            if midata:
                for item_pago in midata['content']:
                    pitems[item_pago["journal_name"]] = {'monto': item_pago["amount"] }

    return pitems


def obtener_montos_fp(pitems, invoi):
    mt_efectivo = {'monto': 0.0}
    mt_banco = {'monto': 0.0}
    mt_tdebito = {'monto': 0.0}
    mt_tcredito = {'monto': 0.0}
    mt_trans_bs = {'monto': 0.0}
    mt_trans_usd = {'monto': 0.0}
    mt_zelle = {'monto': 0.0}
    mt_trans_euro = {'monto': 0.0}
    mt_efectivo_usd = {'monto': 0.0}
    mt_efectivo_euro = {'monto': 0.0}
    mt_pago_movil = {'monto': 0.0}
    mt_credito = {'monto': 0.0}

    currency_rate = invoi.env['res.currency'].search([('name', '=', 'VEF')], limit=1).rate
    for fpago in pitems:
        fpx = invoi.env['formaspago.spooler'].search([('fp_odoo', '=', fpago)], limit=1)
        pago_bs = 0.0
        iva_bs = 0.0

        #tot_efectivo = round ( (doc['efectivo']['monto']/1.16 * factor_moneda ) , 2)
        #tot_efectivo = round (tot_efectivo + tot_efectivo * 0.16, 2)
        #POR_IVA FACTOR_IVA

        #Contenedor. spooler.py
        #tot_efectivo = round ( (doc['efectivo']['monto']/1.16 ) , 2)
        #tot_efectivo = round(tot_efectivo * factor_moneda, 2)
        #tot_iva = round( tot_efectivo * 0.16, 2)
        #tot_efectivo = tot_efectivo + tot_iva
        #....
        #f.write ( "EFECTIVO: {:>10.2f}".format( tot_efectivo ) + "\n" )
        pago_bs = pitems.get( fpx["fp_odoo"] )["monto"]/FACTOR_IVA
        pago_bs = pago_bs * currency_rate
        iva_bs  =  pago_bs * POR_IVA
        pago_bs = pago_bs + iva_bs

        if fpx:
            if fpx["fp_spooler"] == SP_EFECTIVO:
                mt_efectivo ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_BANCO:
                mt_banco["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_TARJETA_DEBITO:
                mt_tdebito["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_TARJETA_CREDITO:
                mt_tcredito["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_TRANSFERENCIA_BS:
                mt_trans_bs ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_TRANSFERENCIA_USD:
                mt_trans_usd["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_ZELLE:
                mt_zelle ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_TRANSFERENCIA_EURO:
                mt_trans_euro ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_EFECTIVO_USD:
                mt_efectivo_usd ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_EFECTIVO_EURO:
                mt_efectivo_euro ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_PAGO_MOVIL:
                mt_pago_movil ["monto"] += pago_bs
            elif fpx["fp_spooler"] == SP_CREDITO:
                mt_credito ["monto"] += pago_bs
        '''
        if fpx:
            if fpx["fp_spooler"] == SP_EFECTIVO:
                mt_efectivo ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_BANCO:
                mt_banco["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_TARJETA_DEBITO:
                mt_tdebito["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_TARJETA_CREDITO:
                mt_tcredito["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_TRANSFERENCIA_BS:
                mt_trans_bs ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_TRANSFERENCIA_USD:
                mt_trans_usd["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_ZELLE:
                mt_zelle ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_TRANSFERENCIA_EURO:
                mt_trans_euro ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_EFECTIVO_USD:
                mt_efectivo_usd ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_EFECTIVO_EURO:
                mt_efectivo_euro ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_PAGO_MOVIL:
                mt_pago_movil ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            elif fpx["fp_spooler"] == SP_CREDITO:
                mt_credito ["monto"] += pitems.get( fpx["fp_odoo"] )["monto"]
            '''

    return mt_efectivo, mt_banco, mt_tdebito, mt_tcredito, mt_trans_bs, mt_trans_usd, mt_zelle, mt_trans_euro, mt_efectivo_usd, mt_efectivo_euro, mt_pago_movil, mt_credito


def generar_referencia(invoi):
    if invoi.move_type == 'out_refund':
        if invoi.reversed_entry_id.name:
            referencia = invoi.reversed_entry_id.name
        else:
            refs = invoi.env['account.move'].search([('ref', '=', invoi.ref.replace("REEMBOLSO", "")), ('move_type', '=', 'out_invoice')], limit=1)
            referencia = refs.name if refs.name else ""
    else:
        referencia = ""

    if referencia != "":
        ref_tmp = re.findall(r'\d+', referencia )
        referencia = ref_tmp[len( ref_tmp ) -1 ]

    return referencia


def crear_campos(invoi, numfactura, ditems, pitems, referencia):
    dfc = {}

    mt_efectivo, mt_banco, mt_tdebito, mt_tcredito, mt_trans_bs, mt_trans_usd, mt_zelle, mt_trans_euro, mt_efectivo_usd, mt_efectivo_euro, mt_pago_movil, mt_credito = obtener_montos_fp(pitems, invoi)

    #if ( invoi.amount_untaxed != invoi.amount_total):
    #    monto_total = invoi.amount_untaxed * 1.16

    dfc = {
    'tipodoc': 'fac' if invoi.move_type == 'out_invoice' else 'nc' if invoi.move_type == 'out_refund' else '*',
    'numero': numfactura,
    'fecha': invoi.date.strftime("%d/%m/%Y"),
    'cliente': str(invoi.partner_id.name),
    'rif':  str(invoi.partner_id.vat) if invoi.partner_id.vat else "",
    'dir1': str(invoi.partner_id.street) if invoi.partner_id.street else "",
    'dir2': str(invoi.partner_id.street2) if invoi.partner_id.street2 else "",
    'telefono': str(invoi.partner_id.phone) if invoi.partner_id.phone else "",
    'productos': ditems,
    'pagos': pitems,
    'efectivo': mt_efectivo,
    'banco': mt_banco,
    'tarj_debito': mt_tdebito, 
    'tarj_credito': mt_tcredito,
    'trans_bs': mt_trans_bs,
    'zelle': mt_zelle,
    'trans_euro': mt_trans_euro,
    'trans_usd': mt_trans_usd,
    'efectivo_usd': mt_efectivo_usd,
    'efectivo_euro': mt_trans_euro,
    'pago_movil': mt_pago_movil,
    'credito':  mt_credito,
    'sub_total': invoi.amount_untaxed,
    'porc_descuento': 0.0,
    'total_pagar': invoi.amount_total,
    #'total_pagar': monto_total,
    'factura_afectada': referencia
    }

    return dfc