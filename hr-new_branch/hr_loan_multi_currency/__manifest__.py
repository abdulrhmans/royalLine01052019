# -*- coding: utf-8 -*-
{
    'name': 'SW - Loan Different Currency',
    'summary': 'Allows to choose currency on loan request',
    'version': '11.0.1.0',
    'category': 'Human Resources',
    'website' : 'https://www.smartway-jo.com',
    'author' : 'Smart Way Business Solutions',
    'description': """
    - New field in Loan request page 'Currency', this will be the currency of the loan.
    - Payment receipt will be in company currency.
""",
    'depends': ['hr_loan'],
    'data': [
            'views/loan.xml',
             ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
