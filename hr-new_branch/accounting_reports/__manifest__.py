# -*- coding: utf-8 -*-
{
    'name': "SW - Analytic Reports",
    'summary': """
                Extra Analytic Reports
			""",
    'description': """
                -Added a Menu Item in the Accounting module-> reporting -> management section.
                -A wizard appears to print the reports.
                -If the financial account is selected the report "Analytic details per financial account" is printed. If not selected the report "Analytic Details report" is printed.
    """,
    'author': "Smart Way Business Solutions",
    'website': "https://www.smartway-jo.com",
    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends': ['base','account','common_report'],
    'installable': True,
    'auto_install': False,
    'data': [
        'report/analytic_report.xml',
        'report/analytic_report_per_fin.xml',
        'wizard/analytic_account_report_wizard_view.xml',
    ],
}
