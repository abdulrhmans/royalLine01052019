# -*- coding: utf-8 -*-

from odoo import api, models

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    @api.model
    def _remove_inherit_form(self):
        view_id = self.env.ref('hr_loan.view_account_payment_form')
        if view_id:
            view_id.active = False

class HrLoan(models.Model):
    _inherit = 'hr.loan'
    
    def get_payment_vals(self):
        res = super(HrLoan, self).get_payment_vals()
        res['partner_name'] = str(self.employee_id.name)
        return res