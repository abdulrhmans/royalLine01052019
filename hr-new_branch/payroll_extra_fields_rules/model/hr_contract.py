# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    other_amount = fields.Float('')
    is_other = fields.Boolean('Provide Other Allowances')
    
    @api.multi
    def write(self, vals):
        res = super(HrContract, self).write(vals)
        for contract in self:
            if 'resource_calendar_id' in vals:
                contract.employee_id.resource_calendar_id = vals['resource_calendar_id']
        return res
    
    
    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        if 'resource_calendar_id' in vals:
            res.employee_id.resource_calendar_id = vals['resource_calendar_id']
        return res