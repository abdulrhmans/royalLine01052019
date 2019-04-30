# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    payment_count = fields.Integer(string='Payments', compute="_get_payment") 
    
    def _get_payment(self): 
        rec = self.env['account.payment'].search([('sale_order_id','=',self.id)])
        self.payment_count = len(rec)
        
    def view_payments(self):
        rec = self.env['account.payment'].search([('sale_order_id','=',self.id)])
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_account_payments').read()[0]
        if len(rec) > 1:
            action['domain'] = [('id', 'in', rec.mapped('id'))]
        elif len(rec) == 1:
            action['views'] = [(self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = rec.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    
    
    