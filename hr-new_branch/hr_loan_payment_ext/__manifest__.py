# -*- coding: utf-8 -*-
{
    'name': 'SW - Loan Payment Ext',
    'summary': 'Compatibility fix with Account Receipt & Payment module',
    'version': '11.0.1.0',
    'category': 'Human Resources',
    'website' : 'https://www.smartway-jo.com',
    'author' : 'Smart Way Business Solutions',
    'description': """
    - Handle payments of loans for account receipt module.
    - Deactivate form view inheriting the payment.
    - Partner not required if there is a loan in payment.
""",
    'depends': ['hr_loan','account_receipt_payment'],
    'data': [
            'views/function.xml',
             ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
