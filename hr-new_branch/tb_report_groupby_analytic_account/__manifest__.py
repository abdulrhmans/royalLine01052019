# -*- coding: utf-8 -*-
{
    'name': "SW - Trial Balance Analytic Separate Tables",
    'summary': "TB Report Standard",
    'description': """
        - Not compatible with tb_report_columns_into_one
        - When click on group by filter, system will add all analytic accounts by default if not set.
    """,
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends': ['base','account','account_reports'],
    'installable': True,
    'auto_install': False,
    'data': [
        'view/trial_balance.xml',
        'view/data.xml',
    ],
}
