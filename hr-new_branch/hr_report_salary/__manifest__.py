# -*- encoding: utf-8 -*-
{
    "name" : "SW - HR Extra Report",
    "version" : "1.0",
    'author' : 'Smart Way Business Solutions',
    'website' : 'https://www.smartway-jo.com',
    "category" : "Human Resources",
    "description": """
        - Add new two reports : Salary statements report and Salary details report 
                        """,
    "depends" : ["base",'account','hr', 'hr_payroll','hr_enhancement'],
    "data" : [
                "extra_hr_reports.xml",
                'views/salary_state_report.xml',
                'views/salary_detail_report.xml',
                'wizard/salary_state_report_wizard_view.xml',
                'wizard/salary_detail_report_wizard_view.xml',
                'security/ir.model.access.csv',
                ],
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: