# -*- coding: utf-8 -*-
{
    'name': "SW - Invoice Source Document Button",
    'summary': """
        Addition of a'Source Document' button linking you directly to your Vendor Bills and Invoices""",
    'description': """
    """,
    'license':  "Other proprietary",
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends': ['base','account','purchase','sale'],
    'data': [
        'views/account_invoice_views.xml',
    ],
    "images":  ['static/description/Image.png'],
}