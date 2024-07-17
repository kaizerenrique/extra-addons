# -*- coding: utf-8 -*-

from odoo import fields, models, api
import os
import platform
import csv
from odoo.http import request

from . import ext_doc

from datetime import datetime
import re
import logging
_logger = logging.getLogger(__name__)

#Extension de los archivos de respuesta fiscal para SuperSpooler. Considerar mayusculas/minusculas
EXTENSION_ARCHIVO_RESPUESTA = "RES"
COLUMNAS_RES = ['fecha', 'hora', 'ref_interna', 'numero_fiscal', 'tipo', 'estatus', 'proximo_z', 'serial_impresora', 'doc_afectado']

#Prefijo archivos de facturas y notas de credito para SuperSpooler
PREFIJO_FACTURAS = "fa"
PREFIJO_NOTAS_CREDITO = "nc"
DELIMITADOR_CSV = '\t'
ERROR_ARCHIVO = "error_archivo"
ERROR_DATOS = "error_datos"
ERROR_DOCUMENTO_NOEXISTE = "error_documento_no_existe"
DATOS_CARGADOS = "cargado"
DATOS_PENDIENTES = 'pendiente'
DATOS_ANULADOS = 'anulado'    #Marca un documento para no procesarlo, es decir, no intentar cargar su info fiscal
CARPETA_ENTRADA = '/var/lib/odoo/facturas_txt'
POR_IVA = 0.16
FACTOR_IVA = 1.16

def gen_archivo_factura( invoi ):
    #doc = extraer( invoi )
    doc = ext_doc.extraer_documento( invoi )
    if doc:
        nombre, currency_rate, currency_symbol = preparar_nombre_archivo( invoi, doc )
    else:
        return {}

    if doc['tipodoc'] == "fac" and nombre:
        f = open(nombre, "w")
        f.write ( "FACTURA:         {}".format( doc['numero'] ) + "\n" )
    elif doc['tipodoc'] ==  "nc":
        f = open(nombre, "w")
        f.write ( "DEVOLUCION:      {}".format( doc['numero'] ) + "\n" )
    else:
        return {}

    escribir_archivo_factura(f, doc, currency_rate, currency_symbol, invoi)
    #cargar_datos_fiscales( doc['numero'], doc['tipodoc'], invoi )
    return doc


def preparar_nombre_archivo( invoi, doc ):
    numero_doc = doc['numero']
    tipo_doc = doc['tipodoc']

    datos = invoi.env['pos.config'].search([], limit=1) 

    if datos:
        carpeta= datos['carpeta_txt']
        currency_symbol = datos['currency_id']
    else:
         currency_symbol = ""

    currency_rate = invoi.env['res.currency'].search([('name', '=', 'VEF')], limit=1).rate
    extension = invoi.pos_order_ids[0].session_id.config_id.extension_archivos
    tipo_nombre = invoi.pos_order_ids[0].session_id.config_id.estilo_nombre
    if not extension: extension = "odo"
    
    if (not datos) or (carpeta == "") or (not isinstance(carpeta, str)):
        carpeta = os.path.expanduser("/tmp") if platform.system() == "Linux" else "c:\\temp"

    separador = "/" if platform.system() == "Linux" else "\\"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    if tipo_nombre == "1":
        nombre = carpeta + separador + "odoo" + "." + extension
    else:
        if tipo_doc == "fac":
            nombre = carpeta + separador + "fa" + numero_doc + "." + extension
        elif tipo_doc ==  "nc":
            nombre = carpeta + separador + "nc" + numero_doc + "." + extension
        else:
            nombre = ""

    return nombre, currency_rate, currency_symbol.name


