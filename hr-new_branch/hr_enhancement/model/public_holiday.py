# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, exceptions, fields, models, tools, _

class PublicHoliday(models.Model):
    _name = 'hr.public_holiday'

    date = fields.Datetime("From Date", required=True)
    date_to = fields.Datetime("To Date", required=True)
    name = fields.Char(string="Holiday Name", required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')

    company_ids = fields.Many2many('res.company', string="Companies",
                                   required=False)
    tag_ids = fields.Many2many('hr.employee.category', string="Tags",
                                   required=False)
    employee_ids = fields.Many2many('hr.employee', string="Impacted Employees",
                                   required=True)

    @api.onchange('company_ids', 'tag_ids')
    def _onchange_function(self):
        domain = []
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))

        if self.tag_ids:
            domain.append(('category_ids', 'in', self.tag_ids.ids))

        if domain:
            employees = self.env['hr.employee'].search(domain)

            self.employee_ids = employees.ids
        else:
            self.employee_ids = False
    
    def compensate_user_tz(self, date):
        '''
        Take date and compensate for user timezone
        :param date:
        :return:
        '''
        date_obj = datetime.strptime(date,
                                     tools.DEFAULT_SERVER_DATE_FORMAT)
        date_from = datetime.combine(date_obj, datetime.min.time())
        date_to = datetime.combine(date_obj, datetime.max.time())
        
        
        user_tz_offset = fields.Datetime.context_timestamp(
            self.sudo(self._uid), date_from).tzinfo._utcoffset
        
        date_from_tz_comp = date_from - user_tz_offset
        date_to_tz_comp = date_to - user_tz_offset
        
        date_from_tz_comp_str = date_from_tz_comp.strftime(
            tools.DEFAULT_SERVER_DATETIME_FORMAT)
        date_to_tz_comp_str = date_to_tz_comp.strftime(
            tools.DEFAULT_SERVER_DATETIME_FORMAT)

        return date_from_tz_comp_str, date_to_tz_comp_str
    
    @api.multi
    def create_leaves(self):
        """
        This method will create a leave for all selected employees
        """
        self.ensure_one()
        if self.state != 'draft':
            raise exceptions.ValidationError('You can only create leave for a '
                                             'draft public holiday')

        self.create_employee_leaves(self.employee_ids)
        self.state = 'done'

    @api.multi
    def create_employee_leaves(self, employee_ids):
        """
        This method will create a leave for the employees it's been given
        :param employee_ids: the employees to create the leave for
        """
        self.ensure_one()

        HRHolidays = self.env['hr.holidays']
        holiday_status_id = self.env['hr.holidays.status'].search(
            [('is_public_holiday', '=', True)], limit=1)

