# -*- coding: utf-8 -*-

from odoo import models, fields

class HrLoan(models.Model):
    _inherit = 'hr.loan'
    
    currency_id = fields.Many2one('res.currency', 'Currency')
    
    def get_payment_vals(self):
        res = super(HrLoan, self).get_payment_vals()
        if self.currency_id and self.currency_id.id != self.env.user.company_id.currency_id.id:
            amount = self.currency_id.compute(self.total_amount, self.env.user.company_id.currency_id)
            res['amount'] = amount
        return res