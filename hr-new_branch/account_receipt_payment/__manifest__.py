# -*- coding: utf-8 -*-
{
    'name': 'SW - Receipts',
    'version': '11.0.1.0',
    'category': 'Accounting',
    'description': """
""",
    'author' : 'Smart Way Business Solutions',
    'website' : ' https://www.smartway-jo.com',
    'depends': ['base','account','account_accountant'],
    'init_xml': [],
    'data': [
             'view/payment_view.xml',
#              'view/receipt.xml',
#              'view/payment.xml',
#              'report.xml',
#              'view/receipt_report.xml',
            'security/ir.model.access.csv'
             ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
