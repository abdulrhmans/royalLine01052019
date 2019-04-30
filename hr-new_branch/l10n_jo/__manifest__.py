# -*- coding: utf-8 -*-
{
    'name': 'Jordan - Accounting',
    'version': '11.0.1.0',
    'category': 'Localization',
    'description': """
This is the base module to manage the accounting chart for Jordan in Odoo.
==============================================================================
    """,
    'website': 'https://www.smartway-jo.com',
    'author': 'Smart Way Business Solutions',
    'depends': ['account','l10n_multilang',],
    'data': [
        'data/account.group.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/account_jo_coa_data.xml',
        'data/account_data.xml',
        'data/account_tax_template_data.xml',
        'data/fiscal_templates_data.xml',
        'data/res.lang.csv',
        'data/account_chart_template_data.yml',
    ],
}
