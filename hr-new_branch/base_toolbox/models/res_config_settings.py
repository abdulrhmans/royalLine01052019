# -*- coding: utf-8 -*-

from odoo import models, api

class SWToolsConfigSettings(models.TransientModel):
    
    _inherit = "res.config.settings"

    @api.multi
    def set_values(self):
        super(SWToolsConfigSettings, self).set_values()
        return True

    @api.model
    def get_values(self):
        res = super(SWToolsConfigSettings, self).get_values()
        return res
    
    @api.multi
    def execute(self):
        return super(SWToolsConfigSettings, self).execute()
