# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit='account.invoice'
    
    @api.multi
    def action_view_saleorder(self):
        so_id = self.mapped('invoice_line_ids').mapped('sale_line_ids').mapped('order_id')
         
        action = self.env.ref('sale.action_quotations').read()[0]
        
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['res_id'] = so_id.id
        action['target'] = 'main'

        if so_id.id > 0 :
            return action
        else :
            raise UserError(_("No Sale Order for this customer invoice"))
    @api.multi
    def action_view_po(self):
        po_id = self.mapped('invoice_line_ids').mapped('purchase_id')
         
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
        action['res_id'] = po_id.id
        action['target'] = 'main'
        
        if po_id.id > 0 :
            return action
        else :
            raise UserError(_("No Purchase Order for this vendor bill"))
            
