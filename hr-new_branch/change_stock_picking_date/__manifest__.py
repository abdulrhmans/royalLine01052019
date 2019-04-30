# -*- coding: utf-8 -*-
{
    'name': "SW - Change Stock Picking Date",
    'summary': """
        This module add "Change Picking Date" wizard  under Tools Menu in Settings for developer mode
			""",
    'description': """
        With wizard you can choose done pickings and change its "Scheduled Date" & "Date of Transfer",
          and changes "Expected Date & date" on Stock Move for this pickings & "Date" on Stock Move Line for this Stock Move  """,
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'category': 'Extra Tools',
    'version': '11.0.1.0',
    'depends': ['base','stock','base_toolbox','account'],
    'installable': True,
    'auto_install': False,
    'data': [
        'wizard/stock_picking_wizard_view.xml',
    ],
}
