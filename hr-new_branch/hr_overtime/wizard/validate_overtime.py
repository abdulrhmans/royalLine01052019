# -*- coding: utf-8 -*-
from odoo import models, api

class validate_overtime_wizard(models.Model):
    _name = "validate.overtime.wizard"
    
    @api.one
    @api.model
    def validate(self):
        ctx = self.env.context.copy()
        hr_overtime = self.env['hr.overtime']
         
        for overtime in hr_overtime.browse(ctx.get('active_ids',[])):
            if overtime.state == 'validate':
                hr_overtime_validation = overtime.done_overtime()
        
        return {'type': 'ir.actions.act_window_close'}
