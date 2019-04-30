# -*- encoding: utf-8 -*-
{
    'name' : 'SW - HR Overtime',
    'version' : '11.0.1.0',
    'category' : 'Human Resource',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'license' : 'AGPL-3',
    'description': """
    - Add overtime Feature .""",
    'data': [
             "view/hr_overtime.xml",
             'view/analytic_tag.xml',
             'wizard/validate_overtime.xml',
             'security/ir.model.access.csv'
             ],
    'depends' : ['base','hr','account','analytic','hr_enhancement','hr_payroll','hr_payroll_account'],
    'installable': True,
    'auto_install': False,
}