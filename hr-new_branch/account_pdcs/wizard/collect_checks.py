# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CollectChecksAction(models.TransientModel):
    _name = 'collect.checks.action'
    _description = "Collect Cheques Action"

    @api.multi
    def collect_checks(self):
        account_payment = self.env['account.payment']
        for payment in account_payment.browse(self._context.get('active_ids', [])):
            if payment.partner_type == 'transfer':
                    raise UserError(_("Payment '%s' is a transfer payment!" % (payment.name)))
                
            if not payment.is_check:
                    raise UserError(_("Payment '%s' not cheque!" % (payment.name)))
            
            if payment.state != 'posted':
                raise UserError(_("Payment '%s' must be posted to collect!") % (payment.name))
            
            if payment.collect_move_id:
                raise UserError(_("Payment '%s' already collected!") % (payment.name))
            
            if not payment.collect_date:
                raise UserError(_("Please set 'Collection Date' for '%s'!") % (payment.name))
            
            if payment.partner_type == 'customer':
                if payment.state == 'posted' and not payment.collect_move_id and payment.cus_check_state == 'under_collection':
                    payment.collect_check()
                else:
                    if payment.cus_check_state != 'under_collection':
                        raise UserError(_("Payment '%s' must be send to bank before collect!") % (payment.name))
                    
                    
            if payment.partner_type == 'supplier':
                if payment.state == 'posted' and not payment.collect_move_id and payment.sup_check_state == 'issued':
                    payment.collect_check()
                else:
                    if payment.sup_check_state != 'issued':
                        raise UserError(_("Payment '%s' must be confirm before collect!") % (payment.name))
                    

        return {'type': 'ir.actions.act_window_close'}
