# -*- encoding: utf-8 -*-
{
    'name' : 'SW - HR Employee Intercompany',
    'version' : '11.0.1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'summary' : 'HR Multi-company - Remove Record Rules',
    'description': """
        - Remove record rules of employees, contracts, Departments & Job Positions to allow the user to see all employees in all companies and their contracts.
        - Set current user company to payslip to avoid the access right error.
        """,
    'data': [],
    'depends' : ['hr_payroll', 'hr_payroll_enhancement'],
    'installable': True,
    'auto_install': False,
}