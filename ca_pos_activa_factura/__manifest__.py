# -*- coding: utf-8 -*-
#################################################################################################
#
#    Activar facturar en POS
#
#    Author: Carlos Alfonzo (calfonzodaly@gmail.com)
#
##################################################################################################
{
    'name': "Activar facturar en POS",
    'version': '17.0.1.1.1',
    'summary': " Activar facturar en POS",
    'description': """
     Activar facturar en POS
    """,
    'category': 'Point of sale',
    'author': 'Carlos Alfonzo',
    'maintainer': 'Carlos Alfonzo',
    'company': 'Carlos Alfonzo',
    'website': 'https://github.com/superka86',
    'depends': [
        'base','point_of_sale'
        ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ca_pos_activa_factura//static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}