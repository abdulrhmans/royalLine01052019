# -*- coding: utf-8 -*-
{
    'name': 'SW - SO Down Payment',
    'summary':"Direct registration for a down payment from a sale order",
    'author' : 'Smart Way Business Solutions',
    'website': 'https//www.smartway-jo.com',
    'license':  "Other proprietary",
    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends': ['base', 'account', 'sale', 'sales_team'],
    'data': [
            'security/ir.model.access.csv',
            'wizard/register_account_payment.xml',
            'view/saleorder_payment.xml',
             ], 
    'images':  ["static/description/image.png"],
    'price': 25,
    'currency' :  'EUR',
    'installable': True,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
