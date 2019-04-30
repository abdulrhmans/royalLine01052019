# -*- encoding: utf-8 -*-
{
    "name" : "SW - Extra Account Reports",
    "version" : "11.0.1.0",
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    "category" : "Accounting",
    "description": """
    - Journal Entry Report.
                        """,
    "depends" : ["base",'account','common_report'],
    "data" : [
                    "extra_account_reports.xml",
                    'views/journal_entries.xml',
            ],
    "installable": True
}