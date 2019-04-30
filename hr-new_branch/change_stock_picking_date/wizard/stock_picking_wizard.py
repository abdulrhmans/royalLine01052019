# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

class PickingDate(models.TransientModel):
    _name = 'change.date.picking'
     
    picking_id = fields.Many2many('stock.picking', string="Picking", domain=[('state','=','done')])
    date = fields.Datetime('Date', required=True)
    change_journal = fields.Boolean('Change Journal')
    
    def change_date(self):
        pickings = self.picking_id
        
        for pick in pickings:
            stock = self.env['stock.picking'].browse(pick.id)
            stock.write({'scheduled_date':self.date,
                         'date_done':self.date})
            move_line = stock.move_lines
            for move in move_line:
                move.write({'date_expected':self.date,'date':self.date})
            for ml in stock.move_line_ids:
                ml.write({'date':self.date})
        if self.change_journal == True:
            for pickk in self.picking_id:
                for sm in pickk.move_lines:
                    account_move = self.env['account.move'].search([('stock_move_id','=',sm.id)])
                    if account_move:
                        for account in account_move:
                            account.button_cancel()
                            account.write({'date':self.date})
                            account_move_line = self.env['account.move.line'].search([('move_id','=',account.id)])
                            for aml in account_move_line:
                                aml.write({'date':self.date})
                            account.post()
            
