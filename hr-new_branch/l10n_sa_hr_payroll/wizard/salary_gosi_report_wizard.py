# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SalaryGosiReportWizard(models.TransientModel):
    _name = "salary.gosi.report.wizard"
    
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    note = fields.Text('Note')
    employee_ids = fields.Many2many('hr.employee', required=True)
    
    def print_report(self):
        report_name = 'l10n_sa_hr_payroll.salary_gosi_report'
            
        data = self.read()[0]
        datas = {
             'ids': self._context.get('active_ids', []),
             'model': 'hr.payslip',
             'form': data,
                 }
        return self.env.ref('l10n_sa_hr_payroll.salary_gosi_report').report_action(docids=[] , data=datas)

