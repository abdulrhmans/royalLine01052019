# -*- coding: utf-8 -*-
{
    'name': "SW - Project Tasks Notification",
    'summary': """Enhancement for Project Module""",
    'description': """
        Enhancement for management for Project
    """,
    'category': 'Project Management',
    'author' : 'Smart Way Team',
    'website': "https://www.smartway-jo.com",
    'version': '0.1',
    'depends': ['project','mail'],
    'data': [
        'views/project_view.xml',
         'views/Reminder.xml',
    ],
    'application': False,
}
