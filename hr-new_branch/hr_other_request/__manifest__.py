# -*- coding: utf-8 -*-
{
    'name': 'SW - HR Employees Requests',
    'version': '11.0.1.0',
    'summary': """Manage Your Employees Requests""",
    'category': 'Human Resources',
    'website' : 'https://www.smartway-jo.com',
    'author' : 'Smart Way Business Solutions',
    'description': """This module adds a new page under the Employees module.
    This module adds the following functionalities:
    - New page "Other Requests" to allow the employees to request documents from HR department.
    - Workflow of approvals & stages of the request.
    - Ability to attach documents on the request.
    - Notifying the employees when the request is done.""",
    'depends': ['base','hr'],
    'data': ['view/views.xml','security/ir.model.access.csv','data/data.xml','view/config_setting.xml'],
    'installable': True,
}
