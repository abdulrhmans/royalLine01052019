# -*- encoding: utf-8 -*-
{
    'name' : 'SW - HR Enhancement',
    'version' : '1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'www.smartway-jo.com',
    'license' : 'AGPL-3',
    'description': """
    - Enhancements on employee, contract, holidays and payslip.
    - Add public holiday feature.
""",
    'data': ["view/hr.xml",
             'view/hr_holidays.xml',
#              'view/salary_rule.xml',
             'view/res.xml',
             'view/public_holiday.xml',
             'wizard/generate_holiday_wizard.xml',
             'security/ir.model.access.csv',
             ],
    'depends' : ['base','account','hr','hr_holidays','resource','hr_payroll','hr_payroll_account','hr_contract'],
    'installable': True,
    'auto_install': False,
}