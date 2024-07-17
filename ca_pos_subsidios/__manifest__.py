# -*- coding: utf-8 -*-
#################################################################################################
#
#    Subsidio de ventas para clientes de parte de terceros
#
#    Author: Carlos Alfonzo (calfonzodaly@gmail.com)
#
##################################################################################################
{
    'name': "Subsidio de ventas POS",
    'version': '17.0.1.1.1',
    'summary': "Permite el subsidio de ventas realizadas en rl punto de venta",
    'description': """
    Permite el subsidio de ventas realizadas en el punto de venta emitiendo una factura al cliente directo y otra al subsidiario, 
    definiendo porcentaje de subsidio (sobre el pecio), entre otros parametros
    """,
    'category': 'Point of sale',
    'author': 'Carlos Alfonzo',
    'maintainer': 'Carlos Alfonzo',
    'company': 'Carlos Alfonzo',
    'website': 'https://github.com/superka86',
    'depends': [
        'base','point_of_sale', "sale_management", "account"
        ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'ca_pos_subsidios/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}