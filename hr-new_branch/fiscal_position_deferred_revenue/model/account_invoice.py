# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        ids = {'am':set({0,-1}),'aml':set({0,-1}),'aaa':set({0,-1}),'dl':set({0,-1})}
        for inv in self.filtered(lambda i: i.type in ['out_invoice', 'out_refund']):
            aaa =  self.env['account.asset.asset'].search([('invoice_id','=',inv.id),('active','=',False)])
            ids['aaa'].update(aaa.mapped('id'))
            ids['am'].update(aaa.mapped('depreciation_line_ids.move_id.id'))
            ids['aml'].update(aaa.mapped('depreciation_line_ids.move_id.line_ids.id'))
            ids['dl'].update(aaa.mapped('depreciation_line_ids.id'))
        self._cr.execute('delete from account_move_line where id in %s'% str(tuple(ids['aml']))  )
        self._cr.execute('delete from account_move where id in %s'% str(tuple(ids['am'])))
        self._cr.execute('delete from account_asset_depreciation_line where id in %s'% str(tuple(ids['dl'])))
        self._cr.execute('delete from account_asset_asset where id in %s'% str(tuple(ids['aaa'])))
        return res
            
            
            
        