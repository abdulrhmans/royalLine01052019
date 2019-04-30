# -*- coding: utf-8 -*-
{
    'name': "SW - Base ToolBox",
    'summary': 'Module adds a Tools Menu',
    'description': """
    This module adds a menu by the name of (Tools) under on settings page,
    The menu appears under the Developer mode only.""",
    'author': "Smart Way Business Solutions",
    'website': "http://smartway-jo.com/",
    'category': 'Extra Tools',
    'version': '11.0.1.0',
    'depends': ['base'],
    'data': [
        'security/groups.xml',
        'views/base_tools_menu.xml',
        'views/res_config_view.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
    
}
