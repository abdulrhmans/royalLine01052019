# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
import time

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    dependent_lines = fields.One2many('hr.employee.dependent','employee_id','Dependent Information')
    employee_health_amount = fields.Float("Employee Health Insurance Amount")
    dependent_health_amount = fields.Float("Dependent Health Insurance Amount", compute="_compute_dependent_health_amount", store=True)
    
    @api.multi
    @api.depends('dependent_lines', 'dependent_lines.health_amount')
    def _compute_dependent_health_amount(self):
        for employee in self:
            total = 0.0
            for dependent in employee.dependent_lines:
                total += dependent.health_amount
            employee.dependent_health_amount = total
    
class HrEmployeeDependent(models.Model):
    _name = "hr.employee.dependent"
    
    employee_id = fields.Many2one('hr.employee')
    name = fields.Char('Name')
    relative_type = fields.Selection([('father','Father'),
                                      ('mother','Mother'),
                                      ('brother','Brother'),
                                      ('sister','Sister'),
                                      ('husband','Husband'),
                                      ('wife','Wife'),
                                      ('daughter','Daughter'),
                                      ('son','Son')], 
                                      string='Type Of Relative')
    birthdate = fields.Date('Birth Date')
    ident_number = fields.Char('Ident Number')
    age = fields.Float('Age', compute="_calc_age", precision_digits=2)
    health_amount = fields.Float('Health Amount')
    
    @api.one
    def _calc_age(self):
        ''' This function will automatically calculates the age of relative.'''
        years = 0.0
        if self.birthdate:
            start = datetime.strptime(self.birthdate, DEFAULT_SERVER_DATE_FORMAT)
            end = datetime.strptime(time.strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
            delta = end - start
            years = (delta.days / 365.0)
        self.age = years
            