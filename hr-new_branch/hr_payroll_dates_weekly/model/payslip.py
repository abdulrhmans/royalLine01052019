# -*- coding: utf-8 -*-

from odoo import fields, models
import time
from datetime import datetime
from dateutil import relativedelta

    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    date_from = fields.Date(string='Date From', readonly=True, required=True,
        default=str(datetime.now() - relativedelta.relativedelta(days=6))[:10], states={'draft': [('readonly', False)]})
    
    
    date_to = fields.Date(string='Date To', readonly=True, required=True,
        default=time.strftime('%Y-%m-%d'),
        states={'draft': [('readonly', False)]})