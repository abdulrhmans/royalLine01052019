# -*- coding: utf-8 -*-
{
    'name': "SW - Auto Backup",
    'summary': 'Automated backups',
    'description': """
    The Database Auto-Backup module enables the user to make configurations for the automatic backup of the database. 
    Backups can be taken on the local system or on a remote server, through SFTP.
    You only have to specify the hostname, port, backup location and database name (all will be pre-filled by default with correct data.
    If you want to write to an external server with SFTP you will need to provide the IP, username and password for the remote backups.
    """,
    'author': "Smart Way Business Solutions",
    'website': "http:/projects.smartway-jo.com",
    'category': 'Extra Tools',
    'version': '11.0.1.0',
    'installable': True,
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/backup_data.xml',
        'data/backup_google_drive_data.xml',
        'views/backup_view.xml',
        'views/backup_retention_policy_views.xml',
    ],
}
