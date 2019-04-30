# -*- coding: utf-8 -*-

from odoo import fields, models,api,_


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    eosb_account_id = fields.Many2one('account.account','EOSB Account', related='company_id.eosb_account_id')
    

    
class Company(models.Model):
    _inherit = 'res.company'
    
    eosb_account_id = fields.Many2one('account.account','EOSB Account')
