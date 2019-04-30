# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def action_invoice_open(self):
        for inv in self:
            for line in inv.invoice_line_ids:
                if not line.account_analytic_id or not line.analytic_tag_ids:
                    raise UserError("Please fill all lines with Analytic Accounts and at least one Analytic Tag.")
        return super(AccountInvoice, self).action_invoice_open()


            
            
        