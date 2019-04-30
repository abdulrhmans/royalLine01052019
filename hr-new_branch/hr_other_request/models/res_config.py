# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    users_to_notify_ot_r_ids = fields.Many2many('res.users',string='Users To Notify') 
    
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    users_to_notify_ot_r_ids = fields.Many2many('res.users',string='Users To Notify',related="company_id.users_to_notify_ot_r_ids") 
