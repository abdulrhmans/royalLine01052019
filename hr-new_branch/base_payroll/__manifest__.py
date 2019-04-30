# -*- encoding: utf-8 -*-
{
    'name' : 'SW - HR Base Payroll',
    'version' : '11.0.1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'summary' : 'Enhancement on Payroll Workflow',
    'description': """
        - Prevent compute slip on refunding.
        - In payslip page, we have added new fields:
            - 'Number Of Hours' , actual hours that employee should works in period.
            - 'Days In Period' actual working days that employee should works in period, .
      """,
    'data': ['view/views.xml'
            ],
    'depends' : ['base', 'hr_payroll'],
    'installable': True,
    'auto_install': False,
}