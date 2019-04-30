# -*- encoding: utf-8 -*-
{
    'name' : 'SW - Health Insurance',
    'version' : '11.0.1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'summary' : 'Manage Employees Health Insurance',
    'description': """
    - In employee page, we have added fields:
    - Dependent Information.
    - Employee Health Insurance Amount.
    - Computed fields: Dependents Health Insurance Amount.
    - Salary Rule to deduct the health insurance.""",
    'data': [
            "view/hr_employee.xml",
            "view/salary_rule.xml",
            "security/ir.model.access.csv"
            ],
    'depends' : ['base','hr','hr_payroll'],
    'installable': True,
    'auto_install': False,
}