# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
    
class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    paid_date = fields.Datetime('Paid Date',readonly=True)
    validation_date = fields.Datetime('Validation Date',readonly=True)
    
    @api.multi
    def action_invoice_paid(self):
        for rec in self:
             self._cr.execute("update account_invoice set paid_date = '%s' where id = %s "%(str(fields.Datetime.now()),rec.id))
        return super(AccountInvoice,self).action_invoice_paid()
    
    
    @api.multi
    def action_invoice_open(self):
        for rec in self:
            rec.validation_date = fields.Datetime.now()
        return super(AccountInvoice,self).action_invoice_open()
    
    @api.multi
    def action_invoice_re_open(self):
        for rec in self:
            self._cr.execute("update account_invoice set validation_date = '%s' where id = %s "%(str(fields.Datetime.now()),rec.id))
        return super(AccountInvoice,self).action_invoice_re_open()

    
 
    
    
    
    
    
    