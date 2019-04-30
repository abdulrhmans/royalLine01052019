# -*- coding: utf-8 -*-
{
    'name': "SW - Account Discount",
    'summary': """
            This module illustrates sales discount on orders and reports
                """,
    'description': """
        - This module communicates the sales discounts into the invoices and journal entires. 
        - Allows entering of discounts in the invoice as well. 
                """,
    'author': "Smart Way Business Solution",
    'website': "https://www.smartway-jo.com",
    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends': ['base', 'account'],
    'data': [
        'security/dicsount_groups.xml',
        'views/res_config_settings_views.xml',
        'views/account_invoice.xml',
        'views/report_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application':False,
    'post_init_hook': 'post_init_hook',
}