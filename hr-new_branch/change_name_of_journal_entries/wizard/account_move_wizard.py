# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

class ChangeNameEntries(models.TransientModel):
    _name = 'change.name.entries'
     
    move_id = fields.Many2one('account.move', required=True, string=" Account Move")
    name = fields.Char('Name', required=True)
    
    def change_name(self):
        sql = """update account_move set name = '%s' WHERE id = %s""" % (self.name,self.move_id.id)
        self.env.cr.execute(sql)
        
        
        
        
