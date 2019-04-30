# -*- coding: utf-8 -*-
{
    'name': 'SW - Deferred Revenue Enhacnement',
    'version': '11.0.1.0',
    'category': 'Accounting',
    'description': """
    - Add new field in fiscal position "Deferred Revenue Accounts".
    - Mapping generated deferred revenue entries based on fiscal position.
    -Upone canceling a deferred revenue invoice, the system will remove all related journal entires and deferred reveneue records.
    -Ensuring the deferred revenue record date is always the first day of the invoice month.
    """,
    'author': 'Smart Way Business Solutions',
    'website': 'https://www.smartway-jo.com',
    'depends': [
        'account','account_asset'
    ],
    'data': [
            'security/ir.model.access.csv',
             'views/fiscal_position.xml'
    ],
}
