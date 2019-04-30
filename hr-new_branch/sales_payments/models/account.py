# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    sale_order_id = fields.Many2one('sale.order', 'SO') 


    

    
