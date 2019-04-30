# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from email.utils import formataddr
from odoo.exceptions import UserError

class AccountMove(models.Model):

    _name = 'account.move'    
    _inherit = ['account.move', 'mail.thread']

    state = fields.Selection(track_visibility='always')
    ref = fields.Char(track_visibility='onchange')
    date = fields.Date(track_visibility='onchange')    
    amount = fields.Monetary(compute='_amount_compute', store=True, track_visibility='onchange')
    
    @api.multi
    @api.depends('line_ids.debit', 'line_ids.credit')
    def _amount_compute(self):
        for move in self:
            total = 0.0
            for line in move.line_ids:
                total += line.debit
            move.amount = total
            
    @api.multi
    def button_cancel(self):
        res = super(AccountMove,self).button_cancel()
        self.create_mail_message(body='Cancel Journal Entry')
        return res
    
    @api.one
    def _get_default_from(self):
        if self.env.user.email:
            return formataddr((self.env.user.name, self.env.user.email))
        raise UserError(_("Unable to send email, please configure the sender's email address or alias."))
    
    @api.multi
    def create_mail_message(self, body):
        user = self.env.user
        for move in self:
            vals = {'type': 'notification',
                'author_id': user.partner_id.id,
                'date': datetime.now(),
                'email_from': self._get_default_from(),
                'model': 'account.move',
                'res_id': move.id,
                'subtype_id': 2,
                'body': body}
            self.env['mail.message'].create(vals)