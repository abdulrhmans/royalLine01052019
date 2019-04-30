# -*- coding: utf-8 -*-

from odoo import fields, models, _,api
from odoo.exceptions import UserError


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"
    
    currency_id = fields.Many2one('res.currency', 'Currency')
    with_initial =fields.Boolean('With Initial Balance',default=True)
    
    
    
    
    
    def print_report_fc(self):
        print(self._context)
        data = self[0].read()
        if 'active_ids' in self._context:
            data[0].update({'active_ids':self._context['active_ids']})
        return self.env.ref('pl_foreign_currency.action_report_partnerledger').report_action(self, data={'form':data[0]})
