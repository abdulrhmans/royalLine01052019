# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, exceptions, fields, models, tools, _
from odoo.tools import float_utils


class Employee(models.Model):
    _inherit = "hr.employee"
    
    def _iter_work_intervals(self, start_dt, end_dt, resource_id, compute_leaves=True):
        if self._context.get('without_leaves', False):
            compute_leaves = False
        return super(Employee, self)._iter_work_intervals(start_dt, end_dt, resource_id, compute_leaves)

         
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
            [('leave_type', '=', 'public_holiday')], limit=1)

#         date_from, date_to = self.compensate_user_tz(self.date)
        DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        date_from = datetime.strptime(self.date, DATETIME_FORMAT)
        date_to = datetime.strptime(self.date_to, DATETIME_FORMAT)
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
            if hasattr(employee, 'work_hour'):
                work_time_second = 60 * 60 * employee.work_hour
            else:
                work_time_second = 28800  # 60*60*8 hours
                
            values['employee_id'] = employee.id
            domain = [
                ('date_from', '<=', self.date_to),
                ('date_to', '>=', self.date),
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.leave_type', '=', 'legal')
            ]
            nholidays = HRHolidays.search(domain)
            if nholidays:
                self.allocate_leaves(employee, nholidays)
            else:
                leave = HRHolidays.sudo().with_context(context).create(values)
                leave._onchange_employee_id()
                leave._onchange_date_to()
                leave.with_context(context).action_validate()
        
    @api.multi
    def allocate_leaves(self, employee, nholidays):
        """
        This method will locate days
        """
        self.ensure_one()
        HRHolidays = self.env['hr.holidays']
        days = 0
        DATETIME_FORMAT = tools.DEFAULT_SERVER_DATETIME_FORMAT
        pup_date_from = datetime.strptime(self.date, DATETIME_FORMAT)
        pup_date_to = datetime.strptime(self.date_to, DATETIME_FORMAT)
        for hol in nholidays:
            date_from = datetime.strptime(self.date if hol.date_from <= self.date else hol.date_from, DATETIME_FORMAT)
            date_to = datetime.strptime(self.date_to if hol.date_to >= self.date_to else hol.date_to, DATETIME_FORMAT)
            days += employee.with_context(without_leaves=True).get_work_days_data(date_from, date_to)['days']
            
        context = {'mail_create_nosubscribe': True,
                   'mail_create_nolog': True,
                   'mail_notrack': True,
                   'tracking_disable': True}
        holiday_status_id = self.env['hr.holidays.status'].search(
            [('leave_type', '=', 'legal')], limit=1)
        if holiday_status_id:
            if days:
                values = {
                          'type': 'add',
                          'holiday_type': 'employee',
                          'holiday_status_id': holiday_status_id.id,
                          'number_of_days_temp': days,
                          'state': 'confirm',
                          'public_id': self.id,
                          'employee_id': employee.id,
                          'name':'This allocation is a reimbursement of %s'%self.name
                          }
                
                leave = HRHolidays.sudo().with_context(context).create(values)
                leave._onchange_employee_id()
                leave.with_context(context).action_validate()
            domain = [
                    ('date_from', '>=', self.date),
                    ('date_to', '<=', self.date_to),
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),
                    ('holiday_status_id.leave_type', '=', 'legal')
                ]
            holiday_status_id = self.env['hr.holidays.status'].search(
                    [('leave_type', '=', 'public_holiday')], limit=1)
            last_date = False
            val_list = []
            for rec in nholidays.sorted(lambda x:x.date_from):
                if rec.date_from > self.date:
                    val_list.append({'name': self.name,
                              'type': 'remove',
                              'holiday_type': 'employee',
                              'holiday_status_id': holiday_status_id.id,
                              'date_from': self.add_remove_second(last_date, 1) if last_date  else self.date  ,
                              'date_to': self.add_remove_second(rec.date_from, -1),
                              'state': 'confirm',
                              'is_batch': True,
                              'public_id': self.id,
                              'employee_id': employee.id
                              })
                last_date = rec.date_to
            if last_date and last_date < self.date_to:
                val_list.append({
                              'type': 'remove',
                              'holiday_type': 'employee',
                              'holiday_status_id': holiday_status_id.id,
                              'date_from': self.add_remove_second(last_date, 1),
                              'date_to': self.date_to,
                              'state': 'confirm',
                              'is_batch': True,
                              'public_id': self.id,
                               'employee_id': employee.id,
                                 'name':'This allocation is a reimbursement of %s'%self.name
                              })
            for val in val_list:
                leave = HRHolidays.sudo().with_context(context).create(val)
                leave._onchange_employee_id()
                leave._onchange_date_to()
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

        # FIX: constraint cannot be placed on table because the company_id column does not exist
#     _sql_constraints = [
#         ('unique_date',
#          'UNIQUE (date, company_id)',
#          'You should only have one public holiday per company and date')
#     ]
    
    def add_remove_second(self, dt, second):
        return str(datetime.strptime(dt, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(seconds=second))
        
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
            'domain': [('public_id', 'in', self.ids)],
            'type': 'ir.actions.act_window',
        }  
