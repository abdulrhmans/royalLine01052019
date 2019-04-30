# -*- encoding: utf-8 -*-
{
    'name' : 'SW - Payroll Extra Fields/Rules',
    'version' : '11.0.1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'summary' : 'This module add extra fields and rules',
    'description': """
- In payslip page, we have added new fields:
    - Add new field in Worked Days table, leave type of each line if exist, to manage paid and unpaid leaves in deductions rules.
    
- In contract page, we have added new fields:
    - Other Allowance.
    - Make Working Schedule in contract page and Working Hours in employee profile synced.
    
- In leave types page, we have added new fields:
    - Unpaid, to mark the unpaid leaves.
    - Code, to read and calculate based on it.

- In employee page:
    - Make Working Hours fields read only.
    
- New salary rules:
    - Other Allowance.
    - Basic Salary Deduction.
    - Other Deduction.""",
    
    'data': [
            "view/hr_employee.xml",
            "view/hr_contract.xml",
            "view/hr_payroll.xml",
            "view/hr_holidays.xml",
            'view/salary_rule.xml',
            ],
    'depends' : ['base', 'hr_payroll', 'hr_contract','base_payroll'],
    'installable': True,
    'auto_install': False,
}