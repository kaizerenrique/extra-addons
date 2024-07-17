{
    "name": "POS Multi Currency Payment | POS: Show Dual Currency | Multi Currency Payment Venezuela | Base Currency USD and 2nd Currency is Bs",
    "version": "17.0.3.2.1",
    'sequence': 1,
    "description": """
        Using this module you can add payment in Dual currency.
    """,
    "summary": """Using this module you can add payment in Dual currency.""",
    "category": "Point Of Sale",
    'price': 125,
    'currency': 'EUR',
    'license': 'OPL-1',
    "author" : "MAISOLUTIONSLLC",
    'sequence': 1,
    "email": 'apps@maisolutionsllc.com',
    "website":'http://maisolutionsllc.com/',
    "depends": ["point_of_sale"],
    "data": [
        "views/views.xml"
    ],
    "qweb": ["static/src/xml/pos.xml"],
    # 'assets': {
    #     'point_of_sale.assets': [
    #         'mai_pos_dual_currency/static/src/css/pos.css',
    #         'mai_pos_dual_currency/static/src/js/**/*',
    #         'mai_pos_dual_currency/static/src/xml/**/*',
    #     ],
    # },
    'assets': {
        'point_of_sale._assets_pos': [
            'mai_pos_dual_currency/static/src/**/*',
        ],
    },
    "images": ['static/description/main_screenshot.png'],
    "live_test_url" : "",
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
