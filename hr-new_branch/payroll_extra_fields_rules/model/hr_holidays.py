# -*- coding: utf-8 -*-
from odoo import models, fields


class LeaveTypes(models.Model):
    _inherit = 'hr.holidays.status'
    
    unpaid = fields.Boolean('Leave Without Paid')
    code = fields.Char('Leave Code', help="Code used in payslip")