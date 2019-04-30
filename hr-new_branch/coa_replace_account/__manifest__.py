# -*- encoding: utf-8 -*-
{
    'name' : 'SW - COA Replace Account',
    'version' : '11.0.1.0',
    'category' : 'Accounting',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'depends' : ['account','account_accountant'],
    'data' : ['wizard/replace_account.xml','security/ir.model.access.csv' ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'description': '''
    - Add replace account action for COA.
    
    '''
}