#         date_from, date_to = self.compensate_user_tz(self.date)
        DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        date_from = datetime.strptime(self.date,DATETIME_FORMAT)
        date_to = datetime.strptime(self.date_to,DATETIME_FORMAT)
        values = {'name': self.name,
                  'type': 'remove',
                  'holiday_type': 'employee',
                  'holiday_status_id': holiday_status_id.id,
                  'date_from': self.date,
                  'date_to': self.date_to,
                  'state': 'confirm',
                  'is_batch': True,
                  'public_id': self.id,
                  }

        if not holiday_status_id:
            raise exceptions.ValidationError(
                'No Leave Type has been configured as Public Holiday. Please '
                'go to Configuration > Leave Types and tick the box \'Public '
                'Holiday\' on the desired leave type.')

        context = {'mail_create_nosubscribe': True,
                   'mail_create_nolog': True,
                   'mail_notrack': True,
                   'tracking_disable': True}

        for employee in employee_ids:
            values['employee_id'] = employee.id
            values['number_of_days_temp'] = (date_to-date_from).days + int(float((date_to-date_from).seconds) / (60*60*employee.work_hour))
            domain = [
                ('date_from', '<=', self.date_to),
                ('date_to', '>=', self.date),
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
            ]
            nholidays = HRHolidays.search_count(domain)
            if nholidays:
                self.allocate_leaves(employee)
            else:
                leave = HRHolidays.sudo().with_context(context).create(values)
                leave.with_context(context).action_validate()
        
    @api.multi
    def allocate_leaves(self, employee):
        """
        This method will locate days
        """
        self.ensure_one()
        HRHolidays = self.env['hr.holidays']
        domain = [
                    ('date_from', '<=', self.date_to),
                    ('date_to', '>=', self.date),
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),
                ]
        holidays = HRHolidays.search(domain)
        days = 0
        
        DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        pup_date_from = datetime.strptime(self.date,DATETIME_FORMAT)
        pup_date_to = datetime.strptime(self.date_to,DATETIME_FORMAT)
        
        for hol in holidays:
            hol_date_from = datetime.strptime(hol.date_from,DATETIME_FORMAT)
            hol_date_to = datetime.strptime(hol.date_to,DATETIME_FORMAT)
            if hol.date_from > self.date:
                off_days = HRHolidays._get_schedule_holidays(hol.date_from, self.date_to, employee.id)
                days += abs((pup_date_to-hol_date_from).days) + int(float((pup_date_to-hol_date_from).seconds) / (60*60*employee.work_hour)) - off_days
            elif hol.date_to < self.date_to:
                off_days = HRHolidays._get_schedule_holidays(self.date, hol.date_to, employee.id)
                days += abs((hol_date_to-pup_date_from).days) + int(float((hol_date_to-pup_date_from).seconds) / (60*60*employee.work_hour)) - off_days
            else:
                off_days = HRHolidays._get_schedule_holidays(self.date, self.date_to, employee.id)
                days += abs((pup_date_to-pup_date_from).days) + int(float((pup_date_to-pup_date_from).seconds) / (60*60*employee.work_hour)) - off_days
        
        if days:
            holiday_status_id = self.env['hr.holidays.status'].search(
                [('leave_type', '=', 'legal')], limit=1)
            
            values = {'name': 'Allocate Leaves',
                      'type': 'add',
                      'holiday_type': 'employee',
                      'holiday_status_id': holiday_status_id.id,
                      'number_of_days_temp': days,
                      'state': 'confirm',
                      'public_id': self.id,
                      'employee_id': employee.id,
                      }
    
            context = {'mail_create_nosubscribe': True,
                       'mail_create_nolog': True,
                       'mail_notrack': True,
                       'tracking_disable': True}
            leave = HRHolidays.sudo().with_context(context).create(values)
            leave.with_context(context).action_validate()
        
    @api.multi
    def remove_leaves(self):
        """
        This method will remove the leave and its related
        analytic entries for all impacted employees
        """
        self.ensure_one()
        HRHolidays = self.env['hr.holidays']

        if self.state != 'done':
            raise exceptions.ValidationError('You can only delete leave for a'
                                             'done public holiday')

        holiday_ids = HRHolidays.search([('public_id', '=', self.id)])
        
        for holiday in holiday_ids:
            holiday.sudo().state = 'draft'
            holiday.sudo().unlink()

        self.state = 'draft'
    
    #FIX: constraint cannot be placed on table because the company_id column does not exist
#     _sql_constraints = [
#         ('unique_date',
#          'UNIQUE (date, company_id)',
#          'You should only have one public holiday per company and date')
#     ]
    
    @api.one
    @api.constrains('date', 'company_ids')
    def _check_unique_constraint(self):
        record = self.search([('date', '=', self.date), ('company_ids', 'in', self.company_ids.ids)])
        if len(record) > 1:
            raise ValidationError('You should only have one public holiday per company and date')

    @api.multi
    def open_generate_wizard(self):
        """
        This method opens the wizard that can generate the leave entry
        for newcomers
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.holiday.generate.holiday.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.multi
    def open_holiday(self):
        return {
            'name': _('Leave Requests'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.holidays',
            'view_id': False,
            'domain': [('public_id','in', self.ids)],
            'type': 'ir.actions.act_window',
        }  
        
class HRHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'

    is_public_holiday = fields.Boolean('Public Holiday', default=False)

    @api.multi
    @api.constrains('is_public_holiday')
    def check_unique_public_holiday(self):
        """
        This method checks that there is a single public holiday per company
        and per date
        """
        for holiday_status in self:
            if holiday_status.is_public_holiday \
                    and self.env['hr.holidays.status'].search(
                        [('is_public_holiday', '=', True),
                         ('id', '!=', holiday_status.id)]):
                raise exceptions.ValidationError(
                    'You can only have one leave type set as Public Holiday')
