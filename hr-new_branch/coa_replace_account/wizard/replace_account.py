# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ReplaceAccount(models.Model):
    _name = 'coa.replace.account'
    
    replace_account_id = fields.Many2one('account.account','Replaced By',required=True)
    
    @api.one
    def replace(self):
        account_obj = self.env['account.account']
        move_line_obj = self.env['account.move.line']
        this = self
        
        account = account_obj.browse(self._context.get('active_ids',[]))[0]
        
        old_account = account.id
        old_company_id = account.company_id.id
        
        new_account = self.replace_account_id.id
        new_company_id = self.replace_account_id.company_id.id
        
        if old_company_id != new_company_id:
            raise UserError(_('The Two Accounts are in different company !!'))
        
        if old_account == new_account:
            raise UserError(_('The Two Accounts are same !!'))
        
        replace_recs = move_line_obj.search([('account_id','=',old_account),('company_id','=',new_company_id)])
        if replace_recs:
            idss = str(tuple(replace_recs.mapped('id'))).replace(',)', ')')
            self._cr.execute("update account_move_line set account_id = "+str(new_account)+" where id in "+idss)
            
        
        return {'type': 'ir.actions.act_window_close'}