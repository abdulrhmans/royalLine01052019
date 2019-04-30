# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.model
    def default_get(self, fields):
        ''''
            Set last name of journal line in case of a manual entry
        '''
        rec = super(AccountMoveLine, self).default_get(fields)
        
        if 'line_ids' not in self._context:
            return rec
        
        if self._context['line_ids']:
            dic = {}
            line = self._context['line_ids'][-1][2]
            if line:
                if 'name' in line:
                    dic['name'] = line['name']
                if 'analytic_account_id' in line :
                    dic['analytic_account_id'] = line['analytic_account_id']
                if 'partner_id' in line:
                    dic['partner_id'] = line['partner_id']
                if dic:
                    rec.update(dic)
            elif self._context['line_ids'][-1]:
                line = self.search_read([('id','=',self._context['line_ids'][-1][1])],limit=1)[0]
                if 'name' in line:
                    dic['name'] = line['name']
                if 'analytic_account_id' in line :
                    dic['analytic_account_id'] = line['analytic_account_id'][0] if line['analytic_account_id'] else False
                if 'partner_id' in line:
                    dic['partner_id'] = line['partner_id'][0] if  line['partner_id'] else False
                if dic:
                    rec.update(dic)
                
         
        return rec
    
    
    @api.onchange('amount_currency', 'currency_id')
    def _onchange_amount_currency(self):
        ''' Overwrite function : to set default credit and debit if exist and currecny amount is zero
        Recompute the debit/credit based on amount_currency/currency_id and date.
        However, date is a related field on account.move. Then, this onchange will not be triggered
        by the form view by changing the date on the account.move.
        To fix this problem, see _onchange_date method on account.move.
        '''
        for line in self:
            amount = line.amount_currency
            if line.currency_id and line.currency_id != line.company_currency_id:
                amount = self.currency_id.with_context(date=line.date).compute(amount, line.company_currency_id)
            if amount > 0:
                line.debit = amount
            elif amount < 0:
                line.credit = -amount
