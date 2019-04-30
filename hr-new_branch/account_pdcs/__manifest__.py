# -*- coding: utf-8 -*-
{
    'name': 'SW - Cheques',
    'version': '11.0.1.0',
    'category': 'Accounting',
    'description': """
""",
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'depends': ['base','account',
                'account_receipt_payment'],
    'init_xml': [],
    'data': [
             'view/payment_view.xml',
             'view/pdc_config.xml',
             'wizard/collect_checks.xml',
             'wizard/send_to_bank.xml',
             'security/ir.model.access.csv'
             ],
    'images':  ["static/description/image.png"],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
