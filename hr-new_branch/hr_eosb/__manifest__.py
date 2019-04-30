# -*- coding: utf-8 -*-
{
    'name': 'SW - End Of Service Benefits',
    'version': '11.0.1.0',
    'category': 'Human Resources',
    'summary':"""Manage your employees end of service benefits""",
    'description': """This module adds the following functionalities:
        1- Configuration page to define the service period and EOS rules per reason, country, and gender.
        2- End of service reasons configuration.
        3- End of service calculation page under payroll module.
        4- End of service account at the settings page.
        5- End of service salary rule [tobe used if paid with payslip].
        6- Adds the following fields at employee contract page:
            - Contract Type.
            - Contract Duration.
            - End of service type & reasons""",
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'depends': ['hr','hr_payroll','base_leave','account'],
    'init_xml': [],
    'data': ['view/views.xml','security/ir.model.access.csv','view/res_config_settings_views.xml','data/data.xml'],
    'demo_xml': [],
    'installable': True,
}
