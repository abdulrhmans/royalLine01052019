# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.multi
    def unlink(self):
        for move in self:
            if move.name and move.name != '/':
               raise UserError(_("You can`t delete Journal Entry that have a sequence"))
        return super(AccountMove,self).unlink()
	
