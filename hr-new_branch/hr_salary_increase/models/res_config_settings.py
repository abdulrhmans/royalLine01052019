from odoo import models, fields, api, _
from odoo.exceptions import UserError 
from email.policy import default


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    users_to_notify_ids = fields.Many2many('res.users',string='Users To Notify') 
    
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    users_to_notify_ids = fields.Many2many('res.users',string='Users To Notify',related="company_id.users_to_notify_ids") 