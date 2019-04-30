# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    @api.multi
    def open_journal_entries(self):
        moves = self.env['account.move.line'].search([('payment_id','in',self.ids)]).mapped('move_id')
        move_ids = []
        if moves:
            move_ids = moves.mapped('id')
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }
        
    @api.multi
    def cancel(self):
        super(AccountPayment, self).cancel()
        for rec in self:
            rec.invoice_ids = [(6, 0, [])]