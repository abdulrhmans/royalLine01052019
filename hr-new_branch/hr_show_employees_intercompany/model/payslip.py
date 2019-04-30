# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
     
    
    @api.multi
    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        res = super(HrPayslip, self).onchange_employee_id(date_from, date_to, employee_id=employee_id, contract_id=contract_id)
        if 'value' in res:
            res['value']['company_id'] = self.env.user.company_id.id
        return res
    
    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        res = super(HrPayslip, self).onchange_employee()
        self.company_id = self.env.user.company_id.id
        return res