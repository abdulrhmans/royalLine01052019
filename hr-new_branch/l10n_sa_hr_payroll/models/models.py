# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

translate=True
class Employee(models.Model):
    _inherit = 'hr.employee'
    
    gosi_number = fields.Char('GOSI Number')
    iqama_no = fields.Char('Hwayah/Iqma')
    employee_no = fields.Char('Employee Number')
    
    
    @api.one
    def check_get_paid_unpaid_days_exist(self):
        return  hasattr(self, 'get_paid_unpaid_days')
    
    
class Contract(models.Model):
    _inherit = 'hr.contract'
    
    housing = fields.Float('Housing Allowance')


