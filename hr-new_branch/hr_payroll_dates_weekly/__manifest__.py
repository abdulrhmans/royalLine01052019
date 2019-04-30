# -*- encoding: utf-8 -*-
{
    'name' : 'SW - HR Payroll Weekly',
    'version' : '11.0.1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'summary' : 'Auto-detect of weekly payslip dates',
    'description': """
        - In payslip page, dates range will be weekly: 
            - To date: The date of today.
            - From date: today-6.
        """,
    'data': [],
    'depends' : ['hr_payroll'],
    'installable': True,
    'auto_install': False,
}