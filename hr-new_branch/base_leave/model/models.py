# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from datetime import datetime


class HolidaysStatus(models.Model):
    _inherit = "hr.holidays.status"
    
    leave_type = fields.Selection([('legal', 'Legal'), ('sick', 'Sick'), ('public_holiday', 'Public Holiday'), ('other', 'Other')], required=True)
    
    @api.multi
    @api.constrains('leave_type')
    def check_unique_public_holiday(self):
        """
        This method checks that there is a single public holiday per company
        and per date
        """
        for holiday_status in self:
             if self.env['hr.holidays.status'].search([('leave_type', '=', 'public_holiday'),
                                                      ('company_id', '=', self.env.user.company_id.id)], offset=1, limit=1):
                raise exceptions.ValidationError('You can only have one leave type set as Public Holiday')


class hRHolidays(models.Model):
    _inherit = "hr.holidays"
    
    year = fields.Selection([(str(year),str(year)) for year in range(1900,10000)],string='Year',default=lambda self:fields.Date.today()[:4])
    
