# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SWToolsConfigSettings(models.TransientModel):
    
    _inherit = "res.config.settings"

    default_sql_password = fields.Char(string="SQL Password", default_model='sql.commands')

    @api.multi
    def set_values(self):
        super(SWToolsConfigSettings, self).set_values()
        self.env['ir.default'].sudo().set('res.config.settings', 'default_sql_password', self.default_sql_password)
        return True

    @api.model
    def get_values(self):
        res = super(SWToolsConfigSettings, self).get_values()
        default_sql_password = self.env['ir.default'].get('res.config.settings', 'default_sql_password')
        res.update(default_sql_password = default_sql_password)
        return res
    
    