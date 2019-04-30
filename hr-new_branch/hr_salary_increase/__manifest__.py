# -*- coding: utf-8 -*-
{
    'name': 'SW - HR Salary Increase',
    'version': '11.0.1.0',
    'summary': 'Manage Employees Salary Increase',
    'category': 'Human Resources',
    'website' : 'https://www.smartway-jo.com',
    'author' : 'Smart Way Business Solutions',
    'description': """This module adds a new menu item "Salary Increase" under the Payroll Module.
    This module adds the following functionalities:
    - The salary increase page where you can define an increase percentage/amount for one or more employees.
    - Workflow where the document needs to have 2 level of approvals "Finance Manager & HR Manager".
    - Salary Increase history table at employee contract.""",
    'depends': ['hr','hr_contract','hr_payroll','account'],
    'data': ['wizard/add_employee.xml','view/salary_increase.xml', 'security/ir.model.access.csv','view/res_config_settings_views.xml','security/rule.xml'],
}