def escribir_archivo_factura(f, doc, currency_rate, currency_symbol, invoi):
    f.write ( "FECHA:           " + doc['fecha'] + "\n"  )
    f.write ( "CLIENTE:         " + doc['cliente'] + "\n"  )
    f.write ( "RIF:             " + doc['rif'] + "\n" if doc['rif'] else "RIF:" + "\n" )
    f.write ( "DIRECCION1:      " + doc['dir1'] + "\n"  if doc['dir1'] else "DIRECCION:" + "\n"  )
    f.write ( "DIRECCION2:      " + doc['dir2'] + "\n" if doc['dir2'] else "DIRECCION2:" + "\n" )
    f.write ( "TELEFONO:        " + doc['telefono'] + "\n" if doc['telefono'] else "TELEFONO:" + "\n" )

    f.write ( "DESCRIPCION                                                 COD          CANT.    IVA    PRECIO UNIT\n")

    factor_moneda = currency_rate #1.0/currency_rate

    FFISCAL_LONG_MAX_DESCRIPCION = 60
    for pos in doc['productos']:
        # Separar la descripcion del item en lineas segun la longitud maxima por linea 
        item_fact = doc['productos'][pos]
        desc = item_fact['descripcion'] if item_fact['descripcion'] else " " #Si agregan items vacios
        long_desc = len( desc )
        lst_descripciones_item = [ desc[i:i+FFISCAL_LONG_MAX_DESCRIPCION] for i in range(0, long_desc, FFISCAL_LONG_MAX_DESCRIPCION ) ]

        #Guarda cada parte de la descripcion en lineas separadas, en las lineas adicionales solo va Descripcion
        #y el esto de las columnas en blanco, en caso de haber lineas adicionales
        
        # Escribe los items formateados en el archivo
        f.write( "{:<60}".format( lst_descripciones_item[0] ) )
        f.write( "{:<8}".format( item_fact['codigoprod'] ) )
        f.write( "{:>10.2f}".format( item_fact['cantidad'] ) )

        f.write( "{:>8.2f}".format( item_fact['iva'] ) )

        f.write( "{:>12.2f}".format( item_fact['precio'] * factor_moneda ) + "\n"  )

        #Escribe las lineas adicionales de la descripcion
        pos = 1
        while pos < len( lst_descripciones_item ):
            f.write( "{:<60}".format( lst_descripciones_item[pos] ) + "\n" )
            pos += 1
    
    #tot_efectivo = round ( (doc['efectivo']['monto']/1.16 * factor_moneda ) , 2)
    #tot_efectivo = round (tot_efectivo + tot_efectivo * 0.16, 2)
    #En contenedor, en ext_doc -> crear_campos
    monto_bs =  invoi.amount_total / FACTOR_IVA * currency_rate
    iva_bs = monto_bs * POR_IVA
    total_bs =  monto_bs + iva_bs

    #Contenedor. spooler.py
    #tot_efectivo = round ( (doc['efectivo']['monto']/1.16 ) , 2)
    #tot_efectivo = round(tot_efectivo * factor_moneda, 2)
    #tot_iva = round( tot_efectivo * 0.16, 2)
    #tot_efectivo = tot_efectivo + tot_iva
    #....
    #f.write ( "EFECTIVO: {:>10.2f}".format( tot_efectivo ) + "\n" )

    # Totales
    #f.write ( "SUB-TOTAL:      {:>10.2f}".format(doc['sub_total'] * factor_moneda ) + "\n")
    f.write ( "SUB-TOTAL:      {:>10.2f}".format( monto_bs ) + "\n")
    f.write ( "DESCUENTO:      {:>10.2f}".format(0.0) + "\n")
    f.write ( "TOTAL A PAGAR:  {:>10.2f}".format(total_bs ) + "\n")
    #f.write ( "TOTAL A PAGAR:  {:>10.2f}".format(doc['total_pagar'] * factor_moneda ) + "\n")
    #f.write ( "CURRENCY     :  {:>10.2f}".format(currency_rate ) + "\n")

    f.write ( "EFECTIVO:       {:>10.2f}".format(doc['efectivo']['monto']  ) + "\n" )
    f.write ( "CHEQUES:        {:>10.2f}".format(doc['banco']['monto']  ) + "\n" )
    f.write ( "TARJ/DEBITO:    {:>10.2f}".format(doc['tarj_debito']['monto']  ) + "\n" )
    f.write ( "TARJ/CREDITO:   {:>10.2f}".format(doc['tarj_credito']['monto']  ) + "\n" )
    f.write ( "Tranf en Bs:    {:>10.2f}".format(doc['trans_bs']['monto']  ) + "\n" )
    f.write ( "Transf en USD:  {:>10.2f}".format(0.0) + "\n" )
    f.write ( "Zelle:          {:>10.2f}".format(doc['zelle']['monto']  ) + "\n" )
    f.write ( "Efect USD:      {:>10.2f}".format(doc['efectivo_usd']['monto']  ) + "\n" )
    f.write ( "Efect EURO:     {:>10.2f}".format(doc['efectivo_euro']['monto']  ) + "\n" )
    f.write ( "Pago movil:     {:>10.2f}".format(doc['pago_movil']['monto']  ) + "\n" )
    f.write ( "CREDITO:        {:>10.2f}".format(doc['credito']['monto']  ) + "\n" )
    '''
    f.write ( "EFECTIVO:       {:>10.2f}".format(doc['efectivo']['monto'] * factor_moneda ) + "\n" )
    f.write ( "CHEQUES:        {:>10.2f}".format(doc['banco']['monto'] * factor_moneda ) + "\n" )
    f.write ( "TARJ/DEBITO:    {:>10.2f}".format(doc['tarj_debito']['monto'] * factor_moneda ) + "\n" )
    f.write ( "TARJ/CREDITO:   {:>10.2f}".format(doc['tarj_credito']['monto'] * factor_moneda ) + "\n" )
    f.write ( "Tranf en Bs:    {:>10.2f}".format(doc['trans_bs']['monto'] * factor_moneda ) + "\n" )
    f.write ( "Transf en USD:  {:>10.2f}".format(0.0) + "\n" )
    f.write ( "Zelle:          {:>10.2f}".format(doc['zelle']['monto'] * factor_moneda ) + "\n" )
    f.write ( "Efect USD:      {:>10.2f}".format(doc['efectivo_usd']['monto'] * factor_moneda ) + "\n" )
    f.write ( "Efect EURO:     {:>10.2f}".format(doc['efectivo_euro']['monto'] * factor_moneda ) + "\n" )
    f.write ( "Pago movil:     {:>10.2f}".format(doc['pago_movil']['monto'] * factor_moneda ) + "\n" )
    f.write ( "CREDITO:        {:>10.2f}".format(doc['credito']['monto'] * factor_moneda ) + "\n" )
    '''
    # Notas 
    f.write ( "NOTA 1:        " + "\n")
    f.write ( "NOTA 2:        " + "\n")
    f.write ( "NOTA 3:        " + "\n")
    f.write ( "NOTA 4:        " + "\n")

    #if doc['tipodoc'] == "nc":
    if (doc['factura_afectada'] != "") :
        f.write ( "FACTURAAFECTADA:       {}".format(doc['factura_afectada']) + "\n" )