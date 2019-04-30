# -*- encoding: utf-8 -*-
{
    'name' : 'SW - Payment Enhancement',
    'version' : '11.0.1.0',
    'category' : 'Accounting',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'depends' : ['account','account_accountant'],
    'data' : ['views/view.xml',
              'views/report.xml' ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'description': '''
    - Show move_name in list,form and search views, also in Payment Receipt report.
    - Add Journal Entries button in payment form view.'''
}
