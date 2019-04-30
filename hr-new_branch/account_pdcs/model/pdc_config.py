# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BankShortcut(models.Model):
    _name = "pdc.config"
    _description = "Cheque Banks"
    
    name = fields.Char('Name',required=True)
    box_account = fields.Many2one('account.account',"Cheques Box",required=True)
    bank_account = fields.Many2one('account.account',"Bank",required=True)
    pdc_received_account = fields.Many2one('account.account',"PDC's Received",required=True)
    pdc_issued_account = fields.Many2one('account.account',"PDC's Issued",required=True)
    company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env.user.company_id)
    
    @api.multi
    def unlink(self):
        checks_obj = self.env['account.check']
        for bank in self:
            if checks_obj.search([('bank_id','=', bank.id)]):
                raise UserError(_('You can not remove this record, as it is reference in customer/supplier payment.'))
        return super(BankShortcut, self).unlink()