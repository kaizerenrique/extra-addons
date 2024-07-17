# -*- coding: utf-8 -*-
#################################################################################################
#
#    Buscar clientes por ceula o vat
#
#    Author: Carlos Alfonzo (calfonzodaly@gmail.com)
#
##################################################################################################
{
    'name': "Buscar clientes por cedula",
    'version': '17.0.1.1.1',
    'summary': " Buscar clientes por ceula o vat",
    'description': """
     Buscar clientes por ceula o vat
    """,
    'category': 'Point of sale',
    'author': 'Carlos Alfonzo',
    'maintainer': 'Carlos Alfonzo',
    'company': 'Carlos Alfonzo',
    'website': 'https://github.com/superka86',
    'depends': [
        'base','point_of_sale',
        ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ca_pos_buscar_ci/static/src/js/partner_list.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}