# -*- encoding: utf-8 -*-
{
    'name' : 'SW - Public Holidays Management',
    'version' : '11.0.1.0',
    'category' : 'Human Resources',
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'summary' : 'Manage Employees Public Holidays',
    'license' : 'AGPL-3',
    'description': """
- New page 'Public Holidays' under Leaves Module, can be accessed only by HR manager, to manage the public holidays for company.
- Automatic reimbursement if public holiday ovelaped with a legal leave (Annual Leave).
- Add new leave type called 'Public Holiday' for managing the public leaves under this type.
- Add connection between public holiday record and related leaves created.
""",
    'data': [
             'view/public_holiday.xml',
             'wizard/generate_holiday_wizard.xml',
             'security/ir.model.access.csv',
             'data/data.xml',
             ],
    'depends' : ['base', 'hr_holidays','base_leave','hr_contract'],
    'installable': True,
    'auto_install': False,
}