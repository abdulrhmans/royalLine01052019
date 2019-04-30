# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

class SendCheckBank(models.TransientModel):
    _name = 'send.check.bank'
    _description = "Send To Bank Action"

    send_bank_date = fields.Date("Date",required=True, default=datetime.datetime.now())
    
    @api.multi
    def send_bank(self):
        account_payment = self.env['account.payment']
        for payment in account_payment.browse(self._context.get('active_ids', [])):
            if payment.is_check and payment.state in ['draft','posted'] and not payment.hide_send_bank_button and payment.partner_type == 'customer':
                payment.send_to_bank_date = self.send_bank_date
                payment.send_check()
            else:
                if not payment.is_check:
                    raise UserError(_("Payment '%s' not cheque!" % (payment.name)))

                if payment.partner_type != 'customer':
                    raise UserError(_("Payment '%s' not for customer, please sure its related to customer!" % (payment.name)))

                if payment.state not in ['draft','posted']:
                    raise UserError(_("Payment '%s' must be draft or posted!" % (payment.name)))
               
                if payment.hide_send_bank_button:
                    raise UserError(_("Payment '%s' already sent to bank!" % (payment.name)))
                
        return {'type': 'ir.actions.act_window_close'}
