# -*- coding: utf-8 -*-
{
    'name': "SW - Change Account Move Name",
    'summary': """Allow Admin users to change JE sequence""",
    'description': """
        Under Settings -> Tools -> Change JE Seq, you will be able to change the journal entry sequence even if it is posted.
    """,
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'category': 'Extra Tools',
    'version': '11.0.1.0',
    'depends': ['base', 'account', 'base_toolbox', ],
    'installable': True,
    'auto_install': False,
    'data': ['wizard/account_move_wizard_view.xml'],
}
