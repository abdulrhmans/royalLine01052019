# -*- coding: utf-8 -*-

from odoo import models, fields, api

class wizard_salary_satatements_report(models.Model):
    _name = "salary.statements.report"
    _description = "Salary Statements Report"
    
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    show_bank_account = fields.Boolean('Show Bank Account Number')
    show_social_security = fields.Boolean('Show Social Security')
    show_income_tax = fields.Boolean('Show Income Tax')
    employee_ids = fields.Many2many('hr.employee', 'salary_statment_employee_rel', 'employee_id', 'report_id',required=True)
    salary = fields.Selection([('basic','Basic Salary'),('net','Net Salary')], string='Based On', required=True, default='net')
    ss_company = fields.Boolean('Show Social Security company contribution')
    hi_company = fields.Boolean('Show Health Insurance company contribution')
    landscape = fields.Boolean("Landscape Mode")
    statement = fields.Html("Statement")
    
    
    def print_report(self, data):
        data['form'] = {}
        data['form'].update(self.read(['from_date', 'to_date', 'employee_ids', 'show_bank_account', 'show_social_security', 
                                       'show_income_tax','salary','ss_company','hi_company','statement'])[0])
        if self.landscape:
            return self.env.ref('hr_report_salary.salary_state_report').with_context(landscape=True).report_action(self, data=data)
        else:
            return self.env.ref('hr_report_salary.salary_state_report').report_action(self, data=data)