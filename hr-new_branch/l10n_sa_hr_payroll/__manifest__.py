# -*- coding: utf-8 -*-
{
    'name': 'SW - Saudi Payroll',
    'version' : '11.0.1.0',
    'category': 'Localization',
    'summary' : """Saudi Payroll Localization""",
    'description': """This module adds the following fields at employee profile:
            - GOSI Number.
            - Hwayah/Iqma.
            - Employee Number.
        This module adds the housing allowance field at employee contract.
        This module adds the following salary rules:
            - GOSI Deduction.
            - GOSI Contrebution.
            - Housing Allowance.
            - Housing Deductoin.
        This adds the GOSI report under payroll - reports.""",
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    'depends': ['hr', 'hr_payroll', 'common_report', 'base_payroll'],
    'data': ['data/rule.xml',
             'report/paper_format.xml',
             'report/salary_gosi_report.xml',
             'report/extra_hr_reports.xml',
             'wizard/salary_gosi_report_wizard_view.xml',
             'views/views.xml'
                    ],
}
