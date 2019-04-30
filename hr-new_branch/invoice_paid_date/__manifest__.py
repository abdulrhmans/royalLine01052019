# -*- coding: utf-8 -*-
{
    'name' : 'SW - Invoice Paid Date',
    'summary': """
                This module modify the open date and paid date of invoice
        """,
    'description': """
                    Modify the open and paid date of invoice when reopen or repaid
                    Add new fields 'paid date' to account invoice
                     
                 """,
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",

    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends' : ['base', 'account',],
    'data' : [
            'views/account.xml',
    ],
    'auto_install': False,
    'application': False,
    'installable': True,
}
