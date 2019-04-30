# -*- coding: utf-8 -*-
{
    'name': "SW - Payroll Access Rights",
    'summary': """Add access rights to employees to access their payslips""",
    'description': """
            -Add access rights payslip to employee.
            -Add record rule for employee payslip to just his his payslips.
            -Remove group 'Payroll Officer' from 'Employee Payslips' menuitem.
            -If you installed this module and want to uninstall it you should add group 'Payroll Officer' to 'Employee Payslips' menuitem manually. """,

    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'license':  "Other proprietary",
    'category': 'Human Resources',
    'version': '11.0.1.0',
    'depends': ['base','hr_payroll'],
    'installable': True,
    'auto_install': False,
    'data': [
        'security/ir.model.access.csv',
        'views/payroll_view.xml',
    ],
}
