# -*- encoding: utf-8 -*-
{
    "name": "SW - SQL ",
    "version": "11.0.1.0",
    "category": "Extra Tools",
    "description": """
		Allow execution of arbitrary SQL commands on DB.
		This module can be useful in order to execute **simple** queries/updates on database without direct access to server.
		The module create a new menu "Configuration" -> "Technical" -> "Tools" -> "SQL Queries".
		Only members of group "SQL manager" can use it.
		""",
    'author': "Smart Way Business Solutions",
    'website': "http://smartway-jo.com/",
    "depends": ["base", "base_toolbox"],
	"license" : 'AGPL-3',
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/sql_command.xml',
        'views/create_views.sql',
        'views/res_config_view.xml',
        'wizard/sqlcommandconfirm_view.xml',
    ],
    "installable": True,
    "active": False,
    "auto_install":False,
	"application" : False,
}
